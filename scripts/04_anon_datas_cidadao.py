"""Migration 04 - Anonimizacao de datas de nascimento e registros.

Troca apenas o dia da data de nascimento, preservando mes e ano. O novo
dia e deterministico por cidadao e valido para o mes/ano original.

As demais colunas de data/timestamp da mesma tabela sao descobertas em
tempo de execucao (via `information_schema`) e deslocadas pelo mesmo
numero de dias aplicado ao nascimento, preservando a diferenca em dias
entre nascimento e registro longitudinal. Isso evita depender de uma lista
curada a mao por tabela, que historicamente ficou incompleta (so 5 das ~53
tabelas tinham as colunas de registro declaradas).

Algumas tabelas de detalhe (`tb_fat_atd_ind_*`, `tb_fat_atend_odonto_*`)
tem `nu_cpf_cidadao` mas nao tem `dt_nascimento` proprio - confirmado
contra o schema real. Para essas, o delta e calculado via join com
`tb_cidadao` (`SATELLITE_TABLES`), e esse passo roda ANTES do loop
principal, enquanto `tb_cidadao.dt_nascimento` ainda esta no valor
original (senao o delta seria calculado a partir de uma data ja
deslocada).
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("04_anon_datas_cidadao")


@dataclass(frozen=True)
class DateTable:
    schema: str
    table: str
    birth_column: str
    cpf_column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"'


DATE_TABLES: list[DateTable] = [
    DateTable("public", "ta_ativ_col_cidadao_particip", "dt_nascimento", "nu_cpf"),
    DateTable("public", "ta_cidadao", "dt_nascimento", "nu_cpf"),
    DateTable("public", "ta_cidadao", "dt_nascimento_responsavel", "nu_cpf_responsavel"),
    DateTable("public", "ta_cidadao", "dt_nascimento_cuidador", "nu_cpf_cuidador"),
    DateTable("public", "ta_prof", "dt_nascimento", "nu_cpf"),
    DateTable("public", "tb_acomp_cidadaos_vinculados", "dt_nascimento_cidadao", "nu_cpf_cidadao"),
    DateTable("public", "tb_atend_prof_ad", "dt_nascimento_cuidador", "nu_cpf_cuidador"),
    DateTable("public", "tb_ativ_col_cidadao_particip", "dt_nascimento", "nu_cpf"),
    DateTable("public", "tb_cds_atend_domiciliar", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_atend_individual", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_atend_odonto", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_ativ_col_participante", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_aval_elegibilidade", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_cad_individual", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_cad_individual", "dt_nascimento_responsavel", "nu_cpf_responsavel"),
    DateTable("public", "tb_cds_domicilio_familia", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_ficha_consumo_alimentar", "dt_nascimento_cidadao", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_proced", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_vacinacao", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cds_visita_domiciliar", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_cidadao", "dt_nascimento", "nu_cpf"),
    DateTable("public", "tb_cidadao", "dt_nascimento_responsavel", "nu_cpf_responsavel"),
    DateTable("public", "tb_cidadao", "dt_nascimento_cuidador", "nu_cpf_cuidador"),
    DateTable("public", "tb_cidadao_grupo_ativ_col", "dt_nascimento", "nu_cpf"),
    DateTable("public", "tb_fat_atendimento_domiciliar", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_atendimento_individual", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_atendimento_odonto", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_atvdd_coletiva_part", "dt_participante_nascimento", "nu_cpf_participante"),
    DateTable("public", "tb_fat_avaliacao_elegibilidade", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_cad_individual", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_cuidado_compartilhado", "dt_nascimento_cidadao", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_marca_consumo_alimnt", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_proced_atend", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_proced_atend_proced", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_vacinacao", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_visita_domiciliar", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_prof", "dt_nascimento", "nu_cpf"),
    DateTable("public", "tl_atend_prof_ad", "dt_nascimento_cuidador", "nu_cpf_cuidador"),
    DateTable("public", "tl_cds_atend_domiciliar", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_atend_individual", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_atend_odonto", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_ativ_col_participante", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_aval_elegibilidade", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_cad_individual", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_cad_individual", "dt_nascimento_responsavel", "nu_cpf_responsavel"),
    DateTable("public", "tl_cds_domicilio_familia", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_ficha_consumo_alimentar", "dt_nascimento_cidadao", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_proced", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_vacinacao", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cds_visita_domiciliar", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tl_cidadao", "dt_nascimento", "nu_cpf"),
    DateTable("public", "tl_cidadao", "dt_nascimento_responsavel", "nu_cpf_responsavel"),
    DateTable("public", "tl_cidadao", "dt_nascimento_cuidador", "nu_cpf_cuidador"),
    DateTable("public", "tl_cidadao_grupo_ativ_col", "dt_nascimento", "nu_cpf"),
    DateTable("public", "tl_prof", "dt_nascimento", "nu_cpf"),
]


@dataclass(frozen=True)
class SatelliteTable:
    """Tabela com `nu_cpf_cidadao` mas sem `dt_nascimento` proprio - o
    delta e obtido via join com `REFERENCE_TABLE`."""

    schema: str
    table: str
    cpf_column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"'


REFERENCE_SCHEMA = "public"
REFERENCE_TABLE = "tb_cidadao"
REFERENCE_CPF_COLUMN = "nu_cpf"
REFERENCE_BIRTH_COLUMN = "dt_nascimento"

SATELLITE_TABLES: list[SatelliteTable] = [
    SatelliteTable("public", "tb_fat_atd_ind_exames", "nu_cpf_cidadao"),
    SatelliteTable("public", "tb_fat_atd_ind_medicamentos", "nu_cpf_cidadao"),
    SatelliteTable("public", "tb_fat_atd_ind_problemas", "nu_cpf_cidadao"),
    SatelliteTable("public", "tb_fat_atd_ind_procedimentos", "nu_cpf_cidadao"),
    SatelliteTable("public", "tb_fat_atend_odonto_encaminham", "nu_cpf_cidadao"),
    SatelliteTable("public", "tb_fat_atend_odonto_exames", "nu_cpf_cidadao"),
    SatelliteTable("public", "tb_fat_atend_odonto_medicament", "nu_cpf_cidadao"),
    SatelliteTable("public", "tb_fat_atend_odonto_problemas", "nu_cpf_cidadao"),
    SatelliteTable("public", "tb_fat_atend_odonto_proced", "nu_cpf_cidadao"),
]

_DATE_TYPES = ("date", "timestamp without time zone", "timestamp with time zone")

# Padroes de nome de coluna que, mesmo sendo date/timestamp, nao sao evento
# clinico do cidadao (sao metadado de sistema/integracao) - nao devem ser
# deslocados junto com a data de nascimento.
_NON_CLINICAL_PATTERNS = (
    "%atualizacao%",
    "%insercao%",
    "%exportacao%",
    "%importacao%",
    "%migracao%",
    "%envio%",
    "%recebimento%",
)


def _column_exists(conn: Connection, schema: str, table: str, column: str) -> bool:
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
        {"schema": schema, "table": table, "column": column},
    ).first()
    return found is not None


def _discover_record_columns(
    conn: Connection, schema: str, table: str, exclude_column: str | None
) -> list[tuple[str, str]]:
    """Descobre colunas de data/timestamp da tabela, exceto a de nascimento
    (quando houver) e padroes que nao representam evento clinico do
    cidadao.

    Retorna pares (coluna, data_type) para que o UPDATE monte a expressao
    certa por tipo (soma de dias inteiros para `date`, de `interval` para
    `timestamp`).
    """
    type_list = ", ".join(f"'{t}'" for t in _DATE_TYPES)
    exclude = " AND ".join(f"column_name NOT ILIKE '{p}'" for p in _NON_CLINICAL_PATTERNS)
    exclude_clause = "AND column_name <> :exclude_column" if exclude_column else ""
    rows = conn.execute(
        text(
            f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND data_type IN ({type_list})
              {exclude_clause}
              AND ({exclude})
            ORDER BY column_name
            """
        ),
        {"schema": schema, "table": table, "exclude_column": exclude_column},
    )
    return [(r.column_name, r.data_type) for r in rows]


