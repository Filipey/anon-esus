"""Regex e limpeza de texto compartilhadas pelos scripts de texto livre."""

from __future__ import annotations

import html
import re

from _conexao import consulta, ident

RE_TAG = re.compile(r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9]*)((?:\s[^>]*)?)/?>")
RE_ENTIDADE = re.compile(r"&([A-Za-z]+|#[0-9]+|#x[0-9A-Fa-f]+);")
RE_ESPACO = re.compile(r"\s+")
RE_PALAVRA = re.compile(r"\w+", re.UNICODE)
RE_MOJIBAKE = re.compile(r"Ã[\x80-\xbf§£©ª¡³µº¢]|Â[\xa0-\xbf]")
RE_TOKEN_CAPITALIZADO = re.compile(r"\b([A-ZÀ-Ú][a-zà-ÿ]{2,})\b")

# Padrões de dado pessoal. São deliberadamente sensíveis (preferem falso
# positivo): o objetivo aqui é dimensionar, não anonimizar.
PADROES_PII = {
    "cpf": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}[-.\s]?\d{2}\b"),
    "cns": re.compile(r"\b[1-2789]\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b"),
    "telefone": re.compile(r"(?:\(?\b\d{2}\)?\s?)?\b9?\d{4}[-.\s]?\d{4}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "cep": re.compile(r"\b\d{5}-\d{3}\b"),
    "data": re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-](?:\d{4}|\d{2})\b"),
    "idade": re.compile(r"\b\d{1,3}\s*(?:anos|a\b|meses|m\b|dias)", re.I),
    "endereco": re.compile(
        r"\b(?:rua|r\.|av\.?|avenida|travessa|tv\.|alameda|rodovia|estrada|"
        r"bairro|n[º°o]\.?\s*\d|quadra|lote|apto|apartamento|casa\s+\d)", re.I),
    "tratamento": re.compile(r"\b(?:sr|sra|srta|dr|dra|enf|enfa)\.?\s+[A-ZÀ-Ú]", re.U),
    "parentesco": re.compile(
        r"\b(?:m[ãa]e|pai|filh[oa]s?|espos[oa]|marido|irm[ãa]o?s?|av[óô]s?|"
        r"net[oa]s?|companheir[oa]|genro|nora|sogr[oa]|tia?o?|prim[oa])\b", re.I),
    "prontuario": re.compile(r"\bprontu[aá]rio\s*(?:n[º°o]?\.?)?\s*:?\s*\d+", re.I),
    "conselho": re.compile(r"\b(?:crm|coren|cro|crf|crefito|crp|crn)\s*[-/:]?\s*\w{0,2}\s*\d{3,}", re.I),
}

# Palavras capitalizadas comuns que também são nome/sobrenome; ficam fora do
# match de nome para não inflar a contagem (início de frase, termo clínico).
NAO_NOME = {
    "Paciente", "Refere", "Nega", "Relata", "Queixa", "Mae", "Pai", "Dor", "Pressao",
    "Retorno", "Orientado", "Orientada", "Encaminhado", "Encaminhada", "Exame",
    "Exames", "Em", "Uso", "Sem", "Com", "Para", "Nao", "Hoje", "Rosa", "Branco",
    "Branca", "Silva", "Santos", "Costa", "Campos", "Neves", "Paz", "Luz", "Vida",
    "Fonte", "Ramos", "Rocha", "Pinto", "Lima", "Leite", "Mota", "Moura", "Cruz",
    "Das", "Dos", "Del", "Unidade", "Saude", "Posto", "Hospital", "Janeiro",
    "Fevereiro", "Marco", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro",
    "Outubro", "Novembro", "Dezembro", "Domingo", "Segunda", "Terca", "Quarta",
    "Quinta", "Sexta", "Sabado",
}


# Grupo de uma coluna classificada como texto livre. A classe do 00 só olha
# a forma (>= 3 palavras), então junta nome de pessoa, endereço, log de
# sistema e catálogo com o texto clínico. O NER é sobre o grupo `clinico`;
# os outros já têm (ou terão) tratamento por coluna.
GRUPOS = ("clinico", "nome", "endereco", "sistema", "catalogo")

