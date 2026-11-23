"""Migration 04 - Anonimizacao de datas de nascimento e registros.

Troca apenas o dia da data de nascimento, preservando mes e ano. O novo
dia e deterministico por cidadao e valido para o mes/ano original.

As datas de atendimento/registro da mesma linha sao deslocadas pelo mesmo
numero de dias aplicado ao nascimento, preservando a diferenca em dias
entre nascimento e registro longitudinal.

Algumas tabelas fato (ex: tb_fat_visita_domiciliar) nao tem uma coluna de
data literal para o evento: a data so existe via co_dim_tempo, uma chave
estrangeira para a dimensao de calendario compartilhada tb_dim_tempo (uma
linha por dia, usada por todos os cidadaos daquele dia). Nao e possivel
simplesmente somar dias a essa chave. Para essas tabelas, DIM_TEMPO_TABLES
reaponta a FK para a linha de tb_dim_tempo que corresponde a data original
mais o mesmo deslocamento aplicado ao nascimento do cidadao naquela linha,
preservando o intervalo em dias entre nascimento e evento.

Outras tabelas (tb_atend, tb_atend_prof) tem data literal (dt_inicio,
dt_fim), mas nao tem CPF nem nascimento na propria linha: o cidadao so e
encontrado via join (tb_atend -> tb_prontuario -> tb_cidadao). Essas
tabelas nunca entravam em DATE_TABLES, entao suas datas nunca eram
deslocadas, mesmo com o nascimento do cidadao mudando, o que quebra
qualquer calculo que compare idade com data de atendimento (ex: "primeira
consulta ate 30 dias de vida" em desenvolvimento infantil). JOINED_DATE_TABLES
cobre esse caso.
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
    fk_cidadao_pec_column: str | None = None
    seed_fallback_column: str | None = None

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"'


DATE_TABLES: list[DateTable] = [
    DateTable("public", "ta_ativ_col_cidadao_particip", "dt_nascimento", "nu_cpf"),
    DateTable("public", "ta_cidadao", "dt_nascimento", "nu_cpf"),
    DateTable("public", "ta_cidadao", "dt_nascimento_responsavel", "nu_cpf_responsavel"),
    DateTable("public", "ta_cidadao", "dt_nascimento_cuidador", "nu_cpf_cuidador"),
    DateTable("public", "ta_prof", "dt_nascimento", "nu_cpf"),
    DateTable("public", "tb_acomp_cidadaos_vinculados", "dt_nascimento_cidadao", "nu_cpf_cidadao", (), "co_fat_cidadao_pec"),
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
    DateTable("public", "tb_cidadao", "dt_nascimento", "nu_cpf", (), None, "co_seq_cidadao"),
    DateTable("public", "tb_cidadao", "dt_nascimento_responsavel", "nu_cpf_responsavel"),
    DateTable("public", "tb_cidadao", "dt_nascimento_cuidador", "nu_cpf_cuidador"),
    DateTable("public", "tb_cidadao_grupo_ativ_col", "dt_nascimento", "nu_cpf"),
    DateTable("public", "tb_fat_atendimento_domiciliar", "dt_nascimento", "nu_cpf_cidadao", (), "co_fat_cidadao_pec"),
    DateTable(
        "public",
        "tb_fat_atendimento_individual",
        "dt_nascimento",
        "nu_cpf_cidadao",
        ("dt_inicial_atendimento", "dt_final_atendimento"),
        "co_fat_cidadao_pec",
    ),
    DateTable(
        "public",
        "tb_fat_atendimento_odonto",
        "dt_nascimento",
        "nu_cpf_cidadao",
        ("dt_inicial_atendimento", "dt_final_atendimento"),
        "co_fat_cidadao_pec",
    ),
    DateTable("public", "tb_fat_atvdd_coletiva_part", "dt_participante_nascimento", "nu_cpf_participante", (), "co_fat_cidadao_pec"),
    DateTable("public", "tb_fat_avaliacao_elegibilidade", "dt_nascimento", "nu_cpf_cidadao", (), "co_fat_cidadao_pec"),
    DateTable("public", "tb_fat_cad_individual", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable(
        "public",
        "tb_fat_cuidado_compartilhado",
        "dt_nascimento_cidadao",
        "nu_cpf_cidadao",
        ("dt_evolucao", "dt_evolucao_anterior", "dt_criacao_cuidado"),
        "co_fat_cidadao_pec",
    ),
    DateTable("public", "tb_fat_marca_consumo_alimnt", "dt_nascimento", "nu_cpf_cidadao"),
    DateTable(
        "public",
        "tb_fat_proced_atend",
        "dt_nascimento",
        "nu_cpf_cidadao",
        ("dt_inicial_atendimento", "dt_final_atendimento"),
        "co_fat_cidadao_pec",
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


@dataclass(frozen=True)
class DimTempoTable:
    """Tabela fato cuja data do evento so existe via FK para tb_dim_tempo.

    `dim_tempo_column` e a coluna a reapontar (ex: co_dim_tempo). O
    deslocamento e calculado a partir de `birth_column`/`cpf_column` na
    mesma linha, com a mesma formula usada para a data de nascimento.
    """

    schema: str
    table: str
    birth_column: str
    cpf_column: str
    dim_tempo_column: str
    fk_cidadao_pec_column: str | None = None
    # _build_new_birth_expr le este campo; sem ele a migration aborta com
    # AttributeError no primeiro passo. None mantem a semente so pelo CPF da
    # linha (linhas sem CPF seguem pelo fallback via co_fat_cidadao_pec).
    seed_fallback_column: str | None = None

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"'


# ---------------------------------------------------------------------------
# Tabelas fato que representam a data do evento apenas via tb_dim_tempo,
# sem coluna de data literal. tb_fat_visita_domiciliar e a origem confirmada
# do bug de "intervalo nascimento-visita" em desenvolvimento infantil: o
# dia de nascimento era deslocado, mas a data da visita (so em co_dim_tempo)
# nunca era. As outras 3 abaixo tem exatamente o mesmo padrao de schema
# (so dt_nascimento + co_dim_tempo, sem dt_inicial_atendimento/
# dt_final_atendimento), por isso tratamos preventivamente. Revise novas
# tabelas fato com esse mesmo padrao se surgirem.
#
# `fk_cidadao_pec_column`: algumas linhas tem birth_column/cpf_column NULOS
# na propria linha (10-20% das linhas em alguns casos, confirmado via
# comparacao direta entre bases), mas sao identificaveis de forma confiavel
# via essa FK ate tb_fat_cidadao_pec.co_cidadao -> tb_cidadao, sem depender
# de CPF em texto. Quando presente, essas linhas tambem sao corrigidas (ver
# _run_dim_tempo_tables_fallback_fk).
# ---------------------------------------------------------------------------
DIM_TEMPO_TABLES: list[DimTempoTable] = [
    DimTempoTable("public", "tb_fat_visita_domiciliar", "dt_nascimento", "nu_cpf_cidadao", "co_dim_tempo", "co_fat_cidadao_pec"),
    DimTempoTable("public", "tb_fat_atendimento_domiciliar", "dt_nascimento", "nu_cpf_cidadao", "co_dim_tempo"),
    DimTempoTable("public", "tb_fat_proced_atend_proced", "dt_nascimento", "nu_cpf_cidadao", "co_dim_tempo", "co_fat_cidadao_pec"),
    DimTempoTable("public", "tb_fat_avaliacao_elegibilidade", "dt_nascimento", "nu_cpf_cidadao", "co_dim_tempo"),
    DimTempoTable("public", "tb_fat_marca_consumo_alimnt", "dt_nascimento", "nu_cpf_cidadao", "co_dim_tempo", "co_fat_cidadao_pec"),
    # Essas duas tem AS DUAS representacoes (coluna literal + co_dim_tempo).
    # A coluna literal ja e corrigida pelo loop de DATE_TABLES abaixo, mas
    # co_dim_tempo e independente e tambem precisa ser reapontado: 100% das
    # linhas com CPF valido em tb_fat_vacinacao tinham co_dim_tempo
    # identico entre base real e anonimizada, mesmo quando a coluna literal
    # ja estava corrigida.
    DimTempoTable("public", "tb_fat_vacinacao", "dt_nascimento", "nu_cpf_cidadao", "co_dim_tempo", "co_fat_cidadao_pec"),
    DimTempoTable("public", "tb_fat_cad_individual", "dt_nascimento", "nu_cpf_cidadao", "co_dim_tempo"),
]


@dataclass(frozen=True)
class JoinedDateTable:
    """Tabela com data literal, mas sem CPF/nascimento na propria linha:
    o cidadao so e encontrado seguindo um caminho de join até tb_cidadao.

    `from_tables` lista as tabelas intermediarias (alias incluido), e
    `where_join` traz as condicoes que as encadeiam até "c" (tb_cidadao),
    incluindo a correlacao com "t" (a tabela sendo atualizada). Tudo isso
    fica no WHERE, nao no ON de um JOIN: um UPDATE ... FROM nao permite
    referenciar a tabela alvo (t) dentro do ON de um JOIN no FROM.
    """

    schema: str
    table: str
    record_columns: tuple[str, ...]
    from_tables: str
    where_join: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"'


# ---------------------------------------------------------------------------
# tb_atend e tb_atend_prof guardam dt_inicio/dt_fim literais, mas nao tem
# CPF nem nascimento na propria linha (sao achados via prontuario). Como
# nunca apareciam em DATE_TABLES, suas datas nunca eram deslocadas: o
# nascimento do cidadao mudava, mas a data de cada atendimento continuava
# sendo a real, o que quebra qualquer calculo de idade-no-atendimento (ex:
# "primeira consulta ate 30 dias de vida" em desenvolvimento infantil).
# Confirmado comparando tb_atend_prof entre as duas bases: dt_inicio
# identico ate o milissegundo antes desta correcao.
# ---------------------------------------------------------------------------
JOINED_DATE_TABLES: list[JoinedDateTable] = [
    JoinedDateTable(
        "public", "tb_atend", ("dt_inicio", "dt_fim"),
        '"public"."tb_prontuario" p, "public"."tb_cidadao" c',
        'p."co_seq_prontuario" = t."co_prontuario" AND c."co_seq_cidadao" = p."co_cidadao"',
    ),
    JoinedDateTable(
        "public", "tb_atend_prof", ("dt_inicio", "dt_fim"),
        '"public"."tb_atend" a, "public"."tb_prontuario" p, "public"."tb_cidadao" c',
        'a."co_seq_atend" = t."co_atend" AND p."co_seq_prontuario" = a."co_prontuario" '
        'AND c."co_seq_cidadao" = p."co_cidadao"',
    ),
]


# ---------------------------------------------------------------------------
# Toda uma familia de tabelas clinicas (tb_medicao, tb_problema_evolucao,
# tb_receita_medicamento, tb_requisicao_exame, tb_alergia_evolucao,
# tb_atestado, tb_cirurgias_internacoes, tb_ivcf, suas correspondentes ta_*
# (historico) e tl_* (log), entre outras) e encontrada apenas via
# co_atend_prof -> tb_atend_prof -> tb_atend -> tb_prontuario -> tb_cidadao,
# e nenhuma delas nunca esteve em DATE_TABLES/DIM_TEMPO_TABLES/
# JOINED_DATE_TABLES. Descoberto a partir de tb_medicao: dataUltimaMedicao-
# PressaoArterial/PesoAltura continuavam retornando a data real (identica a
# base original) mesmo apos o nascimento do cidadao ser deslocado, causando
# a quase totalidade das divergencias de diabetes/hipertensao/pessoa idosa.
# Em vez de listar tabela por tabela, descobrimos em tempo de execucao todas
# as tabelas com coluna "co_atend_prof" e deslocamos suas colunas de data
# (exceto dt_auditoria, que e metadado de quando o registro de auditoria foi
# escrito, nao uma data clinica do cidadao).
# ---------------------------------------------------------------------------
ATEND_PROF_FAMILY_EXCLUDE_TABLES = {"tb_atend", "tb_atend_prof"}
ATEND_PROF_FAMILY_EXCLUDE_COLUMNS = {"dt_auditoria"}
ATEND_PROF_FAMILY_DATE_TYPES = (
    "date",
    "timestamp without time zone",
    "timestamp with time zone",
)


def _run_atend_prof_family_tables(conn: Connection) -> None:
    tables = conn.execute(
        text(
            """
            SELECT DISTINCT table_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name = 'co_atend_prof'
            ORDER BY table_name
            """
        )
    ).scalars().all()

    birth_table_cidadao = DateTable("public", "tb_cidadao", "dt_nascimento", "nu_cpf", (), None, "co_seq_cidadao")
    new_birth_expr = _build_new_birth_expr(birth_table_cidadao, alias="c")
    delta = f'({new_birth_expr} - c."dt_nascimento"::date)'

    for table in tables:
        if table in ATEND_PROF_FAMILY_EXCLUDE_TABLES:
            continue
        date_columns = conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table
                  AND data_type = ANY(:types)
                ORDER BY column_name
                """
            ),
            {"table": table, "types": list(ATEND_PROF_FAMILY_DATE_TYPES)},
        ).scalars().all()
        record_columns = [c for c in date_columns if c not in ATEND_PROF_FAMILY_EXCLUDE_COLUMNS]
        if not record_columns:
            continue

        assignments = ", ".join(
            f'"{column}" = t."{column}" + ({delta} * interval \'1 day\')'
            for column in record_columns
        )
        result = conn.execute(
            text(
                f'UPDATE "public"."{table}" AS t '
                f"SET {assignments} "
                f'FROM "public"."tb_atend_prof" ap, "public"."tb_atend" a, '
                f'     "public"."tb_prontuario" p, "public"."tb_cidadao" c '
                f'WHERE ap."co_seq_atend_prof" = t."co_atend_prof" '
                f'  AND a."co_seq_atend" = ap."co_atend" '
                f'  AND p."co_seq_prontuario" = a."co_prontuario" '
                f'  AND c."co_seq_cidadao" = p."co_cidadao" '
                f'  AND t."co_atend_prof" IS NOT NULL '
                f'  AND c."dt_nascimento" IS NOT NULL'
            )
        )
        log.info(
            "%s: %d linha(s) com data deslocada via co_atend_prof -> tb_cidadao (colunas: %s).",
            table, result.rowcount, ", ".join(record_columns),
        )


