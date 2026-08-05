"""Migration 02 — Anonimização de nomes e CNES de Unidades de Saúde.

Substitui o nome de cada unidade de saúde por uma denominação genérica
("Unidade de Saúde 1", "Unidade de Saúde 2", ...) e o código CNES por um
código fictício de 7 dígitos — o CNES é público e, sozinho, permite
reidentificar a unidade mesmo depois do nome ser trocado pelo rótulo
genérico.

Características (mesmas garantias da migration 01):
- **Atômica**: roda inteira dentro de uma única transação; qualquer
  falha faz rollback e o banco permanece no estado original.
- **Consistente entre tabelas**: o mesmo nome (ou CNES) original recebe
  sempre o mesmo valor fictício em todas as colunas. A numeração do nome é
  determinística (nomes ordenados alfabeticamente); o CNES fictício é
  derivado por hash do valor original — ambos reprodutíveis entre
  execuções.

As colunas a anonimizar são declaradas explicitamente em `NAME_COLUMNS` e
`CNES_COLUMNS`. Antes de aplicar, o script valida que cada coluna existe;
entradas inexistentes são puladas com aviso (não abortam a migration).
"""

from __future__ import annotations

import hashlib
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

# ---------------------------------------------------------------------------
# Colunas que armazenam o código CNES da unidade. Diferente de
# `co_dim_unidade_saude` (chave substituta opaca, preserva vínculo sem
# precisar de tratamento), aqui o valor é o código público real copiado
# diretamente em cada tabela — se só as 4 primeiras (tabelas "mestras")
# fossem trocadas, o CNES original sobreviveria nas outras 23 e permitiria
# religar a unidade fictícia à unidade real via join. Confirmado contra o
# schema físico real (`docs/auditoria_schema.md`, categoria "CNES
# unidade").
# ---------------------------------------------------------------------------
CNES_COLUMNS: list[NameColumn] = [
    NameColumn("public", "ta_unidade_saude", "nu_cnes"),
    NameColumn("public", "tb_unidade_saude", "nu_cnes"),
    NameColumn("public", "tb_dim_unidade_saude", "nu_cnes"),
    NameColumn("public", "tl_unidade_saude", "nu_cnes"),
    NameColumn("public", "ta_cds_domicilio", "nu_cnes"),
    NameColumn("public", "ta_cidadao_vinculacao_equipe", "nu_cnes"),
    NameColumn("public", "ta_equipe_unificacao_base", "nu_cnes"),
    NameColumn("public", "ta_unidade_saude_unif_base", "nu_cnes"),
    NameColumn("public", "tb_cds_domicilio", "nu_cnes"),
    NameColumn("public", "tb_cds_ficha_ativ_col", "nu_cnes"),
    NameColumn("public", "tb_cds_prof", "nu_cnes"),
    NameColumn("public", "tb_cidadao_nucleo_familiar", "nu_cnes"),
    NameColumn("public", "tb_cidadao_vinculacao_equipe", "nu_cnes"),
    NameColumn("public", "tb_equipe_unificacao_base", "nu_cnes"),
    NameColumn("public", "tb_familia", "nu_cnes"),
    NameColumn("public", "tb_grupo_ativ_col", "nu_cnes"),
    NameColumn("public", "tb_prof_grupo_ativ_col", "nu_cnes"),
    NameColumn("public", "tb_revisao", "nu_cnes"),
    NameColumn("public", "tb_unidade_saude_unif_base", "nu_cnes"),
    NameColumn("public", "tl_cds_domicilio", "nu_cnes"),
    NameColumn("public", "tl_cds_ficha_ativ_col", "nu_cnes"),
    NameColumn("public", "tl_cds_prof", "nu_cnes"),
    NameColumn("public", "tl_cidadao_nucleo_familiar", "nu_cnes"),
    NameColumn("public", "tl_cidadao_vinculacao_equipe", "nu_cnes"),
    NameColumn("public", "tl_familia", "nu_cnes"),
    NameColumn("public", "tl_grupo_ativ_col", "nu_cnes"),
    NameColumn("public", "tl_prof_grupo_ativ_col", "nu_cnes"),
]

CNES_SALT = "anon-esus-unidade-cnes-v1"


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


def _fake_cnes(value: str) -> str:
    digest = hashlib.md5(f"{value}{CNES_SALT}".encode()).hexdigest()
    number = int(digest[:8], 16) % 10_000_000
    return f"{number:07d}"


def _anon_names(conn: Connection) -> int:
    targets = [col for col in NAME_COLUMNS if _column_exists(conn, col)]
    for col in NAME_COLUMNS:
        if col not in targets:
            log.warning("coluna inexistente, pulando: %s", col.qualified)

    if not targets:
        log.info("nenhuma coluna de unidade de saúde encontrada — nada a fazer.")
        return 0

    names: set[str] = set()
    for col in targets:
        valores = _collect_raw_values(conn, col)
        log.debug("%s: %d nome(s) distinto(s) coletado(s)", col.qualified, len(valores))
        names |= valores

    if not names:
        log.info("nenhum nome de unidade a anonimizar.")
        return 0

    # Mapeamento determinístico e consistente:
    # nome original -> "Unidade de Saúde N" (ordem alfabética estável).
    name_to_label = {
        name: GENERIC_TEMPLATE.format(n=i) for i, name in enumerate(sorted(names), start=1)
    }
    log.info("%d unidade(s) distinta(s) a anonimizar (nome)", len(name_to_label))

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
    return total


def _anon_cnes(conn: Connection) -> int:
    targets = [col for col in CNES_COLUMNS if _column_exists(conn, col)]
    for col in CNES_COLUMNS:
        if col not in targets:
            log.warning("coluna inexistente, pulando: %s", col.qualified)

    if not targets:
        return 0

    codes: set[str] = set()
    for col in targets:
        codes |= _collect_raw_values(conn, col)

    if not codes:
        return 0

    code_to_fake = {code: _fake_cnes(code) for code in codes}
    log.info("%d CNES distinto(s) a anonimizar", len(code_to_fake))

    conn.execute(
        text(
            "CREATE TEMP TABLE _unidade_cnes_map "
            "(old_cnes text PRIMARY KEY, new_cnes text NOT NULL) "
            "ON COMMIT DROP"
        )
    )
    conn.execute(
        text("INSERT INTO _unidade_cnes_map (old_cnes, new_cnes) VALUES (:old, :new)"),
        [{"old": old, "new": new} for old, new in code_to_fake.items()],
    )

    total = 0
    for col in targets:
        result = conn.execute(
            text(
                f'UPDATE "{col.schema}"."{col.table}" AS t '
                f'SET "{col.column}" = m.new_cnes '
                f"FROM _unidade_cnes_map m "
                f"WHERE t.\"{col.column}\"::text = m.old_cnes"
            )
        )
        log.info("%s: %d linha(s) atualizada(s)", col.qualified, result.rowcount)
        total += result.rowcount or 0
    return total


def run(engine: Engine) -> None:
    """Executa a migration de forma atômica."""
    log.info("iniciando anonimização de nomes e CNES de unidades de saúde...")

    with engine.begin() as conn:
        name_total = _anon_names(conn)
        cnes_total = _anon_cnes(conn)
        log.info(
            "concluído: %d linha(s) de nome e %d linha(s) de CNES atualizada(s).",
            name_total,
            cnes_total,
        )
