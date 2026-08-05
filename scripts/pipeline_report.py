"""Relatorio de auditoria da pipeline: o que mudou, quantitativa e
qualitativamente, sem expor nenhum valor real.

Antes de rodar as migrations, `build_snapshot()` tira uma "foto" de cada
coluna declarada em alguma migration (linhas totais da tabela, quantos
valores nao-nulos, e um checksum agregado order-independent dos valores) e
de cada tabela que `12_anon_ip_logs.py` deleta ou esvazia. Depois de rodar
todas as migrations, `build_snapshot()` tira a mesma foto de novo;
`build_report()` compara as duas.

O checksum prova que o conteudo de uma coluna mudou sem nunca expor um
valor real no relatorio - e a soma (order-independent) de um hash por
linha, igual ao mecanismo ja usado em `08_anon_antropometrico.py`/
`10_anon_cns.py`, so que aqui e usado pra comparar, nao pra substituir.

Isso e uma segunda passada completa pelas tabelas-alvo (uma antes, uma
depois) - em tabelas muito grandes, cada passada e uma varredura
sequencial da coluna. Rode com tempo disponivel antes de aplicar a
pipeline no banco real.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType

from pipeline_logging import get_logger
from sqlalchemy import Engine, text

log = get_logger("pipeline_report")

SCRIPTS_DIR = Path(__file__).resolve().parent


def _load_module(filename: str) -> ModuleType:
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"não foi possível carregar {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class ColumnTarget:
    migration: str
    schema: str
    table: str
    column: str


@dataclass(frozen=True)
class TableTarget:
    migration: str
    schema: str
    table: str
    action: str  # "delete" ou "scrub"


@dataclass
class ColumnSnapshot:
    target: ColumnTarget
    exists: bool = False
    total_rows: int = 0
    non_null: int = 0
    checksum: str = "0"


@dataclass
class TableSnapshot:
    target: TableTarget
    exists: bool = False
    total_rows: int = 0


def _column_targets() -> list[ColumnTarget]:
    """(migração, schema, tabela, coluna) de todas as migrations 01-11,
    reaproveitando o mesmo extrator usado por `audit_schema.py`."""
    audit = _load_module("audit_schema.py")
    declared = audit._declared_columns()
    return [ColumnTarget(d.migration, d.schema, d.table, d.column) for d in declared]


def _table_targets() -> list[TableTarget]:
    """Tabelas de `12_anon_ip_logs.py`, que operam por linha/tabela
    inteira em vez de por coluna."""
    m12 = _load_module("12_anon_ip_logs.py")
    targets = [
        TableTarget("12_anon_ip_logs", t.schema, t.table, "delete") for t in m12.DELETE_TABLES
    ]
    targets.append(TableTarget("12_anon_ip_logs", m12.SCRUB_SCHEMA, m12.SCRUB_TABLE, "scrub"))
    return targets


def _snapshot_column(conn, target: ColumnTarget) -> ColumnSnapshot:
    snap = ColumnSnapshot(target)
    exists = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :s AND table_name = :t AND column_name = :c
            """
        ),
        {"s": target.schema, "t": target.table, "c": target.column},
    ).first()
    if not exists:
        return snap
    snap.exists = True
    col = target.column
    checksum_expr = (
        f"COALESCE(sum((('x' || substr(md5(\"{col}\"::text), 1, 8))"
        "::bit(32)::bigint)::numeric), 0)"
    )
    row = conn.execute(
        text(
            f'SELECT count(*) AS total, count("{col}") AS non_null, '
            f"{checksum_expr} AS checksum "
            f'FROM "{target.schema}"."{target.table}"'
        )
    ).one()
    snap.total_rows = row.total
    snap.non_null = row.non_null
    snap.checksum = str(row.checksum)
    return snap


def _snapshot_table(conn, target: TableTarget) -> TableSnapshot:
    snap = TableSnapshot(target)
    exists = conn.execute(
        text("SELECT 1 FROM information_schema.tables WHERE table_schema = :s AND table_name = :t"),
        {"s": target.schema, "t": target.table},
    ).first()
    if not exists:
        return snap
    snap.exists = True
    snap.total_rows = conn.execute(
        text(f'SELECT count(*) FROM "{target.schema}"."{target.table}"')
    ).scalar()
    return snap


