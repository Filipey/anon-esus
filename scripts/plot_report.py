"""Gera plots (estilo LaTeX) a partir do relatório de auditoria da pipeline.

Lê o JSON escrito por `pipeline_report.py` (`logs/<...>_auditoria.json`) e
produz figuras comparando, por migration: quantas colunas foram
declaradas vs. quantas de fato tiveram conteúdo alterado, e quantas
linhas foram removidas em tabelas (relevante só para `12_anon_ip_logs`).

Uso:
    python scripts/plot_report.py [caminho_do_relatorio.json]

Sem argumento, usa o relatório de auditoria mais recente em `logs/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT / "logs"
PLOTS_DIR = ROOT / "plots"

# Paleta própria (não é a default do matplotlib/seaborn) - azul petróleo e
# âmbar para contraste entre "declaradas" e "alteradas", vermelho escuro
# reservado para remoção de linhas (ação mais drástica, migration 12).
COLOR_DECLARADAS = "#2E4057"
COLOR_ALTERADAS = "#F18F01"
COLOR_REMOVIDAS = "#9E2A2B"


def _latest_report() -> Path:
    candidates = sorted(LOGS_DIR.glob("*_auditoria.json"))
    if not candidates:
        raise FileNotFoundError(f"nenhum relatório *_auditoria.json encontrado em {LOGS_DIR}")
    return candidates[-1]


def _set_style() -> None:
    """Visual 'estilo LaTeX' (serif + mathtext Computer Modern) sem exigir
    uma instalação real de LaTeX no sistema."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update(
        {
            "font.family": "serif",
            "mathtext.fontset": "cm",
            "axes.edgecolor": "0.3",
            "axes.linewidth": 0.8,
            "grid.linewidth": 0.5,
            "grid.alpha": 0.4,
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
        }
    )


def load_summary(report_path: Path) -> pd.DataFrame:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    df = pd.DataFrame.from_dict(data["resumo_por_migration"], orient="index")
    df.index.name = "migration"
    return df.sort_index()


def plot_colunas(df: pd.DataFrame, out_dir: Path) -> Path:
    """Figura 6x4: # colunas declaradas vs. # colunas com conteúdo alterado."""
    long_df = df.reset_index().melt(
        id_vars="migration",
        value_vars=["colunas_declaradas", "colunas_com_conteudo_alterado"],
        var_name="tipo",
        value_name="quantidade",
    )
    long_df["tipo"] = long_df["tipo"].map(
        {
            "colunas_declaradas": "# declaradas",
            "colunas_com_conteudo_alterado": "# alteradas",
        }
    )

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(
        data=long_df,
        x="migration",
        y="quantidade",
        hue="tipo",
        hue_order=["# declaradas", "# alteradas"],
        palette=[COLOR_DECLARADAS, COLOR_ALTERADAS],
        ax=ax,
    )
    ax.set_xlabel("")
    ax.set_ylabel("# colunas")
    ax.set_title("Colunas declaradas vs. com conteúdo alterado, por migration")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.legend(title=None, frameon=False, loc="upper right")
    sns.despine(ax=ax)
    fig.tight_layout()

    path = out_dir / "colunas_por_migration.pdf"
    fig.savefig(path)
    fig.savefig(path.with_suffix(".png"))
    plt.close(fig)
    return path


def plot_linhas_removidas(df: pd.DataFrame, out_dir: Path) -> Path:
    """Figura 4x3: # linhas removidas em tabelas, por migration.

    Usa só o prefixo numérico da migration no eixo x (nomes completos não
    cabem em 12 categorias num eixo de 4 polegadas) — a legenda completa
    já está na Figura 1.
    """
    labels = [name.split("_", 1)[0] for name in df.index]

    fig, ax = plt.subplots(figsize=(4, 3))
    sns.barplot(
        x=labels,
        y=df["linhas_removidas_em_tabelas"],
        color=COLOR_REMOVIDAS,
        ax=ax,
    )
    ax.set_xlabel("migration (nº)")
    ax.set_ylabel("# linhas removidas")
    ax.set_title("Linhas removidas em tabelas")
    ax.set_ylim(bottom=0, top=max(1, df["linhas_removidas_em_tabelas"].max() * 1.2))
    sns.despine(ax=ax)
    fig.tight_layout()

    path = out_dir / "linhas_removidas_por_migration.pdf"
    fig.savefig(path)
    fig.savefig(path.with_suffix(".png"))
    plt.close(fig)
    return path


def main() -> int:
    report_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _latest_report()
    print(f"usando relatório: {report_path}")

    df = load_summary(report_path)
    PLOTS_DIR.mkdir(exist_ok=True)
    _set_style()

    for path in (plot_colunas(df, PLOTS_DIR), plot_linhas_removidas(df, PLOTS_DIR)):
        print(f"gerado: {path} (+ .png)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
