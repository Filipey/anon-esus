"""Pseudo-anonimização de texto livre (receita, atestado, SOAP) para exportação.

Ordem das trocas num texto, da mais específica à mais genérica:

1. Unidade de saúde -> "Unidade de Saúde N" (rótulo da migration 02 para a
   grafia encontrada; nome parcial, como "Ildemar de Castro", vai para o
   rótulo da unidade atual). Vem antes dos nomes porque as unidades têm nome
   de pessoa.
2. Município da base (Doutor Severiano) -> "Município 1".
3. CPF e CNS válidos -> fictício válido, o mesmo para o mesmo número.
4. Registro em conselho (CRM, COREN, CRP...) e telefone -> dígitos fictícios.
5. Nomes, com substituto do mesmo sexo e consistente em toda a exportação:
   a. nomes cadastrados do próprio paciente (próprio, social, mãe, pai,
      responsável, cuidador), tolerando grafia diferente, sobrenome a
      mais/a menos e prenome sozinho;
   b. qualquer nome completo cadastrado na base (cidadão, mãe, pai,
      profissional);
   c. sequência "prenome + sobrenome" reconhecida pelos léxicos de nomes da
      base, para nome que não está cadastrado (acompanhante, terceiro);
   d. prenome solto depois de função ou parentesco ("técnica Ana",
      "ACS Rita e Joana", "Dr. Carlos", "o pai de João").
6. Datas (numéricas e por extenso) deslocadas pelo delta do paciente.
7. Idade de 90 anos ou mais -> "mais de 90 anos" (como a coluna idade_anos).

O que nenhuma camada pega (apelido, nome raro em texto todo maiúsculo sem
gatilho, nome de terceiro sem contexto) continua no texto; a exportação mede
o resíduo."""

from __future__ import annotations

import random
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from difflib import SequenceMatcher

from faker import Faker

PARTICULAS = {"da", "de", "do", "das", "dos", "e", "d"}
_ESPACOS = re.compile(r"\s+")
PALAVRA = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ']+")
MARCACAO = re.compile(r"<[^>]*>|&[a-zA-Z]+;|&#\d+;")


def normalizar(nome: str) -> str:
    """Mesma forma da migration 09: sem acento, minúsculo, espaço simples."""
    sem_acento = "".join(
        ch for ch in unicodedata.normalize("NFD", nome) if unicodedata.category(ch) != "Mn"
    )
    return _ESPACOS.sub(" ", sem_acento).strip().lower()


def mesma_caixa(ficticio: str, original: str) -> str:
    letras = [ch for ch in original if ch.isalpha()]
    if letras and all(ch.isupper() for ch in letras):
        return ficticio.upper()
    if letras and all(ch.islower() for ch in letras):
        return ficticio.lower()
    return ficticio


def _sem_acento_regex(texto: str) -> str:
    """Regex que casa o texto com ou sem acento e com espaço flexível."""
    classes = {"a": "[aáàâã]", "e": "[eéê]", "i": "[ií]", "o": "[oóôõ]",
               "u": "[uúü]", "c": "[cç]"}
    partes = []
    for ch in normalizar(texto):
        if ch == " ":
            partes.append(r"\s+")
        else:
            partes.append(classes.get(ch, re.escape(ch)))
    return "".join(partes)


# --- documentos -------------------------------------------------------------

def cpf_valido(digitos: str) -> bool:
    d = [int(c) for c in digitos]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    return all(sum(d[i] * (n + 1 - i) for i in range(n)) * 10 % 11 % 10 == d[n]
               for n in (9, 10))


def cns_valido(digitos: str) -> bool:
    return (len(digitos) == 15 and digitos[0] in "12789"
            and sum(int(c) * (15 - i) for i, c in enumerate(digitos)) % 11 == 0)


CPF_RE = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}(?!\d)")
CNS_RE = re.compile(r"(?<!\d)[12789]\d{14}(?!\d)")
CONSELHO_RE = re.compile(
    r"\b(CRM|COREN|CRP|CRO|CRN|CREFITO|CRF)\b([^\dA-Za-z]{0,4}(?:[A-Z]{2})?[^\dA-Za-z]{0,4})"
    r"(\d[\d./-]*\d|\d)")
