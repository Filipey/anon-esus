"""Distribuição e cardinalidade de colunas que podem carregar condição de
saúde/diagnóstico (CIAP, CID, "outra condição" em texto livre, ...).

Diferente de `antropometrico.py`, aqui não há uma lista de colunas já
declarada em nenhuma migration — nenhuma migration 01-12 cobre esse dado
ainda (ver `docs/mapeamento_colunas.tsv`, categoria "Texto livre" /
`no_outra_condicao1/2/3` em `tb_fat_cad_individual`, e as tabelas
`*_antecedente_ciap` confirmadas em `docs/auditoria_schema.md`). Este
script descobre candidatas direto no `information_schema` por padrão de
nome de coluna, na mesma linha de `scripts/audit_schema.py`.

**AJUSTE `_NAME_PATTERNS` e confirme contra o schema real** antes de
confiar no resultado — assim como as listas de colunas dos outros
scripts, isto é um ponto de partida, não uma fonte definitiva.

Classificação por prefixo (convenção já usada em todo o schema do e-SUS
APS/PEC, visível nas outras migrations): `co_`/`tp_`/`st_` = código/status
-> plota distribuição de valores; `ds_`/`no_` = texto livre -> **nunca**
plota o conteúdo (evitaria vazar uma string sensível dentro de um gráfico
publicado), só mede metadados (taxa de preenchimento, cardinalidade,
tamanho médio).

Para colunas codificadas, além da distribuição, mede quantos valores
distintos aparecem <= `RARITY_THRESHOLD` vezes na base: um código de
condição rara que só aparece 1-2 vezes funciona como quase-identificador
mesmo sem ser, isoladamente, um dado direto — é o principal motivo de
olhar pra essas colunas junto com CPF/CNS/endereço.

Uso:
    python scripts/plots/condicoes_medicas.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sqlalchemy import text

from _common import (
    COLOR_PRIMARY,
    COLOR_RISK,
    fetch_cardinality,
    fetch_rarity,
    fetch_value_counts,
    get_logger,
    load_engine,
    save_fig,
    set_latex_style,
)

log = get_logger("plots.condicoes_medicas")

SCHEMA = "public"
RARITY_THRESHOLD = 5
TOP_N = 30

# Padrões de nome de coluna que sugerem condição/diagnóstico de saúde.
# Bordas via "^", "_" ou fim de string, pra "cid" não bater em
# "cidade"/"cidadao".
_NAME_PATTERNS = [
    re.compile(r"(^|_)ciap\d?(_|$)", re.IGNORECASE),
    re.compile(r"(^|_)cid10?(_|$)", re.IGNORECASE),
    re.compile(r"(^|_)condicao\w*", re.IGNORECASE),
    re.compile(r"(^|_)doenca\w*", re.IGNORECASE),
    re.compile(r"(^|_)diagnostic\w*", re.IGNORECASE),
    re.compile(r"(^|_)patologia\w*", re.IGNORECASE),
]

# Tabelas de catálogo/dimensão (ex.: tb_dim_ciap — lista de códigos CIAP em
# si) não têm uma linha por cidadão; não fazem sentido pra distribuição
# por paciente e só poluiriam o relatório.
_CATALOG_TABLE_HINTS = ("_dim_", "tb_ciap", "tb_cid")


@dataclass(frozen=True)
class ConditionColumn:
    table: str
    column: str
    data_type: str
    is_coded: bool  # True = co_/tp_/st_ (código); False = ds_/no_ (texto livre)


def _is_catalog_table(table: str) -> bool:
    return any(hint in table for hint in _CATALOG_TABLE_HINTS)


def _matches_condition_pattern(column: str) -> bool:
    return any(p.search(column) for p in _NAME_PATTERNS)


def discover_condition_columns(engine) -> list[ConditionColumn]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = :schema
                """
            ),
            {"schema": SCHEMA},
        ).all()

    found: list[ConditionColumn] = []
    for table, column, data_type in rows:
        if _is_catalog_table(table):
            continue
        if not _matches_condition_pattern(column):
            continue
        is_coded = column.startswith(("co_", "tp_", "st_"))
        found.append(ConditionColumn(table, column, data_type, is_coded))
    return found


