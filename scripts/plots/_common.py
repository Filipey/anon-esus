"""Utilitários compartilhados pelos scripts de plotagem (`scripts/plots/`).

Estilo visual, conexão com o banco e helpers de consulta genéricos usados
por mais de um script de plotagem (`antropometrico.py`,
`condicoes_medicas.py`, ...) — mesma estética "estilo LaTeX" já usada em
`scripts/plot_report.py`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sqlalchemy import Engine, text

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
PLOTS_DIR = ROOT / "plots"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pipeline_logging import get_logger  # noqa: E402

# Paleta própria (não é a default do matplotlib/seaborn), na mesma família
# de `scripts/plot_report.py`: azul petróleo para o valor "neutro"/volume,
# âmbar para um segundo série, vermelho escuro reservado para métricas de
# risco (raridade, cardinalidade alta).
COLOR_PRIMARY = "#2E4057"
COLOR_SECONDARY = "#F18F01"
COLOR_RISK = "#9E2A2B"


def set_latex_style() -> None:
    """Visual "estilo LaTeX" (serif + mathtext Computer Modern), idêntico ao
    usado em `scripts/plot_report.py` — sem exigir LaTeX instalado."""
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


def load_module(filename: str) -> ModuleType:
    """Importa um arquivo .py de `scripts/` cujo nome pode não ser um
    identificador Python válido (ex.: `00_connect_db.py`)."""
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"não foi possível carregar {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def load_engine() -> Engine:
    return load_module("00_connect_db.py").engine


def save_fig(fig, stem: str) -> Path:
    """Salva a figura em .pdf e .png (mesma convenção de plot_report.py)."""
    PLOTS_DIR.mkdir(exist_ok=True)
    path = PLOTS_DIR / f"{stem}.pdf"
    fig.savefig(path)
    fig.savefig(path.with_suffix(".png"))
    plt.close(fig)
    return path


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    row = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :s AND table_name = :t AND column_name = :c
            """
        ),
        {"s": schema, "t": table, "c": column},
    ).first()
    return row is not None


def fetch_numeric_series(engine: Engine, schema: str, table: str, column: str) -> pd.Series:
    """Lê todos os valores não-nulos de uma coluna numérica como `pd.Series`."""
    with engine.connect() as conn:
        if not column_exists(conn, schema, table, column):
            return pd.Series(dtype="float64")
        query = text(
            f'SELECT "{column}"::double precision AS v FROM "{schema}"."{table}" '
            f'WHERE "{column}" IS NOT NULL'
        )
        df = pd.read_sql(query, conn)
    return df["v"]


def fetch_cardinality(engine: Engine, schema: str, table: str, column: str) -> dict:
    """Total de linhas, não-nulos e valores distintos de uma coluna."""
    with engine.connect() as conn:
        if not column_exists(conn, schema, table, column):
            return {"total_rows": 0, "non_null": 0, "distinct": 0}
        row = conn.execute(
            text(
                f'SELECT count(*) AS total, count("{column}") AS non_null, '
                f'count(DISTINCT "{column}") AS distinct_count '
                f'FROM "{schema}"."{table}"'
            )
        ).one()
    return {"total_rows": row.total, "non_null": row.non_null, "distinct": row.distinct_count}


def fetch_value_counts(
    engine: Engine, schema: str, table: str, column: str, top_n: int = 30
) -> pd.DataFrame:
    """Top-N valores mais frequentes de uma coluna categórica/codificada."""
    with engine.connect() as conn:
        if not column_exists(conn, schema, table, column):
            return pd.DataFrame(columns=["valor", "contagem"])
        query = text(
            f'SELECT "{column}"::text AS valor, count(*) AS contagem '
            f'FROM "{schema}"."{table}" '
            f'WHERE "{column}" IS NOT NULL '
            f'GROUP BY "{column}" '
            f'ORDER BY contagem DESC '
            f"LIMIT :top_n"
        )
        df = pd.read_sql(query, conn, params={"top_n": top_n})
    return df


def fetch_rarity(engine: Engine, schema: str, table: str, column: str, threshold: int = 5) -> dict:
    """Quantos valores distintos (e quantas linhas) têm contagem <= threshold.

    Proxy de risco de reidentificação: um código (ex.: CIAP/CID de doença
    rara) que aparece poucas vezes na base funciona como
    quase-identificador, mesmo sem ser nominalmente um dado direto.
    """
    with engine.connect() as conn:
        if not column_exists(conn, schema, table, column):
            return {"distinct_raros": 0, "linhas_raras": 0, "distinct_total": 0, "linhas_total": 0}
        row = conn.execute(
            text(
                f"""
                WITH contagens AS (
                    SELECT "{column}" AS v, count(*) AS n
                    FROM "{schema}"."{table}"
                    WHERE "{column}" IS NOT NULL
                    GROUP BY "{column}"
                )
                SELECT
                    count(*) FILTER (WHERE n <= :threshold) AS distinct_raros,
                    COALESCE(sum(n) FILTER (WHERE n <= :threshold), 0) AS linhas_raras,
                    count(*) AS distinct_total,
                    sum(n) AS linhas_total
                FROM contagens
                """
            ),
            {"threshold": threshold},
        ).one()
    return {
        "distinct_raros": row.distinct_raros,
        "linhas_raras": row.linhas_raras or 0,
        "distinct_total": row.distinct_total,
        "linhas_total": row.linhas_total or 0,
    }