TELEFONE_RE = re.compile(r"(?<!\d)(?:\(\d{2}\)\s?)?9?\d{4}-\d{4}(?!\d)")

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
DATA_NUM = re.compile(
    r"(?<![\d/.])(?:(?P<iso>(?P<ia>\d{4})-(?P<im>\d{2})-(?P<id>\d{2}))"
    r"|(?P<d>\d{1,2})(?P<s>[/.])(?P<m>\d{1,2})(?:(?P=s)(?P<a>\d{4}|\d{2}))?)(?!\d)")
DATA_EXTENSO = re.compile(
    r"\b(?P<d>\d{1,2})(?P<e1>\s+de\s+)(?P<m>janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho"
    r"|agosto|setembro|outubro|novembro|dezembro)(?:(?P<e2>\s+de\s+)(?P<a>\d{4}))?\b", re.I)
IDADE_RE = re.compile(r"\b(\d{2,3})(\s+)(anos)\b", re.I)


def desloca_datas(texto: str, delta: timedelta, ano_ref: int) -> str:
    """Datas com ano sempre; dd/mm sem ano só com dois dígitos e dia != mês
    ("12/12 h", "06/06 horas", "30/30 dias", "1/2 comprimido" ficam)."""
    def num(m: re.Match) -> str:
        try:
            if m["iso"]:
                return (date(int(m["ia"]), int(m["im"]), int(m["id"])) + delta).isoformat()
            dia, mes, ano, sep = m["d"], m["m"], m["a"], m["s"]
            if ano is None:
                if sep != "/" or len(dia) != 2 or len(mes) != 2 or dia == mes:
                    return m.group()
                d = date(ano_ref, int(mes), int(dia)) + delta
                return f"{d:%d}/{d:%m}"
            a = int(ano) if len(ano) == 4 else 2000 + int(ano)
            d = date(a, int(mes), int(dia)) + delta
            fim = f"{d:%Y}" if len(ano) == 4 else f"{d:%y}"
            return f"{d.day:0{len(dia)}d}{sep}{d.month:0{len(mes)}d}{sep}{fim}"
        except ValueError:  # não é data válida (ex.: 30/30)
            return m.group()

    def extenso(m: re.Match) -> str:
        mes = [normalizar(x) for x in MESES].index(normalizar(m["m"])) + 1
        try:
            d = date(int(m["a"]) if m["a"] else ano_ref, mes, int(m["d"])) + delta
        except ValueError:
            return m.group()
        nome_mes = mesma_caixa(MESES[d.month - 1], m["m"])
        s = f"{d.day:0{len(m['d'])}d}{m['e1']}{nome_mes}"
        return s + (f"{m['e2']}{d.year}" if m["a"] else "")

    return DATA_EXTENSO.sub(extenso, DATA_NUM.sub(num, texto))


# --- nomes ------------------------------------------------------------------

def _chave_fonetica(p: str) -> str:
    p = p.replace("ph", "f").replace("th", "t").replace("y", "i").replace("w", "v") \
         .replace("k", "c").replace("ss", "s")
    p = p[0] + p[1:].replace("h", "") if p else p
    return re.sub(r"(.)\1+", r"\1", p)


def parecido(a: str, b: str) -> bool:
    """Mesma palavra com outra grafia (NATAN/NATHAN, MIKAELLY/MIKELLY;
    GONCALVES/GONÇALVES já sai igual na normalização)."""
    if a == b:
        return True
    if min(len(a), len(b)) < 4:
        return False
    ca, cb = _chave_fonetica(a), _chave_fonetica(b)
    return ca == cb or SequenceMatcher(None, ca, cb).ratio() >= 0.85


@dataclass
class Lexicos:
    """Nomes cadastrados na base, para as camadas 5b, 5c e 5d."""
    nomes_completos: dict[str, str]          # normalizado -> sexo (F/M/?)
    prenome_sexo: dict[str, str]             # prenome normalizado -> F/M
    prenomes: set[str]
    sobrenomes: set[str]
    # Sexo do cadastro da própria pessoa (nome do cidadão/social): vale mais
    # que o sexo inferido de onde o nome apareceu primeiro (ex.: o mesmo nome
    # digitado errado como `no_pai` de outra pessoa).
    sexo_proprio: dict[str, str] = field(default_factory=dict)
    palavras_comuns: set[str] = field(default_factory=set)


