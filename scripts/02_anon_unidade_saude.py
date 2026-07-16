"""Migration 02 — Anonimização de nomes de Unidades de Saúde.

Substitui o nome de cada unidade de saúde por uma denominação genérica
("Unidade de Saúde 1", "Unidade de Saúde 2", ...).

Características (mesmas garantias da migration 01):
- **Atômica**: roda inteira dentro de uma única transação; qualquer
  falha faz rollback e o banco permanece no estado original.
- **Consistente entre tabelas**: o mesmo nome original recebe sempre o
  mesmo rótulo em todas as colunas. A numeração é determinística (nomes
  ordenados alfabeticamente), então execuções repetidas produzem o mesmo
  mapeamento.

As colunas a anonimizar são declaradas explicitamente em `NAME_COLUMNS`.
Antes de aplicar, o script valida que cada coluna existe; entradas
inexistentes são puladas com aviso (não abortam a migration).
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("02_anon_unidade_saude")


@dataclass(frozen=True)
class NameColumn:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# Lista explícita de colunas que armazenam o nome da unidade de saúde.
#
# Pré-populada com colunas conhecidas do e-SUS APS/PEC. AJUSTE conforme o
# schema real da sua base. Colunas inexistentes são apenas puladas.
# ---------------------------------------------------------------------------
NAME_COLUMNS: list[NameColumn] = [
    NameColumn("public", "ta_unidade_saude", "no_unidade_saude"),
    NameColumn("public", "tb_unidade_saude", "no_unidade_saude"),
    NameColumn("public", "tb_dim_unidade_saude", "no_unidade_saude"),
    NameColumn("public", "tl_unidade_saude", "no_unidade_saude"),
]

GENERIC_TEMPLATE = "Unidade de Saúde {n}"


def _column_exists(conn: Connection, col: NameColumn) -> bool:
    found = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"schema": col.schema, "table": col.table, "column": col.column},
    ).first()
    return found is not None


def _collect_raw_values(conn: Connection, col: NameColumn) -> set[str]:
    rows = conn.execute(
        text(
            f'SELECT DISTINCT "{col.column}" AS v '
            f'FROM "{col.schema}"."{col.table}" '
            f'WHERE "{col.column}" IS NOT NULL '
            f"  AND btrim(\"{col.column}\"::text) <> ''"
        )
    )
    return {str(r.v) for r in rows}


def run(engine: Engine) -> None:
    """Executa a migration de forma atômica."""
    log.info("iniciando anonimização de nomes de unidades de saúde...")

    with engine.begin() as conn:
        # 1) Resolve quais colunas realmente existem na base.
        targets = []
        for col in NAME_COLUMNS:
            if _column_exists(conn, col):
                log.debug("coluna-alvo encontrada: %s", col.qualified)
                targets.append(col)
            else:
                log.warning("coluna inexistente, pulando: %s", col.qualified)

        if not targets:
            log.info("nenhuma coluna de unidade de saúde encontrada — nada a fazer.")
            return

        # 2) Coleta todos os nomes distintos de todas as colunas.
        names: set[str] = set()
        for col in targets:
            valores = _collect_raw_values(conn, col)
            log.debug("%s: %d nome(s) distinto(s) coletado(s)", col.qualified, len(valores))
            names |= valores

        if not names:
            log.info("nenhum nome de unidade a anonimizar.")
            return

        # 3) Mapeamento determinístico e consistente:
        #    nome original -> "Unidade de Saúde N" (ordem alfabética estável).
        name_to_label = {
            name: GENERIC_TEMPLATE.format(n=i)
            for i, name in enumerate(sorted(names), start=1)
        }
        log.info("%d unidade(s) distinta(s) a anonimizar", len(name_to_label))

        # 4) Tabela temporária de mapeamento + UPDATE por join (atômico).
        conn.execute(
            text(
                "CREATE TEMP TABLE _unidade_map "
                "(old_name text PRIMARY KEY, new_name text NOT NULL) "
                "ON COMMIT DROP"
            )
        )
        conn.execute(
            text("INSERT INTO _unidade_map (old_name, new_name) VALUES (:old, :new)"),
            [{"old": old, "new": new} for old, new in name_to_label.items()],
        )

        total = 0
        for col in targets:
            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" AS t '
                    f'SET "{col.column}" = m.new_name '
                    f"FROM _unidade_map m "
                    f"WHERE t.\"{col.column}\"::text = m.old_name"
                )
            )
            log.info("%s: %d linha(s) atualizada(s)", col.qualified, result.rowcount)
            total += result.rowcount or 0

        log.info(
            "concluído: %d unidade(s) anonimizada(s), %d linha(s) atualizada(s).",
            len(name_to_label),
            total,
        )
