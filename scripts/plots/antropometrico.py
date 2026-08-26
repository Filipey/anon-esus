"""Distribuição e cardinalidade dos dados antropométricos (base real).

Reaproveita a lista de colunas já declarada em
`scripts/08_anon_antropometrico.py` (`ANTHRO_COLUMNS`) — a mesma que a
migration hasheia — e gera, por campo semântico (peso, altura, IMC,
perímetro cefálico, circunferência abdominal, perímetro de panturrilha,
altura uterina), agrupando todas as tabelas que o guardam
(`tb_fat_atendimento_individual`, `ta_medicao`/`tb_medicao`/`tl_medicao`,
...):

  1. histograma de densidade + ECDF da distribuição;
  2. cardinalidade (razão valores distintos / valores não-nulos).

O próprio docstring da migration 08 já aponta o motivo de medir
cardinalidade aqui: campos antropométricos têm poucos milhares de valores
plausíveis, então um hash (mesmo com sal) não impede um ataque de força
bruta que pré-calcule o hash de todo o range plausível — a Figura de
cardinalidade dá um número a essa fragilidade.

Uso:
    python scripts/plots/antropometrico.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from _common import (
    COLOR_PRIMARY,
    COLOR_RISK,
    fetch_numeric_series,
    get_logger,
    load_engine,
    load_module,
    save_fig,
    set_latex_style,
)

log = get_logger("plots.antropometrico")

# Mapeia trecho do nome da coluna -> campo semântico. Ordem importa:
# padrões mais específicos primeiro (ex.: "altura_uterina" antes de
# "altura", senão cai no campo errado).
_FIELD_PATTERNS: list[tuple[str, str]] = [
    ("altura_uterina", "altura_uterina"),
    ("perimetro_cefalico", "perimetro_cefalico"),
    ("perim_cefalico", "perimetro_cefalico"),
    ("circunf_abdominal", "circunferencia_abdominal"),
    ("circ_abdominal", "circunferencia_abdominal"),
    ("perim_panturrilha", "perimetro_panturrilha"),
    ("perimetro_panturrilha", "perimetro_panturrilha"),
    ("imc", "imc"),
    ("peso", "peso"),
    ("altura", "altura"),
]

_FIELD_LABELS = {
    "peso": "Peso (kg)",
    "altura": "Altura (cm)",
    "imc": "IMC",
    "perimetro_cefalico": "Perímetro cefálico (cm)",
    "circunferencia_abdominal": "Circunferência abdominal (cm)",
    "perimetro_panturrilha": "Perímetro de panturrilha (cm)",
    "altura_uterina": "Altura uterina (cm)",
}


def _semantic_field(column: str) -> str | None:
    for pattern, field in _FIELD_PATTERNS:
        if pattern in column:
            return field
    return None


def _group_columns_by_field(anthro_columns) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for col in anthro_columns:
        field = _semantic_field(col.column)
        if field is None:
            log.warning("coluna sem campo semântico reconhecido, pulando: %s", col.qualified)
            continue
        grouped.setdefault(field, []).append(col)
    return grouped


def _pool_values(engine, columns) -> pd.Series:
    parts = [fetch_numeric_series(engine, c.schema, c.table, c.column) for c in columns]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.Series(dtype="float64")
    return pd.concat(parts, ignore_index=True)


def plot_distribuicao(field: str, values: pd.Series) -> None:
    label = _FIELD_LABELS.get(field, field)
    fig, (ax_hist, ax_ecdf) = plt.subplots(1, 2, figsize=(8, 3.2))

    sns.histplot(values, stat="density", color=COLOR_PRIMARY, ax=ax_hist, bins=40)
    ax_hist.set_xlabel(label)
    ax_hist.set_ylabel("densidade")
    ax_hist.set_title("Distribuição")

    sns.ecdfplot(values, color=COLOR_PRIMARY, ax=ax_ecdf)
    ax_ecdf.set_xlabel(label)
    ax_ecdf.set_ylabel("proporção acumulada")
    ax_ecdf.set_title("ECDF")

    n_fmt = f"{len(values):,}".replace(",", ".")
    fig.suptitle(f"{label} — n = {n_fmt}")
    sns.despine(fig=fig)
    fig.tight_layout()

    save_fig(fig, f"antropometrico_{field}_distribuicao")


def plot_cardinalidade(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ordered = summary.sort_values("razao_cardinalidade", ascending=False)
    sns.barplot(data=ordered, x="campo", y="razao_cardinalidade", color=COLOR_RISK, ax=ax)
    ax.set_xlabel("")
    ax.set_ylabel("valores distintos / valores não-nulos")
    ax.set_title("Cardinalidade relativa dos campos antropométricos")
    ax.set_ylim(0, min(1.05, max(0.1, ordered["razao_cardinalidade"].max() * 1.15)))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    sns.despine(ax=ax)
    fig.tight_layout()
    save_fig(fig, "antropometrico_cardinalidade")


def main() -> int:
    set_latex_style()
    engine = load_engine()
    anthro_module = load_module("08_anon_antropometrico.py")
    grouped = _group_columns_by_field(anthro_module.ANTHRO_COLUMNS)

    summary_rows = []
    for field, columns in sorted(grouped.items()):
        log.info("campo '%s': %d coluna(s) fonte", field, len(columns))
        values = _pool_values(engine, columns)
        if values.empty:
            log.warning("campo '%s' sem valores na base, pulando plot de distribuição", field)
            continue

        plot_distribuicao(field, values)
        log.info("gerado: plots/antropometrico_%s_distribuicao.pdf (+ .png)", field)

        non_null = len(values)
        distinct = int(values.nunique())
        summary_rows.append(
            {
                "campo": _FIELD_LABELS.get(field, field),
                "nao_nulos": non_null,
                "distintos": distinct,
                "razao_cardinalidade": distinct / non_null if non_null else 0.0,
            }
        )

    if summary_rows:
        summary = pd.DataFrame(summary_rows)
        plot_cardinalidade(summary)
        log.info("gerado: plots/antropometrico_cardinalidade.pdf (+ .png)")
        log.info("\n%s", summary.to_string(index=False))
    else:
        log.warning("nenhum campo antropométrico com valores encontrado.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
