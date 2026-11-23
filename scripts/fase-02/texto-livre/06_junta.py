"""Junta receitas, SOAP e atestados num CSV só, uma linha por receita.

Lê os três CSVs já pseudo-anonimizados por `04_exporta.py` (mesma rodada: IDs,
datas e nomes fictícios batem) e liga pelo `atendimento_prof_id`. Ao lado de
cada receita vêm o SOAP e o(s) atestado(s) do mesmo atendimento; o SOAP se
repete nas receitas do mesmo atendimento. Não acessa o banco.

Uso: 06_junta.py <pasta com os CSVs> [--sem-html]
Grava 07_receitas_com_contexto.csv, ou 07_receitas_com_contexto_sem_html.csv
com `--sem-html` (texto limpo por `_limpeza.sem_html` antes do corte no limite do
Excel; limpando depois, o corte pode cair no meio de um bloco do Word)."""

import csv
import sys
from collections import defaultdict
from pathlib import Path

from _limpeza import sem_html

csv.field_size_limit(10**9)
LIMITE_EXCEL = 32767      # caracteres por célula; acima disso o Excel corta sozinho

# Ordem de leitura: quem/quando, o que o profissional escreveu, o que prescreveu.
CONTEXTO = ["receita_id", "atendimento_prof_id", "paciente_id", "data_atendimento", "sexo",
            "idade_anos", "unidade_saude", "ocupacao_profissional", "cbo_profissional",
            "tipo_atendimento_prof", "tipo_atendimento", "local_atendimento",
            "cids_atendimento", "ciaps_atendimento"]
SOAP = ["subjetivo", "objetivo", "avaliacao", "plano", "notas_cid_ciap"]
PRESCRICAO = ["medicamento", "concentracao", "forma_farmaceutica", "via_administracao",
              "posologia", "dose", "recomendacao"]


def le(caminho: Path) -> list[dict]:
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def cabe(texto: str) -> str:
    if len(texto) <= LIMITE_EXCEL:
        return texto
    aviso = f" [texto cortado: {len(texto)} caracteres no original]"
    return texto[:LIMITE_EXCEL - len(aviso)] + aviso


def main(pasta: Path, limpa_html: bool = False) -> None:
    receitas = le(pasta / "04_receitas_medicamento.csv")
    soap = {s["atendimento_prof_id"]: s for s in le(pasta / "06_soap.csv")}
    atestados = defaultdict(list)
    for a in le(pasta / "05_atestados.csv"):
        atestados[a["atendimento_prof_id"]].append(a)

    resto = [c for c in receitas[0] if c not in CONTEXTO + PRESCRICAO]
    cabecalho = (CONTEXTO + [f"soap_{c}" for c in SOAP] + PRESCRICAO + resto
                 + ["qt_atestados", "atestado_tipo", "atestado_texto", "atestado_cid10",
                    "atestado_dias_afastamento"])
    juntar = lambda lista, c: " ||| ".join(a[c] for a in lista if a[c])

    limpa = sem_html if limpa_html else (lambda t: t)
    nome = "07_receitas_com_contexto" + ("_sem_html" if limpa_html else "") + ".csv"
    with open(pasta / nome, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        w.writerow(cabecalho)
        for r in receitas:
            s = soap.get(r["atendimento_prof_id"], {})
            at = atestados.get(r["atendimento_prof_id"], [])
            linha = ([r[c] for c in CONTEXTO] + [s.get(c, "") for c in SOAP]
                     + [r[c] for c in PRESCRICAO] + [r[c] for c in resto]
                     + [len(at), juntar(at, "tipo_atestado_desc"), juntar(at, "texto_atestado"),
                        juntar(at, "cid10_atestado"), juntar(at, "dias_afastamento")])
            w.writerow([cabe(limpa(v)) if isinstance(v, str) else v for v in linha])
    print(f"{len(receitas)} receitas; com SOAP: "
          f"{sum(r['atendimento_prof_id'] in soap for r in receitas)}; com atestado: "
          f"{sum(r['atendimento_prof_id'] in atestados for r in receitas)}; {len(cabecalho)} colunas")


if __name__ == "__main__":
    main(Path(sys.argv[1]), "--sem-html" in sys.argv[2:])