_TAB_SISTEMA = re.compile(
    r"^(auditoria_evento|revisao|lote_|processamento|migracao|nodo|recurso|perfil|papel|"
    r"config_sistema|credencial|dado_recebido|recebimento|relatorio_processamento|"
    r"historico_acesso|historico_dados_|envio_rnds|territorio_.*_erro|importacao_|"
    r"situacao_dado_recebido|acomp_cidadaos_vinc)"
)
_TAB_CATALOGO = re.compile(
    r"^(dim_|tipo_|cid10|cid11|ciap|cbo|proced|medicamento|principio_ativo|imunobiologico|"
    r"forma_farmaceutica|etnia|escolaridade|renda_familiar|povo_comunidade|pratica_saude|"
    r"racionalidade|publico_alvo|tema_|complexidade|conselho_classe|especialidade|"
    r"estrategia_vacinacao|faixa_etaria|dose_imunobiologico|local_apl|local_atend|"
    r"calendario_vacinal|grupo_atendimento|grupo_exame|opcao_rapida_exame|parte_bucal|"
    r"alim_bebida|beneficio|substancia|manifestacao_alergia|categoria_|situacao_|status_|"
    r"pergunta|qst_|mchat_pergunta|ivcf_perguntas|rastreio_cancer_pergunta|contexto_pergunta|"
    r"ad_destino|ad_origem|ad_tipo_|cds_tipo_|cds_ativ_col_|cds_pic|cds_adm_medicamento|"
    r"cds_imunobiologico|cds_visita_dom_motivo|antecedente_tipo_item|conduta_|"
    r"neuro_.*_detalhe|lista_espera_|justifica_nao_possui_cpf|doenca_.*_auto|"
    r"subtipo_unidade|unidade_saude|inep|dsei|polo_base|lotacao|atestado_modelo|"
    r"especialidades_|tipo_agravo|situacao_localidade|situacao_raiz|papel)"
)
_COL_NOME = re.compile(
    r"^(no_cidadao|no_mae|no_pai|no_social|no_responsavel|no_nome|no_profissional|"
    r"no_civil_profissional|no_cuidador|ds_nome|no_mae_cidadao|no_pai_cidadao)"
)
_COL_ENDERECO = re.compile(r"(logradouro|bairro|complemento|ponto_referencia|cep|endereco)")


def grupo(tabela: str, coluna: str) -> str:
    tab = tabela.split("_", 1)[1] if "_" in tabela else tabela
    if _COL_NOME.search(coluna):
        return "nome"
    if _COL_ENDERECO.search(coluna) or tab in {"logradouro", "bairro"}:
        return "endereco"
    if _TAB_SISTEMA.search(tab) or coluna in {"ds_ultima_tentativa", "ds_mensagem_erro"}:
        return "sistema"
    if _TAB_CATALOGO.search(tab) or coluna.endswith("_filtro") or coluna == "ds_filtro":
        return "catalogo"
    return "clinico"


def sem_html(texto: str) -> str:
    """Tira tags, decodifica entidades e normaliza espaço."""
    return RE_ESPACO.sub(" ", html.unescape(RE_TAG.sub(" ", texto))).strip()


def ler_valores(conn, tabela: str, coluna: str, limite: int | None = None):
    """Valores distintos não-vazios da coluna com a contagem de cada um.

    Com `limite`, devolve uma amostra aleatória (reprodutível) dos distintos.
    """
    v = f"nullif(btrim({ident(coluna)}::text), '')"
    sql = f"SELECT v, count(*) FROM (SELECT {v} AS v FROM public.{ident(tabela)}) s " \
          "WHERE v IS NOT NULL GROUP BY v"
    if limite:
        consulta(conn, "SELECT setseed(0.42)")
        sql += f" ORDER BY random() LIMIT {int(limite)}"
    return consulta(conn, sql)


def lexico_nomes(conn) -> set[str]:
    """Tokens (>= 3 letras) de nome de cidadão, mãe, pai e profissional
    cadastrados na própria base, capitalizados em Python — `initcap`/`lower`
    num banco SQL_ASCII não tratam letra acentuada."""
    lex: set[str] = set()
    for tabela, coluna in [
        ("tb_cidadao", "no_cidadao"),
        ("tb_cidadao", "no_mae"),
        ("tb_cidadao", "no_pai"),
        ("tb_prof", "no_profissional"),
    ]:
        r = consulta(conn, f"SELECT DISTINCT {ident(coluna)} FROM public.{ident(tabela)}")
        if isinstance(r, dict):
            continue
        for (nome,) in r:
            for t in (nome or "").split():
                if len(t) >= 3:
                    lex.add(t.lower().capitalize())
    return lex - NAO_NOME - {"Das", "Dos"}


def achados_pii(limpo: str, nomes: set[str]) -> dict[str, list[str]]:
    """Trechos que casaram com cada padrão de dado pessoal."""
    out = {}
    for rotulo, rx in PADROES_PII.items():
        achados = [m.group(0) for m in rx.finditer(limpo)]
        if achados:
            out[rotulo] = achados
    candidatos = (set(RE_TOKEN_CAPITALIZADO.findall(limpo)) - NAO_NOME) & nomes
    if candidatos:
        out["nome_do_lexico"] = sorted(candidatos)
    return out
