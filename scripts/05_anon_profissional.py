"""Migration 05 - Anonimizacao de dados identificadores de profissionais.

Preserva categoria profissional e registros de saude, mas substitui nomes
por nomes ficticios com sobrenome "Teste" e registros profissionais por
``99999``. Colunas inexistentes sao puladas com aviso.

O CNS do profissional nao e alterado aqui: o mapeamento do DW marca esse
campo como pendente de definicao por exigir gerador/validador de CNS.
"""

from __future__ import annotations

from dataclasses import dataclass

from faker import Faker
from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("05_anon_profissional")


@dataclass(frozen=True)
class ColumnTarget:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


NAME_COLUMNS: list[ColumnTarget] = [
    ColumnTarget("public", "ta_prof", "no_civil_profissional"),
    ColumnTarget("public", "ta_prof", "no_profissional"),
    ColumnTarget("public", "ta_prof", "no_profissional_filtro"),
    ColumnTarget("public", "ta_prof", "no_social_profissional"),
    ColumnTarget("public", "tb_dim_profissional", "no_profissional"),
    ColumnTarget("public", "tb_lote_transp_historico_exprt", "no_profissional"),
    ColumnTarget("public", "tb_prof", "no_civil_profissional"),
    ColumnTarget("public", "tb_prof", "no_profissional_filtro"),
    ColumnTarget("public", "tb_prof", "no_social_profissional"),
    ColumnTarget("public", "tl_prof", "no_profissional_filtro"),
]

REGISTRATION_COLUMNS: list[ColumnTarget] = [
    ColumnTarget("public", "ta_prof", "nu_conselho_classe"),
    ColumnTarget("public", "tb_prof", "nu_conselho_classe"),
    ColumnTarget("public", "tl_prof", "nu_conselho_classe"),
    # tb_atend_prof e um "retrato" do profissional no momento do
    # atendimento - guarda sua propria copia do registro, confirmada
    # contra o schema real (nao e a mesma linha de tb_prof).
    ColumnTarget("public", "ta_atend_prof", "nu_conselho_classe"),
    ColumnTarget("public", "tb_atend_prof", "nu_conselho_classe"),
    ColumnTarget("public", "tl_atend_prof", "nu_conselho_classe"),
]

FAKER_LOCALE = "pt_BR"
FAKER_SEED = 20260714
FAKE_LAST_NAME = "Teste"
GENERIC_REGISTRATION = "99999"


def _column_exists(conn: Connection, col: ColumnTarget) -> bool:
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


def _collect_raw_values(conn: Connection, col: ColumnTarget) -> set[str]:
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
    if index % 2 == 0:
        first_name = fake.first_name_female()
    else:
        first_name = fake.first_name_male()
    return f"{first_name} {FAKE_LAST_NAME}"


def _anon_names(conn: Connection) -> int:
    targets = [col for col in NAME_COLUMNS if _column_exists(conn, col)]
    for col in NAME_COLUMNS:
        if col not in targets:
            log.warning("coluna inexistente, pulando: %s", col.qualified)

    names: set[str] = set()
    for col in targets:
        values = _collect_raw_values(conn, col)
        log.debug("%s: %d nome(s) distinto(s) coletado(s)", col.qualified, len(values))
        names |= values

    if not names:
        return 0

    name_to_fake = {
        name: _fake_name(i)
        for i, name in enumerate(sorted(names))
    }
    conn.execute(
        text(
            "CREATE TEMP TABLE _prof_name_map "
            "(old_name text PRIMARY KEY, new_name text NOT NULL) "
            "ON COMMIT DROP"
        )
    )
    conn.execute(
        text("INSERT INTO _prof_name_map (old_name, new_name) VALUES (:old, :new)"),
        [{"old": old, "new": new} for old, new in name_to_fake.items()],
    )

    total = 0
    for col in targets:
        result = conn.execute(
            text(
                f'UPDATE "{col.schema}"."{col.table}" AS t '
                f'SET "{col.column}" = m.new_name '
                f"FROM _prof_name_map m "
                f'WHERE t."{col.column}"::text = m.old_name'
            )
        )
        log.info("%s: %d nome(s) atualizado(s)", col.qualified, result.rowcount)
        total += result.rowcount or 0
    return total


def _anon_registrations(conn: Connection) -> int:
    total = 0
    for col in REGISTRATION_COLUMNS:
        if not _column_exists(conn, col):
            log.warning("coluna inexistente, pulando: %s", col.qualified)
            continue

        result = conn.execute(
            text(
                f'UPDATE "{col.schema}"."{col.table}" '
                f'SET "{col.column}" = :registration '
                f'WHERE "{col.column}" IS NOT NULL '
                f"  AND btrim(\"{col.column}\"::text) <> ''"
            ),
            {"registration": GENERIC_REGISTRATION},
        )
        log.info("%s: %d registro(s) atualizado(s)", col.qualified, result.rowcount)
        total += result.rowcount or 0
    return total


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao de profissionais...")

    with engine.begin() as conn:
        name_total = _anon_names(conn)
        registration_total = _anon_registrations(conn)
        log.info(
            "concluido: %d nome(s) e %d registro(s) profissional(is) anonimizados.",
            name_total,
            registration_total,
        )
