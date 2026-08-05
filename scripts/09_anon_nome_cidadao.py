"""Migration 09 - Anonimizacao do nome do cidadao.

A guideline original define regra de nome ficticio para profissional e
denominacao generica para unidade de saude, mas nao menciona o nome do
proprio cidadao. A auditoria real do banco encontrou 11 colunas que
guardam nome do cidadao (proprio, mae, pai ou nome social) em texto claro
mesmo depois do CPF e do e-mail anonimizados - substitui por nome ficticio
para fechar essa lacuna.

Diferente de `05_anon_profissional.py`, nao ha sobrenome fixo exigido pela
guideline para cidadao - usa nome completo ficticio comum. Cada coluna e
mapeada de forma independente (nao ha requisito de correlacionar o nome
ficticio da mae com o registro dela como cidada).
"""

from __future__ import annotations

from dataclasses import dataclass

from faker import Faker
from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("09_anon_nome_cidadao")


@dataclass(frozen=True)
class NameColumn:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# Colunas de nome de cidadao (proprio, mae, pai, social) confirmadas na
# auditoria real do banco (categoria "Nome cidadao").
# ---------------------------------------------------------------------------
NAME_COLUMNS: list[NameColumn] = [
    NameColumn("public", "ta_ativ_col_cidadao_particip", "no_nome"),
    NameColumn("public", "tb_ativ_col_cidadao_particip", "no_nome"),
    NameColumn("public", "tb_fat_avaliacao_elegibilidade", "no_nome"),
    NameColumn("public", "tb_fat_avaliacao_elegibilidade", "no_nome_mae"),
    NameColumn("public", "tb_fat_avaliacao_elegibilidade", "no_nome_pai"),
    NameColumn("public", "tb_fat_avaliacao_elegibilidade", "no_nome_social"),
    NameColumn("public", "tb_fat_cad_individual", "no_nome"),
    NameColumn("public", "tb_fat_cad_individual", "no_nome_mae"),
    NameColumn("public", "tb_fat_cad_individual", "no_nome_pai"),
    NameColumn("public", "tb_fat_cad_individual", "no_nome_social"),
    NameColumn("public", "tb_fat_marca_consumo_alimnt", "no_nome"),
]

FAKER_LOCALE = "pt_BR"
FAKER_SEED = 20260803


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


def _fake_name(index: int) -> str:
    fake = Faker(FAKER_LOCALE)
    fake.seed_instance(FAKER_SEED + index)
    return fake.name()


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao de nomes de cidadaos...")

    with engine.begin() as conn:
        targets = [col for col in NAME_COLUMNS if _column_exists(conn, col)]
        for col in NAME_COLUMNS:
            if col not in targets:
                log.warning("coluna inexistente, pulando: %s", col.qualified)

        if not targets:
            log.info("nenhuma coluna de nome de cidadao encontrada — nada a fazer.")
            return

        names: set[str] = set()
        for col in targets:
            values = _collect_raw_values(conn, col)
            log.debug("%s: %d nome(s) distinto(s) coletado(s)", col.qualified, len(values))
            names |= values

        if not names:
            log.info("nenhum nome de cidadao a anonimizar.")
            return

        name_to_fake = {name: _fake_name(i) for i, name in enumerate(sorted(names))}
        conn.execute(
            text(
                "CREATE TEMP TABLE _nome_cidadao_map "
                "(old_name text PRIMARY KEY, new_name text NOT NULL) "
                "ON COMMIT DROP"
            )
        )
        conn.execute(
            text("INSERT INTO _nome_cidadao_map (old_name, new_name) VALUES (:old, :new)"),
            [{"old": old, "new": new} for old, new in name_to_fake.items()],
        )

        total = 0
        for col in targets:
            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" AS t '
                    f'SET "{col.column}" = m.new_name '
                    f"FROM _nome_cidadao_map m "
                    f'WHERE t."{col.column}"::text = m.old_name'
                )
            )
            log.info("%s: %d nome(s) atualizado(s)", col.qualified, result.rowcount)
            total += result.rowcount or 0

        log.info(
            "concluido: %d nome(s) distinto(s) anonimizado(s), %d linha(s) atualizada(s).",
            len(name_to_fake),
            total,
        )
