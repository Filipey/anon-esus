"""Migration 04 - Anonimizacao de datas de nascimento e registros.

Troca apenas o dia da data de nascimento, preservando mes e ano. O novo
dia e deterministico por cidadao e valido para o mes/ano original.

As datas de atendimento/registro da mesma linha sao deslocadas pelo mesmo
numero de dias aplicado ao nascimento, preservando a diferenca em dias
entre nascimento e registro longitudinal.
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
    record_columns: tuple[str, ...] = ()

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
    DateTable(
        "public",
        "tb_fat_atendimento_individual",
        "dt_nascimento",
        "nu_cpf_cidadao",
        ("dt_inicial_atendimento", "dt_final_atendimento"),
    ),
    DateTable(
        "public",
        "tb_fat_atendimento_odonto",
        "dt_nascimento",
        "nu_cpf_cidadao",
        ("dt_inicial_atendimento", "dt_final_atendimento"),
    ),
    DateTable("public", "tb_fat_atvdd_coletiva_part", "dt_participante_nascimento", "nu_cpf_participante"),
    DateTable("public", "tb_fat_avaliacao_elegibilidade", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable("public", "tb_fat_cad_individual", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable(
        "public",
        "tb_fat_cuidado_compartilhado",
        "dt_nascimento_cidadao",
        "nu_cpf_cidadao",
        ("dt_evolucao", "dt_evolucao_anterior", "dt_criacao_cuidado"),
    ),
    DateTable("public", "tb_fat_marca_consumo_alimnt", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable(
        "public",
        "tb_fat_proced_atend",
        "dt_nascimento",
        "nu_cpf_cidadao",
        ("dt_inicial_atendimento", "dt_final_atendimento"),
    ),
    DateTable("public", "tb_fat_proced_atend_proced", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable(
        "public",
        "tb_fat_vacinacao",
        "dt_nascimento",
        "nu_cpf_cidadao",
        ("dt_inicial_atendimento", "dt_final_atendimento"),
    ),
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


def _existing_record_columns(conn: Connection, target: DateTable) -> tuple[str, ...]:
    return tuple(
        column
        for column in target.record_columns
        if _column_exists(conn, target.schema, target.table, column)
    )


def _build_new_birth_expr(target: DateTable) -> str:
    birth = f't."{target.birth_column}"'
    cpf = f't."{target.cpf_column}"'
    month_start = f"date_trunc('month', {birth}::date)::date"
    next_month = f"({month_start} + interval '1 month')::date"
    days_in_month = f"(({next_month} - {month_start})::int)"
    seed = f"(('x' || substr(md5({cpf}::text), 1, 8))::bit(32)::bigint)"
    new_day_offset = f"({seed} % {days_in_month})::int"
    return f"({month_start} + {new_day_offset})"


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao de datas de nascimento e registros...")

    with engine.begin() as conn:
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

            record_columns = _existing_record_columns(conn, target)
            new_birth = _build_new_birth_expr(target)
            old_birth = f't."{target.birth_column}"'
            delta = f"({new_birth} - {old_birth}::date)"
            assignments = [f'"{target.birth_column}" = {new_birth}']
            assignments.extend(
                f'"{column}" = t."{column}" + ({delta} * interval \'1 day\')'
                for column in record_columns
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
                "%s: %d linha(s) atualizada(s), %d coluna(s) de registro deslocada(s)",
                target.qualified,
                result.rowcount,
                len(record_columns),
            )
            total += result.rowcount or 0

        log.info("concluido: %d linha(s) com datas anonimizadas.", total)