def monta_lexicos(nomes: list[tuple[str, str | None]], palavras_comuns: set[str],
                  proprios: list[tuple[str, str | None]] = ()) -> Lexicos:
    """`nomes`: (nome, sexo F/M/None). Prenome/sobrenome que aparece como
    palavra minúscula comum nos textos (ex.: "rosa", "dores") sai do léxico
    das camadas 5c/5d, para não trocar palavra por nome. `proprios`: nome e
    sexo do cadastro do próprio cidadão."""
    completos: dict[str, str] = {}
    conta_sexo: dict[str, Counter] = defaultdict(Counter)
    sobrenomes: Counter = Counter()
    for nome, sexo in nomes:
        tok = [t for t in normalizar(nome).split() if t]
        if len(tok) < 2 or tok[0] in {"rn", "recem", "rec"}:
            continue
        completos.setdefault(" ".join(tok), sexo or "?")
        if sexo:
            conta_sexo[tok[0]][sexo] += 1
        for t in tok[1:]:
            if t not in PARTICULAS:
                sobrenomes[t] += 1
    prenome_sexo = {p: c.most_common(1)[0][0] for p, c in conta_sexo.items()}
    for chave, sexo in completos.items():
        if sexo == "?":
            completos[chave] = prenome_sexo.get(chave.split()[0], "?")
    ok = lambda t, n: len(t) >= 3 and n >= 2 and t not in palavras_comuns
    prenomes = {p for p, c in conta_sexo.items() if ok(p, sum(c.values()))}
    conta_proprio: dict[str, Counter] = defaultdict(Counter)
    for nome, sexo in proprios:
        if nome and sexo:
            conta_proprio[normalizar(nome)][sexo] += 1
    return Lexicos(completos, prenome_sexo, prenomes,
                   {s for s, n in sobrenomes.items() if ok(s, n)},
                   {k: c.most_common(1)[0][0] for k, c in conta_proprio.items()},
                   set(palavras_comuns))


# Camada 5d: palavra que costuma vir antes de um prenome solto ("técnica de
# Enfermagem Ana", "ACS Rita e Joana", "Dr. Carlos", "o pai de João").
# Valor = sexo que o gatilho indica (None = não indica).
GATILHOS = {
    "dr": None, "dra": "F", "sr": "M", "sra": "F", "enf": None, "enfa": "F",
    "enfermeira": "F", "enfermeiro": "M", "tecnica": "F", "tecnico": "M", "enfermagem": None,
    "acs": None, "comunitaria": "F", "comunitarias": "F", "comunitario": "M",
    "comunitarios": None, "agente": None, "agentes": None,
    "mae": "F", "pai": "M", "filho": "M", "filha": "F", "esposo": "M", "esposa": "F",
    "marido": "M", "irma": "F", "irmao": "M", "avo": None, "neto": "M", "neta": "F",
    "companheiro": "M", "companheira": "F", "namorado": "M", "namorada": "F",
    "genitora": "F", "genitor": "M", "bebe": None, "menino": "M", "menina": "F",
    "crianca": None, "paciente": None, "psicologa": "F", "psicologo": "M",
    "nutricionista": None, "fisioterapeuta": None, "dentista": None, "professora": "F",
    "professor": "M", "cuidadora": "F", "cuidador": "M", "tia": "F", "tio": "M",
    "prima": "F", "primo": "M", "sobrinha": "F", "sobrinho": "M", "cunhada": "F",
    "cunhado": "M", "sogra": "F", "sogro": "M", "vizinha": "F", "vizinho": "M",
    "acompanhante": None, "responsavel": None,
}
_FAKER_PRENOMES = None


def _prenomes_faker() -> set[str]:
    global _FAKER_PRENOMES
    if _FAKER_PRENOMES is None:
        from faker.providers.person.pt_BR import Provider
        _FAKER_PRENOMES = {normalizar(n) for n in
                           list(Provider.first_names_female) + list(Provider.first_names_male)}
    return _FAKER_PRENOMES


@dataclass
class Paciente:
    sexo: str | None = None                  # F/M
    nomes: list[tuple[str, str | None]] = field(default_factory=list)  # (nome, sexo)
    cpf: str | None = None
    cns: str | None = None