def plot_frequencia(col: ConditionColumn, counts: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6, max(3, 0.22 * len(counts))))
    ordered = counts.sort_values("contagem", ascending=True)
    sns.barplot(data=ordered, y="valor", x="contagem", color=COLOR_PRIMARY, ax=ax, orient="h")
    ax.set_xscale("log")
    ax.set_xlabel("# ocorrências (escala log)")
    ax.set_ylabel("")
    ax.set_title(f"{col.table}.{col.column} — top {len(counts)} valores")
    sns.despine(ax=ax)
    fig.tight_layout()
    save_fig(fig, f"condicoes_{col.table}_{col.column}_frequencia")


def plot_raridade(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6, max(3, 0.3 * len(summary))))
    ordered = summary.sort_values("pct_linhas_raras", ascending=True)
    label = ordered["tabela"] + "." + ordered["coluna"]
    sns.barplot(x=ordered["pct_linhas_raras"], y=label, color=COLOR_RISK, ax=ax, orient="h")
    ax.set_xlabel(f"% de linhas com valor raro (≤ {RARITY_THRESHOLD} ocorrências na base)")
    ax.set_ylabel("")
    ax.set_title("Risco de reidentificação por raridade do código")
    sns.despine(ax=ax)
    fig.tight_layout()
    save_fig(fig, "condicoes_raridade")


def main() -> int:
    set_latex_style()
    engine = load_engine()

    columns = discover_condition_columns(engine)
    if not columns:
        log.warning(
            "nenhuma coluna candidata encontrada (padrões: ciap/cid/condicao/doenca/"
            "diagnostico/patologia). Confirme os padrões em _NAME_PATTERNS contra o "
            "schema real."
        )
        return 0

    log.info("%d coluna(s) candidata(s) encontrada(s).", len(columns))

    coded_summary_rows = []
    freetext_summary_rows = []

    for col in columns:
        card = fetch_cardinality(engine, SCHEMA, col.table, col.column)
        if card["non_null"] == 0:
            log.info("%s.%s: sem valores não-nulos, pulando", col.table, col.column)
            continue

        if col.is_coded:
            counts = fetch_value_counts(engine, SCHEMA, col.table, col.column, top_n=TOP_N)
            if not counts.empty:
                plot_frequencia(col, counts)
                log.info(
                    "gerado: plots/condicoes_%s_%s_frequencia.pdf (+ .png)", col.table, col.column
                )

            rarity = fetch_rarity(engine, SCHEMA, col.table, col.column, RARITY_THRESHOLD)
            pct_raras = (
                100.0 * rarity["linhas_raras"] / rarity["linhas_total"]
                if rarity["linhas_total"]
                else 0.0
            )
            coded_summary_rows.append(
                {
                    "tabela": col.table,
                    "coluna": col.column,
                    "nao_nulos": card["non_null"],
                    "distintos": card["distinct"],
                    "pct_linhas_raras": pct_raras,
                }
            )
        else:
            # Texto livre: nunca plota o conteúdo, só metadados.
            freetext_summary_rows.append(
                {
                    "tabela": col.table,
                    "coluna": col.column,
                    "linhas_totais": card["total_rows"],
                    "nao_nulos": card["non_null"],
                    "pct_preenchido": 100.0 * card["non_null"] / card["total_rows"]
                    if card["total_rows"]
                    else 0.0,
                    "distintos": card["distinct"],
                }
            )

    if coded_summary_rows:
        summary = pd.DataFrame(coded_summary_rows)
        plot_raridade(summary)
        log.info("gerado: plots/condicoes_raridade.pdf (+ .png)")
        log.info("\nColunas codificadas:\n%s", summary.to_string(index=False))

    if freetext_summary_rows:
        freetext = pd.DataFrame(freetext_summary_rows)
        log.info(
            "\nColunas de texto livre (conteúdo NUNCA plotado, só metadados):\n%s",
            freetext.to_string(index=False),
        )

    if not coded_summary_rows and not freetext_summary_rows:
        log.warning("todas as colunas candidatas estavam vazias na base.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