# ---------------------------------------------------------------------------
# Segunda familia, descoberta ao investigar o residuo de diabetes depois da
# correcao acima: tabelas que tem "co_prontuario" diretamente (sem precisar
# passar por co_atend_prof/tb_atend), como tb_exame_requisitado (usada para
# "data da ultima solicitacao de hemoglobina glicada"), tb_pre_natal (inclui
# dt_ultima_menstruacao), tb_antecedente, tb_ad_cidadao, etc. Mesmo caso:
# nunca estiveram em nenhuma lista de anonimizacao. Tabelas que tambem tem
# "co_atend_prof" sao excluidas aqui porque ja foram corrigidas (com todas
# as suas colunas de data) pela familia acima.
# ---------------------------------------------------------------------------
PRONTUARIO_FAMILY_EXCLUDE_TABLES = {"tb_atend", "tb_acomp_cidadaos_vinculados"}


def _run_prontuario_family_tables(conn: Connection) -> None:
    atend_prof_tables = set(
        conn.execute(
            text(
                """
                SELECT DISTINCT table_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND column_name = 'co_atend_prof'
                """
            )
        ).scalars().all()
    )

    tables = conn.execute(
        text(
            """
            SELECT DISTINCT table_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name = 'co_prontuario'
            ORDER BY table_name
            """
        )
    ).scalars().all()

    birth_table_cidadao = DateTable("public", "tb_cidadao", "dt_nascimento", "nu_cpf", (), None, "co_seq_cidadao")
    new_birth_expr = _build_new_birth_expr(birth_table_cidadao, alias="c")
    delta = f'({new_birth_expr} - c."dt_nascimento"::date)'

    for table in tables:
        if table in PRONTUARIO_FAMILY_EXCLUDE_TABLES or table in atend_prof_tables:
            continue
        date_columns = conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table
                  AND data_type = ANY(:types)
                ORDER BY column_name
                """
            ),
            {"table": table, "types": list(ATEND_PROF_FAMILY_DATE_TYPES)},
        ).scalars().all()
        record_columns = [c for c in date_columns if c not in ATEND_PROF_FAMILY_EXCLUDE_COLUMNS]
        if not record_columns:
            continue

        assignments = ", ".join(
            f'"{column}" = t."{column}" + ({delta} * interval \'1 day\')'
            for column in record_columns
        )
        result = conn.execute(
            text(
                f'UPDATE "public"."{table}" AS t '
                f"SET {assignments} "
                f'FROM "public"."tb_prontuario" p, "public"."tb_cidadao" c '
                f'WHERE p."co_seq_prontuario" = t."co_prontuario" '
                f'  AND c."co_seq_cidadao" = p."co_cidadao" '
                f'  AND t."co_prontuario" IS NOT NULL '
                f'  AND c."dt_nascimento" IS NOT NULL'
            )
        )
        log.info(
            "%s: %d linha(s) com data deslocada via co_prontuario -> tb_cidadao (colunas: %s).",
            table, result.rowcount, ", ".join(record_columns),
        )


# ---------------------------------------------------------------------------
# Terceira familia, descoberta investigando um valor de "primeira consulta"
# que nao mudava entre as duas bases mesmo sem bater com nenhuma tabela ja
# corrigida: varias tabelas "tb_fat_rel_op_*" (relatorio operacional de
# crianca/gestante/risco cardiovascular), "tb_fat_op_acompanhamento_idosa",
# "tb_fat_ivcf", "tb_fat_complementar" etc. tem "co_fat_cidadao_pec"
# diretamente (sem precisar de co_atend_prof nem co_prontuario) e nunca
# estiveram em nenhuma lista de anonimizacao. Sao justamente as tabelas
# pre-computadas que alimentam os indicadores de acompanhamento (crianca,
# gestante, risco cardio, idosa), entao esse gap explicava divergencias
# que nao vinham de nenhuma das duas familias anteriores.
# ---------------------------------------------------------------------------
FAT_CIDADAO_PEC_FAMILY_EXCLUDE_TABLES = {
    "tb_acomp_cidadaos_vinculados",
    "tb_fat_atendimento_domiciliar",
    "tb_fat_atendimento_individual",
    "tb_fat_atendimento_odonto",
    "tb_fat_atvdd_coletiva_part",
    "tb_fat_avaliacao_elegibilidade",
    "tb_fat_cad_individual",
    "tb_fat_cuidado_compartilhado",
    "tb_fat_marca_consumo_alimnt",
    "tb_fat_proced_atend",
    "tb_fat_proced_atend_proced",
    "tb_fat_vacinacao",
    "tb_fat_visita_domiciliar",
}


def _run_fat_cidadao_pec_family_tables(conn: Connection) -> None:
    atend_prof_tables = set(
        conn.execute(
            text(
                """
                SELECT DISTINCT table_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND column_name = 'co_atend_prof'
                """
            )
        ).scalars().all()
    )
    prontuario_tables = set(
        conn.execute(
            text(
                """
                SELECT DISTINCT table_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND column_name = 'co_prontuario'
                """
            )
        ).scalars().all()
    )

    tables = conn.execute(
        text(
            """
            SELECT DISTINCT table_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name = 'co_fat_cidadao_pec'
            ORDER BY table_name
            """
        )
    ).scalars().all()

    birth_table_cidadao = DateTable("public", "tb_cidadao", "dt_nascimento", "nu_cpf", (), None, "co_seq_cidadao")
    new_birth_expr = _build_new_birth_expr(birth_table_cidadao, alias="c")
    delta = f'({new_birth_expr} - c."dt_nascimento"::date)'

    for table in tables:
        if (
            table in FAT_CIDADAO_PEC_FAMILY_EXCLUDE_TABLES
            or table in atend_prof_tables
            or table in prontuario_tables
        ):
            continue
        date_columns = conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table
                  AND data_type = ANY(:types)
                ORDER BY column_name
                """
            ),
            {"table": table, "types": list(ATEND_PROF_FAMILY_DATE_TYPES)},
        ).scalars().all()
        record_columns = [c for c in date_columns if c not in ATEND_PROF_FAMILY_EXCLUDE_COLUMNS]
        if not record_columns:
            continue

        assignments = ", ".join(
            f'"{column}" = t."{column}" + ({delta} * interval \'1 day\')'
            for column in record_columns
        )
        result = conn.execute(
            text(
                f'UPDATE "public"."{table}" AS t '
                f"SET {assignments} "
                f'FROM "public"."tb_fat_cidadao_pec" AS fcp, "public"."tb_cidadao" AS c '
                f'WHERE fcp."co_seq_fat_cidadao_pec" = t."co_fat_cidadao_pec" '
                f'  AND c."co_seq_cidadao" = fcp."co_cidadao" '
                f'  AND t."co_fat_cidadao_pec" IS NOT NULL '
                f'  AND c."dt_nascimento" IS NOT NULL'
            )
        )
        log.info(
            "%s: %d linha(s) com data deslocada via co_fat_cidadao_pec -> tb_cidadao (colunas: %s).",
            table, result.rowcount, ", ".join(record_columns),
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


def _existing_record_columns(conn: Connection, target: DateTable) -> tuple[str, ...]:
    return tuple(
        column
        for column in target.record_columns
        if _column_exists(conn, target.schema, target.table, column)
    )


def _build_new_birth_expr(target: DateTable, alias: str = "t") -> str:
    birth = f'{alias}."{target.birth_column}"'
    cpf = f'{alias}."{target.cpf_column}"'
    seed_source = f"{cpf}::text"
    if target.seed_fallback_column:
        fallback = f'{alias}."{target.seed_fallback_column}"'
        seed_source = f"COALESCE({cpf}::text, {fallback}::text)"
    month_start = f"date_trunc('month', {birth}::date)::date"
    next_month = f"({month_start} + interval '1 month')::date"
    days_in_month = f"(({next_month} - {month_start})::int)"
    seed = f"(('x' || substr(md5({seed_source}), 1, 8))::bit(32)::bigint)"
    new_day_offset = f"({seed} % {days_in_month})::int"
    return f"({month_start} + {new_day_offset})"


def _run_dim_tempo_tables(conn: Connection) -> None:
    """Reaponta co_dim_tempo (ou equivalente) para a linha de tb_dim_tempo
    que corresponde a data original mais o deslocamento do nascimento.

    Nao da pra somar dias numa FK: a mesma linha de tb_dim_tempo e
    compartilhada por todos os cidadaos daquele dia. Por isso buscamos,
    para cada linha, a NOVA linha de tb_dim_tempo cuja data bate com
    data_original + delta (o mesmo delta aplicado ao nascimento do
    cidadao naquela linha).
    """
    if not _column_exists(conn, "public", "tb_dim_tempo", "dt_registro"):
        log.warning("tb_dim_tempo ausente ou sem dt_registro; pulando reaponta de dim_tempo.")
        return

    for target in DIM_TEMPO_TABLES:
        required = (target.birth_column, target.cpf_column, target.dim_tempo_column)
        missing = [
            column
            for column in required
            if not _column_exists(conn, target.schema, target.table, column)
        ]
        if missing:
            log.warning(
                "tabela/coluna obrigatoria ausente, pulando %s: %s",
                target.qualified,
                ", ".join(missing),
            )
            continue

        new_birth = _build_new_birth_expr(target)
        old_birth = f't."{target.birth_column}"'
        delta = f"({new_birth} - {old_birth}::date)"
        base_where = (
            f'dt_old."co_seq_dim_tempo" = t."{target.dim_tempo_column}" '
            f'AND t."{target.birth_column}" IS NOT NULL '
            f'AND t."{target.cpf_column}" IS NOT NULL '
            f"AND btrim(t.\"{target.cpf_column}\"::text) <> ''"
        )

        sem_destino = conn.execute(
            text(
                f'SELECT count(*) FROM {target.qualified} AS t '
                f'JOIN "public"."tb_dim_tempo" AS dt_old '
                f'  ON dt_old."co_seq_dim_tempo" = t."{target.dim_tempo_column}" '
                f'LEFT JOIN "public"."tb_dim_tempo" AS dt_new '
                f"  ON dt_new.\"dt_registro\" = (dt_old.\"dt_registro\" + ({delta}) * interval '1 day')::date "
                f'WHERE t."{target.birth_column}" IS NOT NULL '
                f'  AND t."{target.cpf_column}" IS NOT NULL '
                f"  AND btrim(t.\"{target.cpf_column}\"::text) <> '' "
                f'  AND dt_new."co_seq_dim_tempo" IS NULL'
            )
        ).scalar_one()
        if sem_destino:
            log.warning(
                "%s: %d linha(s) sem data de destino em tb_dim_tempo (nao reapontadas, "
                "verifique se tb_dim_tempo cobre o intervalo necessario).",
                target.qualified,
                sem_destino,
            )

        # O ON de um JOIN dentro do FROM de um UPDATE nao pode referenciar a
        # propria tabela sendo atualizada (t); por isso dt_old e dt_new sao
        # listados separados (cross join) e toda a correlacao com t fica no
        # WHERE, onde isso e permitido.
        result = conn.execute(
            text(
                f'UPDATE {target.qualified} AS t '
                f'SET "{target.dim_tempo_column}" = dt_new."co_seq_dim_tempo" '
                f'FROM "public"."tb_dim_tempo" AS dt_old, "public"."tb_dim_tempo" AS dt_new '
                f"WHERE dt_new.\"dt_registro\" = (dt_old.\"dt_registro\" + ({delta}) * interval '1 day')::date "
                f"  AND {base_where}"
            )
        )
        log.info(
            "%s: %d linha(s) com %s reapontada(s) para a data correta.",
            target.qualified,
            result.rowcount,
            target.dim_tempo_column,
        )

        if target.fk_cidadao_pec_column and _column_exists(
            conn, "public", "tb_fat_cidadao_pec", "co_cidadao"
        ):
            _run_dim_tempo_fallback_fk(conn, target)


def _run_dim_tempo_fallback_fk(conn: Connection, target: DimTempoTable) -> None:
    """Corrige linhas que o passo acima pulou por terem birth_column/
    cpf_column nulos na propria linha. Essas linhas ainda sao identificaveis
    de forma confiavel via fk_cidadao_pec_column -> tb_fat_cidadao_pec.co_cidadao
    -> tb_cidadao, sem depender do CPF em texto da linha. Confirmado que isso
    cobre uma fracao relevante das linhas (10-20% em algumas tabelas).
    """
    fk = target.fk_cidadao_pec_column
    # Para achar o nascimento ORIGINAL (pre-deslocamento) do cidadao, usamos
    # a formula inversa: o nascimento atual (ja deslocado, se o loop principal
    # ja rodou) nao serve de base para recalcular o delta deterministicamente
    # a partir do CPF do cidadao (que so muda por acao do script 01, antes
    # deste). Por isso recomputamos o novo nascimento a partir do CPF atual
    # de tb_cidadao diretamente (mesma formula, consistente com o restante
    # do script, pois tb_cidadao.dt_nascimento/.nu_cpf ainda nao foram
    # alterados por este script neste ponto da execucao).
    birth_table_cidadao = DateTable("public", "tb_cidadao", "dt_nascimento", "nu_cpf", (), None, "co_seq_cidadao")
    new_birth_expr = _build_new_birth_expr(birth_table_cidadao, alias="cid")
    delta = f'({new_birth_expr} - cid."dt_nascimento"::date)'

    result = conn.execute(
        text(
            f'UPDATE {target.qualified} AS t '
            f'SET "{target.dim_tempo_column}" = dt_new."co_seq_dim_tempo" '
            f'FROM "public"."tb_dim_tempo" AS dt_old, "public"."tb_dim_tempo" AS dt_new, '
            f'     "public"."tb_fat_cidadao_pec" AS fcp, "public"."tb_cidadao" AS cid '
            f'WHERE dt_old."co_seq_dim_tempo" = t."{target.dim_tempo_column}" '
            f"  AND dt_new.\"dt_registro\" = (dt_old.\"dt_registro\" + ({delta}) * interval '1 day')::date "
            f'  AND fcp."co_seq_fat_cidadao_pec" = t."{fk}" '
            f'  AND cid."co_seq_cidadao" = fcp."co_cidadao" '
            f'  AND t."{target.cpf_column}" IS NULL '
            f'  AND t."{fk}" IS NOT NULL '
            f'  AND cid."dt_nascimento" IS NOT NULL'
        )
    )
    log.info(
        "%s: %d linha(s) adicional(is) corrigida(s) via FK limpa (CPF nulo na propria linha).",
        target.qualified,
        result.rowcount,
    )


def _run_joined_date_tables(conn: Connection) -> None:
    """Desloca colunas de data literais em tabelas que nao tem CPF nem
    nascimento na propria linha, seguindo `join_sql` até tb_cidadao
    (alias "c") para calcular o delta.
    """
    for target in JOINED_DATE_TABLES:
        missing_cols = [
            column
            for column in target.record_columns
            if not _column_exists(conn, target.schema, target.table, column)
        ]
        if missing_cols:
            log.warning(
                "tabela/coluna ausente, pulando %s: %s",
                target.qualified,
                ", ".join(missing_cols),
            )
            continue

        birth_table = DateTable(target.schema, target.table, "dt_nascimento", "nu_cpf", (), None, "co_seq_cidadao")
        new_birth = _build_new_birth_expr(birth_table, alias="c")
        delta = f'({new_birth} - c."dt_nascimento"::date)'
        assignments = ", ".join(
            f'"{column}" = t."{column}" + ({delta} * interval \'1 day\')'
            for column in target.record_columns
        )

        result = conn.execute(
            text(
                f'UPDATE {target.qualified} AS t '
                f"SET {assignments} "
                f"FROM {target.from_tables} "
                f"WHERE {target.where_join} "
                f'  AND c."dt_nascimento" IS NOT NULL'
            )
        )
        log.info(
            "%s: %d linha(s) com data deslocada via join ate tb_cidadao.",
            target.qualified,
            result.rowcount,
        )


def _run_date_tables_fallback_fk(conn: Connection) -> None:
    """Corrige, para as tabelas de DATE_TABLES que tem fk_cidadao_pec_column,
    as linhas que o loop principal (abaixo) vai pular por terem cpf_column
    nulo na propria linha (confirmado: 10-20% das linhas em algumas tabelas
    fato). Essas linhas sao identificaveis de forma confiavel via
    fk_cidadao_pec_column -> tb_fat_cidadao_pec.co_cidadao -> tb_cidadao, sem
    depender do CPF em texto da linha.

    Mesma exigencia de ordem que _run_dim_tempo_tables/_run_joined_date_tables:
    roda ANTES do loop principal deslocar tb_cidadao.dt_nascimento, porque o
    calculo de delta precisa do nascimento ORIGINAL (a formula e
    deterministica: recalcular sobre um valor ja deslocado "nao muda" em
    relacao a si mesmo, dando delta zero).
    """
    if not _column_exists(conn, "public", "tb_fat_cidadao_pec", "co_cidadao"):
        log.warning("tb_fat_cidadao_pec ausente ou sem co_cidadao; pulando fallback por FK limpa.")
        return

    birth_table_cidadao = DateTable("public", "tb_cidadao", "dt_nascimento", "nu_cpf", (), None, "co_seq_cidadao")
    new_birth_expr = _build_new_birth_expr(birth_table_cidadao, alias="cid")
    delta = f'({new_birth_expr} - cid."dt_nascimento"::date)'

    for target in DATE_TABLES:
        fk = target.fk_cidadao_pec_column
        if not fk:
            continue
        required = (target.cpf_column, fk)
        missing = [c for c in required if not _column_exists(conn, target.schema, target.table, c)]
        if missing:
            log.warning(
                "tabela/coluna obrigatoria ausente, pulando fallback de %s: %s",
                target.qualified,
                ", ".join(missing),
            )
            continue
        record_columns = _existing_record_columns(conn, target)
        has_birth_column = _column_exists(conn, target.schema, target.table, target.birth_column)

        assignments = []
        if has_birth_column:
            assignments.append(f'"{target.birth_column}" = {new_birth_expr}')
        assignments.extend(
            f'"{column}" = t."{column}" + ({delta} * interval \'1 day\')'
            for column in record_columns
        )
        if not assignments:
            continue

        result = conn.execute(
            text(
                f'UPDATE {target.qualified} AS t '
                f"SET {', '.join(assignments)} "
                f'FROM "public"."tb_fat_cidadao_pec" AS fcp, "public"."tb_cidadao" AS cid '
                f'WHERE fcp."co_seq_fat_cidadao_pec" = t."{fk}" '
                f'  AND cid."co_seq_cidadao" = fcp."co_cidadao" '
                f'  AND t."{target.cpf_column}" IS NULL '
                f'  AND t."{fk}" IS NOT NULL '
                f'  AND cid."dt_nascimento" IS NOT NULL'
            )
        )
        log.info(
            "%s: %d linha(s) adicional(is) corrigida(s) via FK limpa (CPF nulo na propria linha).",
            target.qualified,
            result.rowcount,
        )


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao de datas de nascimento e registros...")

    with engine.begin() as conn:
        # Reaponta as datas via tb_dim_tempo ANTES de deslocar dt_nascimento
        # abaixo: o delta e calculado a partir do nascimento ORIGINAL, e
        # recalcula-lo depois que dt_nascimento ja foi trocado daria delta
        # zero (a formula e deterministica: a mesma linha, com o mesmo dia
        # novo, "nao muda" em relacao a si mesma).
        log.info("reapontando datas de evento representadas so por tb_dim_tempo...")
        _run_dim_tempo_tables(conn)

        # Mesma exigencia de ordem: le o nascimento ORIGINAL de tb_cidadao
        # via join, antes do loop abaixo trocar esse valor.
        log.info("deslocando datas de atendimento sem cpf/nascimento na propria linha...")
        _run_joined_date_tables(conn)

        log.info("corrigindo linhas com cpf nulo na propria linha via FK limpa ate tb_cidadao...")
        _run_date_tables_fallback_fk(conn)

        log.info("deslocando datas de toda a familia de tabelas ligadas via co_atend_prof...")
        _run_atend_prof_family_tables(conn)

        log.info("deslocando datas de toda a familia de tabelas ligadas via co_prontuario...")
        _run_prontuario_family_tables(conn)

        log.info("deslocando datas de toda a familia de tabelas ligadas via co_fat_cidadao_pec...")
        _run_fat_cidadao_pec_family_tables(conn)

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

            # Com seed_fallback_column (ex: tb_cidadao/co_seq_cidadao), a
            # linha tem um identificador proprio sempre presente, entao nao
            # precisa exigir CPF: sem isso, todo cidadao com CPF nulo nunca
            # teria o proprio nascimento deslocado (nem teria fallback
            # possivel, por ser a tabela de origem do delta de todo o resto).
            if target.seed_fallback_column:
                cpf_guard = ""
            else:
                cpf_guard = (
                    f'  AND t."{target.cpf_column}" IS NOT NULL '
                    f'  AND btrim(t."{target.cpf_column}"::text) <> \'\''
                )
            result = conn.execute(
                text(
                    f'UPDATE "{target.schema}"."{target.table}" AS t '
                    f"SET {', '.join(assignments)} "
                    f'WHERE t."{target.birth_column}" IS NOT NULL '
                    f"{cpf_guard}"
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