def build_snapshot(engine: Engine) -> dict:
    """Tira a foto de todas as colunas/tabelas-alvo. Chamar antes e depois
    de rodar as migrations, com os MESMOS alvos (a ordem de
    `_column_targets`/`_table_targets` é estável entre chamadas)."""
    columns: list[ColumnSnapshot] = []
    tables: list[TableSnapshot] = []
    with engine.connect() as conn:
        for target in _column_targets():
            try:
                columns.append(_snapshot_column(conn, target))
            except Exception:
                log.exception(
                    "falha ao tirar foto de %s.%s.%s (%s)",
                    target.schema,
                    target.table,
                    target.column,
                    target.migration,
                )
                columns.append(ColumnSnapshot(target))
        for target in _table_targets():
            try:
                tables.append(_snapshot_table(conn, target))
            except Exception:
                log.exception(
                    "falha ao tirar foto de %s.%s (%s)",
                    target.schema,
                    target.table,
                    target.migration,
                )
                tables.append(TableSnapshot(target))
    return {"columns": columns, "tables": tables}


def _column_diff(before: ColumnSnapshot, after: ColumnSnapshot) -> dict:
    return {
        "tabela": f"{before.target.schema}.{before.target.table}",
        "coluna": before.target.column,
        "existia_antes": before.exists,
        "existe_depois": after.exists,
        "linhas_antes": before.total_rows,
        "linhas_depois": after.total_rows,
        "nao_nulos_antes": before.non_null,
        "nao_nulos_depois": after.non_null,
        "conteudo_mudou": before.checksum != after.checksum,
    }


def _table_diff(before: TableSnapshot, after: TableSnapshot) -> dict:
    return {
        "tabela": f"{before.target.schema}.{before.target.table}",
        "acao": before.target.action,
        "existia_antes": before.exists,
        "existe_depois": after.exists,
        "linhas_antes": before.total_rows,
        "linhas_depois": after.total_rows,
        "linhas_removidas": max(before.total_rows - after.total_rows, 0),
    }


def build_report(before: dict, after: dict, started_at: datetime, finished_at: datetime) -> dict:
    by_migration: dict[str, dict] = {}

    for b, a in zip(before["columns"], after["columns"], strict=True):
        entry = by_migration.setdefault(b.target.migration, {"colunas": [], "tabelas": []})
        entry["colunas"].append(_column_diff(b, a))

    for b, a in zip(before["tables"], after["tables"], strict=True):
        entry = by_migration.setdefault(b.target.migration, {"colunas": [], "tabelas": []})
        entry["tabelas"].append(_table_diff(b, a))

    resumo = {}
    for migration, entry in by_migration.items():
        resumo[migration] = {
            "colunas_declaradas": len(entry["colunas"]),
            "colunas_com_conteudo_alterado": sum(
                1 for c in entry["colunas"] if c["conteudo_mudou"]
            ),
            "colunas_inexistentes_no_banco": sum(
                1 for c in entry["colunas"] if not c["existia_antes"]
            ),
            "tabelas_declaradas": len(entry["tabelas"]),
            "linhas_removidas_em_tabelas": sum(t["linhas_removidas"] for t in entry["tabelas"]),
        }

    return {
        "iniciado_em": started_at.isoformat(),
        "concluido_em": finished_at.isoformat(),
        "resumo_por_migration": resumo,
        "detalhe_por_migration": by_migration,
    }


def write_report(report: dict, path: Path) -> None:
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def log_summary(report: dict) -> None:
    log.info("=== Resumo da auditoria (quantitativo) ===")
    for migration, resumo in sorted(report["resumo_por_migration"].items()):
        log.info(
            "%s: %d/%d coluna(s) com conteudo alterado, %d coluna(s) inexistente(s) no banco, "
            "%d linha(s) removida(s) em tabela(s)",
            migration,
            resumo["colunas_com_conteudo_alterado"],
            resumo["colunas_declaradas"],
            resumo["colunas_inexistentes_no_banco"],
            resumo["linhas_removidas_em_tabelas"],
        )