class Anonimizador:
    def __init__(self, unidades_rotulo: dict[str, str], lexicos: Lexicos,
                 municipios: dict[str, str]):
        self.lex = lexicos
        self.sorteio = random.SystemRandom()
        self.fake = Faker("pt_BR")
        self.fake.seed_instance(self.sorteio.getrandbits(64))
        self._sobrenomes_fake = sorted({s for s in (self.fake.last_name() for _ in range(3000))
                                        if " " not in s})
        self.mapa_nome: dict[str, list[str]] = {}       # nome normalizado -> tokens fictícios
        self.ficticios: set[str] = set()
        self.mapa_doc: dict[str, str] = {}
        self.contagem: Counter = Counter()
        self._unidades = self._monta_unidades(unidades_rotulo)
        self._municipios = [(re.compile(r"\b" + _sem_acento_regex(m) + r"\b", re.I), rot)
                            for m, rot in municipios.items()]

    # -- unidades ------------------------------------------------------------
    @staticmethod
    def _monta_unidades(rotulo: dict[str, str]) -> list[tuple[re.Pattern, object]]:
        por_norm: dict[str, list[str]] = defaultdict(list)
        for bruto in rotulo:
            por_norm[normalizar(bruto)].append(bruto)

        def escolhe(achado: str) -> str:
            if achado in rotulo:
                return rotulo[achado]
            candidatos = por_norm[normalizar(achado)]
            maiusc = achado.isupper()
            iguais = [c for c in candidatos if c.isupper() == maiusc] or candidatos
            return rotulo[sorted(iguais)[0]]

        regras = []
        # Nome genérico ("Secretaria de Saude") não identifica e aparece como
        # expressão comum no texto; fica como está.
        genericos = {"nao informado", "cnes nao encontrado", "secretaria de saude",
                     "polo academia da saude", "laboratorio municipal de analises clinicas",
                     "unidade de vigilancia em saude"}
        # Nome completo cadastrado, do mais longo ao mais curto.
        for norm in sorted(por_norm, key=len, reverse=True):
            if norm in genericos:
                continue
            regras.append((re.compile(r"\b" + _sem_acento_regex(norm) + r"\b", re.I), escolhe))
        # Nome parcial ou truncado -> rótulo da unidade atual.
        prefixo = (r"(?:(?:Unidade\s+B[aá]sica\s+de\s+Sa[uú]de|Centro\s+de\s+Sa[uú]de|"
                   r"Posto\s+de\s+Sa[uú]de|Hospital|Unidade\s+Mista)\s+)?")
        parciais = {
            r"(?:Francisco\s+)?Ild[eo]mar\s+(?:de\s+)?Cast(?:ro)?":
                "UBS Unidade Basica de Saude Francisco Ildemar de Castro",
            r"Cristalino\s+Leite(?:\s+da\s+Silva)?": "UBS Unidade Basica de Saude Cristalino Leite da Silva",
            r"Maria\s+Nogueira\s+Neta": "UBS Unidade Basica de Saude Maria Nogueira Neta",
            r"Ant[oô]nio\s+Marques\s+de\s+Melo": "Posto de Saude Antonio Marques de Melo",
            r"Maria\s+do\s+Socorro\s+(?:de\s+)?Queiroz\s+(?:da\s+)?Silve(?:re)?ira":
                "Posto de Saude Maria do Socorro Queiroz da Silvereira",
            r"Jos[eé]\s+Dez[ií]lio(?:\s+Fernandes)?": "Hospital Jose Dezilio Fernandes",
            r"Amor\s+At[ií]pico": "Centro de Especialidades Amor Atipico",
        }
        for padrao, bruto in parciais.items():
            if bruto in rotulo:
                regras.append((re.compile(r"\b" + prefixo + padrao + r"\b", re.I), rotulo[bruto]))
        return regras

    def _troca_unidades(self, texto: str) -> str:
        for regex, alvo in self._unidades:
            def troca(m: re.Match) -> str:
                rot = alvo(m.group()) if callable(alvo) else alvo
                self.contagem["unidade"] += 1
                return mesma_caixa(rot, m.group())
            texto = regex.sub(troca, texto)
        for regex, rot in self._municipios:
            n = len(regex.findall(texto))
            if n:
                self.contagem["municipio"] += n
                texto = regex.sub(lambda m: mesma_caixa(rot, m.group()), texto)
        return texto

    # -- documentos ----------------------------------------------------------
    def _doc_ficticio(self, chave: str, gera) -> str:
        if chave not in self.mapa_doc:
            self.mapa_doc[chave] = gera()
        return self.mapa_doc[chave]

    def _cpf_falso(self) -> str:
        while True:
            d = [self.sorteio.randint(0, 9) for _ in range(9)]
            for n in (10, 11):
                s = sum(v * (n - i) for i, v in enumerate(d)) % 11
                d.append(0 if s < 2 else 11 - s)
            t = "".join(map(str, d))
            if cpf_valido(t):
                return t

    def _cns_falso(self, primeiro: str) -> str:
        while True:
            d = [int(primeiro)] + [self.sorteio.randint(0, 9) for _ in range(13)]
            s = sum(v * (15 - i) for i, v in enumerate(d))
            for ult in range(10):
                if (s + ult) % 11 == 0:
                    return "".join(map(str, d + [ult]))

    @staticmethod
    def _mesmo_formato(digitos_novos: str, original: str) -> str:
        it = iter(digitos_novos)
        return "".join(next(it) if ch.isdigit() else ch for ch in original)

    def _troca_documentos(self, texto: str) -> str:
        def cns(m: re.Match) -> str:
            if not cns_valido(m.group()):
                return m.group()
            self.contagem["cns"] += 1
            return self._doc_ficticio("cns" + m.group(), lambda: self._cns_falso(m.group()[0]))

        def cpf(m: re.Match) -> str:
            dig = re.sub(r"\D", "", m.group())
            if not cpf_valido(dig):
                return m.group()
            self.contagem["cpf"] += 1
            return self._mesmo_formato(self._doc_ficticio("cpf" + dig, self._cpf_falso), m.group())

        def digitos(chave: str, original: str) -> str:
            novo = self._doc_ficticio(chave + original, lambda: "".join(
                str(self.sorteio.randint(0, 9)) for _ in re.sub(r"\D", "", original)))
            return self._mesmo_formato(novo, original)

        def conselho(m: re.Match) -> str:
            self.contagem["conselho"] += 1
            return m[1] + m[2] + digitos("cons", m[3])

        def telefone(m: re.Match) -> str:
            self.contagem["telefone"] += 1
            return digitos("tel", m.group())

        texto = CNS_RE.sub(cns, texto)
        texto = CPF_RE.sub(cpf, texto)
        texto = CONSELHO_RE.sub(conselho, texto)
        return TELEFONE_RE.sub(telefone, texto)

    # -- nomes ---------------------------------------------------------------
    def _prenome_falso(self, sexo: str) -> str:
        if sexo not in ("F", "M"):
            sexo = self.sorteio.choice("FM")
        f = self.fake.first_name_female if sexo == "F" else self.fake.first_name_male
        while True:
            p = f()
            if " " not in p:
                return p

    def ficticio(self, nome_norm: str, sexo: str | None) -> list[str]:
        """Tokens fictícios para um nome normalizado (mesmo nº de palavras,
        partículas no lugar, prenome do mesmo sexo). Consistente: o mesmo nome
        sempre recebe o mesmo fictício."""
        if nome_norm in self.mapa_nome:
            return self.mapa_nome[nome_norm]
        tok = nome_norm.split()
        sexo = self.lex.sexo_proprio.get(nome_norm) or (
            sexo if sexo in ("F", "M") else self.lex.prenome_sexo.get(tok[0], "?"))
        for _ in range(50):
            novo = []
            for i, t in enumerate(tok):
                if t in PARTICULAS and i > 0:
                    novo.append(t)
                elif i == 0 or (i == 1 and (t in self.lex.prenome_sexo or t in _prenomes_faker())):
                    novo.append(self._prenome_falso(sexo))       # prenome composto
                else:
                    novo.append(self.sorteio.choice(self._sobrenomes_fake))
            chave = normalizar(" ".join(novo))
            if (chave not in self.lex.nomes_completos and chave not in self.ficticios
                    and all(normalizar(a) != b for a, b in zip(novo, tok) if b not in PARTICULAS)):
                break
        self.mapa_nome[nome_norm] = novo
        self.ficticios.add(normalizar(" ".join(novo)))
        return novo

    @staticmethod
    def _tokens(texto: str) -> tuple[list[tuple[int, int, str, str, bool]], str]:
        mascarado = MARCACAO.sub(lambda m: " " * len(m.group()), texto)
        toks = [(m.start(), m.end(), m.group(), normalizar(m.group()))
                for m in PALAVRA.finditer(mascarado)]
        # adjacente = só espaço (ou marcação HTML) entre um token e o próximo
        return [(s, e, w, n, i + 1 < len(toks) and not mascarado[e:toks[i + 1][0]].strip())
                for i, (s, e, w, n) in enumerate(toks)], mascarado

    def _troca_nomes(self, texto: str, pac: Paciente) -> str:
        toks, mascarado = self._tokens(texto)
        novo: dict[int, str] = {}                 # índice do token -> substituto

        def livre(i: int) -> bool:
            return i not in novo

        def aplica(ini: int, fim: int, mapa: dict[str, str], camada: str) -> None:
            for k in range(ini, fim):
                n = toks[k][3]
                if n in mapa and not (n in PARTICULAS and k > ini):
                    novo[k] = mesma_caixa(mapa[n], toks[k][2]) if not toks[k][2].istitle() \
                        else mapa[n].capitalize() if mapa[n].islower() else mapa[n]
            self.contagem[camada] += 1

        def corrida(i: int, aceita) -> int:
            """Fim (exclusivo) da maior sequência adjacente a partir de i em que
            cada token é aceito (partícula só no meio)."""
            j = i
            while j < len(toks) and livre(j):
                n = toks[j][3]
                if aceita(n):
                    j += 1
                elif n in PARTICULAS and j + 1 < len(toks) and aceita(toks[j + 1][3]) \
                        and toks[j][4]:
                    j += 1
                else:
                    break
                if not toks[j - 1][4]:
                    break
            while j > i and toks[j - 1][3] in PARTICULAS:
                j -= 1
            return j

        # 5a. nomes cadastrados do paciente. O cadastro pode ter sido corrigido
        # depois do texto ("NATHAN" x "NATAN", "MIKELLY" x "MIKAELLY"), então a
        # palavra casa por semelhança, não só por igualdade.
        for nome, sexo in pac.nomes:
            reg = normalizar(nome).split()
            if not reg:
                continue
            fic = self.ficticio(" ".join(reg), sexo)
            por_reg = {r: f for r, f in zip(reg, fic) if r not in PARTICULAS}
            casa = {}                                  # palavra do texto -> palavra do cadastro
            for k in range(len(toks)):
                n = toks[k][3]
                if n not in PARTICULAS and n not in casa:
                    alvo = next((r for r in por_reg if parecido(n, r)), None)
                    if alvo:
                        casa[n] = alvo
            mapa = {n: por_reg[r] for n, r in casa.items()}
            sobrenomes_finais = [r for r in reg if r not in PARTICULAS][-2:]
            for i in range(len(toks)):
                if not livre(i) or toks[i][3] not in mapa:
                    continue
                j = corrida(i, lambda n: n in mapa)
                casados = [casa[toks[k][3]] for k in range(i, j) if toks[k][3] not in PARTICULAS]
                # com prenome (1º ou 2º do cadastro: "Joana Souza" de
                # "Maria Joana ... Souza"), 3+ palavras ou o par final
                if len(casados) >= 2 and (any(c in reg[:2] for c in casados) or len(casados) >= 3
                                          or casados[-2:] == sobrenomes_finais):
                    aplica(i, j, mapa, "nome_paciente")
            # prenome sozinho (ex.: "LUCAS (LUCAS TAVARES ...)", ou o segundo
            # prenome como apelido: "Lucimar - (Maria Lucimar ...)"), se não for
            # minúsculo: em minúsculo pode ser palavra comum
            prenomes_reg = {r for r in reg[:2] if r in self.lex.prenome_sexo} if len(reg) >= 2 else set()
            for i in range(len(toks)):
                w, n = toks[i][2], toks[i][3]
                if livre(i) and casa.get(n) in prenomes_reg and not w.islower():
                    aplica(i, i + 1, {n: mapa[n]}, "prenome_paciente")

        # 5b. nome completo cadastrado na base
        for i in range(len(toks)):
            if not livre(i):
                continue
            for n in range(7, 1, -1):
                if i + n > len(toks) or not all(livre(k) for k in range(i, i + n)) \
                        or not all(toks[k][4] for k in range(i, i + n - 1)):
                    continue
                chave = " ".join(toks[k][3] for k in range(i, i + n))
                if chave in self.lex.nomes_completos and chave not in self.ficticios:
                    fic = self.ficticio(chave, self.lex.nomes_completos[chave])
                    aplica(i, i + n, dict(zip(chave.split(), fic)), "nome_base")
                    break

        # 5c. prenome + sobrenome dos léxicos, com inicial maiúscula
        lex = self.lex
        for i in range(len(toks)):
            if not livre(i) or toks[i][3] not in lex.prenomes or toks[i][2].islower():
                continue
            j = corrida(i, lambda n: n in lex.prenomes or n in lex.sobrenomes)
            cand = [k for k in range(i, j) if toks[k][3] not in PARTICULAS]
            if len(cand) >= 2 and all(not toks[k][2].islower() for k in cand):
                chave = " ".join(toks[k][3] for k in range(i, j))
                if chave in self.ficticios:
                    continue
                fic = self.ficticio(chave, lex.prenome_sexo.get(toks[i][3]))
                aplica(i, j, dict(zip(chave.split(), fic)), "nome_lexico")

        # 5d. prenome solto (ou lista "Rita e Joana") depois de função ou
        # parentesco. Em texto todo maiúsculo só vale prenome conhecido; em
        # caixa mista, também palavra com inicial maiúscula que não é comum.
        prenomes = lex.prenomes | {p for p in _prenomes_faker() if p not in lex.palavras_comuns}

        def separa(a: int, b: int, extra: str = "") -> bool:
            return bool(re.fullmatch(r"[\s.:(\-ªº" + extra + r"]{0,5}",
                                     mascarado[toks[a][1]:toks[b][0]]))

        def aceito(k: int, sobrenome: bool = False) -> bool:
            w, n = toks[k][2], toks[k][3]
            if len(n) < 3 or n in GATILHOS or n in PARTICULAS or not livre(k):
                return False
            if w.isupper():
                return n in prenomes or (sobrenome and n in lex.sobrenomes)
            if w[0].isupper():
                return n in prenomes or n not in lex.palavras_comuns
            return not sobrenome and n in prenomes

        for i in range(len(toks)):
            if toks[i][3] not in GATILHOS:
                continue
            sexo_g, ant, j = GATILHOS[toks[i][3]], i, i + 1
            if j < len(toks) and toks[j][3] in {"de", "da", "do"} and separa(i, j):
                ant, j = j, j + 1                       # "o pai de João"
            while j < len(toks) and separa(ant, j, ",") and aceito(j):
                fim = j + 1
                while fim < len(toks) and toks[fim - 1][4]:
                    if aceito(fim, sobrenome=True) and not toks[fim][2].islower():
                        fim += 1
                    elif toks[fim][3] in PARTICULAS - {"e"} and fim + 1 < len(toks) and toks[fim][4] \
                            and aceito(fim + 1, sobrenome=True) and not toks[fim + 1][2].islower():
                        fim += 2
                    else:
                        break
                chave = " ".join(toks[k][3] for k in range(j, fim))
                fic = self.ficticio(chave, sexo_g or lex.prenome_sexo.get(toks[j][3]))
                aplica(j, fim, dict(zip(chave.split(), fic)), "nome_gatilho")
                # lista: "Rita e Joana", "Rita, Ana e Joana"
                if fim < len(toks) and toks[fim][3] == "e" and separa(fim - 1, fim, ","):
                    ant, j = fim, fim + 1
                elif fim < len(toks) and "," in mascarado[toks[fim - 1][1]:toks[fim][0]]:
                    ant, j = fim - 1, fim
                else:
                    break

        if not novo:
            return texto
        partes, pos = [], 0
        for k in sorted(novo):
            s, e = toks[k][0], toks[k][1]
            partes += [texto[pos:s], novo[k]]
            pos = e
        return "".join(partes) + texto[pos:]

    # -- tudo ----------------------------------------------------------------
    def anonimiza(self, texto: str | None, pac: Paciente, delta: timedelta, ano_ref: int):
        if not texto:
            return texto
        t = self._troca_unidades(texto)
        t = self._troca_documentos(t)
        t = self._troca_nomes(t, pac)
        t = desloca_datas(t, delta, ano_ref)

        def idade(m: re.Match) -> str:
            if int(m[1]) < 90:
                return m.group()
            self.contagem["idade_90+"] += 1
            return mesma_caixa("mais de 90", m[3]) + m[2] + m[3]
        return IDADE_RE.sub(idade, t)