def _build_new_birth_expr(birth_ref: str, cpf_ref: str) -> str:
    month_start = f"date_trunc('month', {birth_ref}::date)::date"
    next_month = f"({month_start} + interval '1 month')::date"
    days_in_month = f"(({next_month} - {month_start})::int)"
    seed = f"(('x' || substr(md5({cpf_ref}::text), 1, 8))::bit(32)::bigint)"
    new_day_offset = f"({seed} % {days_in_month})::int"
    return f"({month_start} + {new_day_offset})"


def _process_satellite_tables(conn: Connection) -> int:
    """Desloca colunas de data de tabelas sem `dt_nascimento` proprio, via
    join com `REFERENCE_TABLE`. Precisa rodar ANTES do loop principal,
    enquanto a data de nascimento de referencia ainda esta no valor
    original (senao o delta seria calculado a partir de uma data ja
    deslocada)."""
    if not _column_exists(conn, REFERENCE_SCHEMA, REFERENCE_TABLE, REFERENCE_BIRTH_COLUMN):
        log.warning(
            "tabela de referencia ausente (%s.%s.%s) - tabelas satelite puladas",
            REFERENCE_SCHEMA,
            REFERENCE_TABLE,
            REFERENCE_BIRTH_COLUMN,
        )
        return 0

    new_birth = _build_new_birth_expr(
        f'ref."{REFERENCE_BIRTH_COLUMN}"', f'ref."{REFERENCE_CPF_COLUMN}"'
    )
    delta_days = f'({new_birth} - ref."{REFERENCE_BIRTH_COLUMN}"::date)'

    total = 0
    for sat in SATELLITE_TABLES:
        if not _column_exists(conn, sat.schema, sat.table, sat.cpf_column):
            log.warning("tabela/coluna ausente, pulando %s: %s", sat.qualified, sat.cpf_column)
            continue

        record_columns = _discover_record_columns(conn, sat.schema, sat.table, exclude_column=None)
        if not record_columns:
            log.debug("%s: nenhuma coluna de data a deslocar", sat.qualified)
            continue

        assignments = []
        for column, data_type in record_columns:
            if data_type == "date":
                assignments.append(f'"{column}" = t."{column}" + {delta_days}')
            else:
                assignments.append(
                    f'"{column}" = t."{column}" + ({delta_days} * interval \'1 day\')'
                )

        result = conn.execute(
            text(
                f'UPDATE "{sat.schema}"."{sat.table}" AS t '
                f"SET {', '.join(assignments)} "
                f'FROM "{REFERENCE_SCHEMA}"."{REFERENCE_TABLE}" AS ref '
                f'WHERE t."{sat.cpf_column}" = ref."{REFERENCE_CPF_COLUMN}" '
                f'  AND t."{sat.cpf_column}" IS NOT NULL '
                f'  AND btrim(t."{sat.cpf_column}"::text) <> \'\' '
                f'  AND ref."{REFERENCE_BIRTH_COLUMN}" IS NOT NULL'
            )
        )
        log.info(
            "%s (satelite): %d linha(s) atualizada(s), %d coluna(s) de registro deslocada(s) (%s)",
            sat.qualified,
            result.rowcount,
            len(record_columns),
            ", ".join(c for c, _ in record_columns),
        )
        total += result.rowcount or 0
    return total


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao de datas de nascimento e registros...")

    with engine.begin() as conn:
        # Tabelas satelite primeiro - dependem da data de nascimento de
        # referencia ainda estar no valor original.
        satellite_total = _process_satellite_tables(conn)

        total = 0
        for target in DATE_TABLES:
            required = (target.birth_column, target.cpf_column)
            missing_required = [
                column
                for column in required
                if not _column_exists(conn, target.schema, target.table, column)
            ]
            if missing_required:
                log.warning(
                    "tabela/coluna obrigatoria ausente, pulando %s: %s",
                    target.qualified,
                    ", ".join(missing_required),
                )
                continue

            record_columns = _discover_record_columns(
                conn, target.schema, target.table, exclude_column=target.birth_column
            )
            new_birth = _build_new_birth_expr(f't."{target.birth_column}"', f't."{target.cpf_column}"')
            old_birth = f't."{target.birth_column}"'
            delta_days = f"({new_birth} - {old_birth}::date)"

            assignments = [f'"{target.birth_column}" = {new_birth}']
            for column, data_type in record_columns:
                if data_type == "date":
                    assignments.append(f'"{column}" = t."{column}" + {delta_days}')
                else:
                    assignments.append(
                        f'"{column}" = t."{column}" + ({delta_days} * interval \'1 day\')'
                    )

            result = conn.execute(
                text(
                    f'UPDATE "{target.schema}"."{target.table}" AS t '
                    f"SET {', '.join(assignments)} "
                    f'WHERE t."{target.birth_column}" IS NOT NULL '
                    f'  AND t."{target.cpf_column}" IS NOT NULL '
                    f'  AND btrim(t."{target.cpf_column}"::text) <> \'\''
                )
            )
            log.info(
                "%s: %d linha(s) atualizada(s), %d coluna(s) de registro deslocada(s) (%s)",
                target.qualified,
                result.rowcount,
                len(record_columns),
                ", ".join(c for c, _ in record_columns) or "-",
            )
            total += result.rowcount or 0

        log.info(
            "concluido: %d linha(s) com datas anonimizadas (%d em tabelas satelite).",
            total + satellite_total,
            satellite_total,
        )
