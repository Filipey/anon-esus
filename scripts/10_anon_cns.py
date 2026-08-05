"""Migration 10 - Anonimizacao provisoria do CNS (Cartao Nacional de Saude).

O CNS aparece em ~92 colunas do banco, quase sempre ao lado do CPF, mas a
guideline original nao definiu regra para ele - so fala de CPF. Diferente
do CPF, nao existe uma biblioteca pronta para gerar CNS ficticio e valido
(o digito verificador segue um algoritmo proprio). Decisao explicita: por
enquanto, tratar como o dado antropometrico (`08_anon_antropometrico.py`) -
hash deterministico salgado, sem se preocupar em gerar um CNS com formato
valido. Trocar por um gerador de CNS real fica para uma proxima fase.

`tb_fat_cad_domiciliar.nu_instituicao_cns` foi deixada de fora de proposito:
e o CNS de contato de uma instituicao, nao de uma pessoa.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("10_anon_cns")


@dataclass(frozen=True)
class CnsColumn:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# Colunas de CNS (cidadao, profissional, cuidador, responsavel) confirmadas
# na auditoria real do banco (categoria "CNS").
# ---------------------------------------------------------------------------
CNS_COLUMNS: list[CnsColumn] = [
    CnsColumn("public", "ta_ativ_col_cidadao_particip", "nu_cns"),
    CnsColumn("public", "ta_cds_domicilio", "nu_cns"),
    CnsColumn("public", "ta_cds_domicilio", "nu_cns_responsavel_tecnico"),
    CnsColumn("public", "ta_cidadao", "nu_cns"),
    CnsColumn("public", "ta_cidadao", "nu_cns_cuidador"),
    CnsColumn("public", "ta_cidadao", "nu_cns_responsavel"),
    CnsColumn("public", "ta_cidadao_grupo", "nu_cns"),
    CnsColumn("public", "ta_cidadao_unificacao_base", "nu_cns"),
    CnsColumn("public", "ta_prof", "nu_cns"),
    CnsColumn("public", "ta_prof_historico_cns", "nu_cns"),
    CnsColumn("public", "tb_acomp_cidadaos_vinculados", "nu_cns_cidadao"),
    CnsColumn("public", "tb_atend_prof_ad", "nu_cns_cuidador"),
    CnsColumn("public", "tb_ativ_col_cidadao_particip", "nu_cns"),
    CnsColumn("public", "tb_cds_aval_elegibilidade", "nu_cns_cidadao"),
    CnsColumn("public", "tb_cds_aval_elegibilidade", "nu_cns_cuidador"),
    CnsColumn("public", "tb_cds_cad_domiciliar", "nu_cns_responsavel_tecnico"),
    CnsColumn("public", "tb_cds_cad_individual", "nu_cns_cidadao"),
    CnsColumn("public", "tb_cds_domicilio", "nu_cns"),
    CnsColumn("public", "tb_cds_domicilio", "nu_cns_responsavel_tecnico"),
    CnsColumn("public", "tb_cds_ficha_consumo_alimentar", "nu_cns_cidadao"),
    CnsColumn("public", "tb_cds_ficha_zika_microcefalia", "nu_cns_cidadao"),
    CnsColumn("public", "tb_cds_ficha_zika_microcefalia", "nu_cns_responsavel_familiar"),
    CnsColumn("public", "tb_cds_prof", "nu_cns"),
    CnsColumn("public", "tb_cidadao", "nu_cns"),
    CnsColumn("public", "tb_cidadao", "nu_cns_cuidador"),
    CnsColumn("public", "tb_cidadao", "nu_cns_responsavel"),
    CnsColumn("public", "tb_cidadao_grupo", "nu_cns"),
    CnsColumn("public", "tb_cidadao_grupo_ativ_col", "nu_cns"),
    CnsColumn("public", "tb_cidadao_nucleo_familiar", "nu_cns_profissional"),
    CnsColumn("public", "tb_cidadao_unificacao_base", "nu_cns"),
    CnsColumn("public", "tb_dim_profissional", "nu_cns"),
    CnsColumn("public", "tb_envio_rnds", "nu_cns_prof"),
    CnsColumn("public", "tb_fat_atd_ind_encaminhamentos", "nu_cns_cidadao"),
    CnsColumn("public", "tb_fat_atd_ind_exames", "nu_cns_cidadao"),
    CnsColumn("public", "tb_fat_atd_ind_medicamentos", "nu_cns_cidadao"),
    CnsColumn("public", "tb_fat_atd_ind_problemas", "nu_cns"),
    CnsColumn("public", "tb_fat_atd_ind_procedimentos", "nu_cns"),
    CnsColumn("public", "tb_fat_atend_odonto_encaminham", "nu_cns_cidadao"),
    CnsColumn("public", "tb_fat_atend_odonto_exames", "nu_cns_cidadao"),
    CnsColumn("public", "tb_fat_atend_odonto_medicament", "nu_cns_cidadao"),
    CnsColumn("public", "tb_fat_atend_odonto_problemas", "nu_cns"),
    CnsColumn("public", "tb_fat_atend_odonto_proced", "nu_cns"),
    CnsColumn("public", "tb_fat_atendimento_domiciliar", "nu_cns"),
    CnsColumn("public", "tb_fat_atendimento_individual", "nu_cns"),
    CnsColumn("public", "tb_fat_atendimento_odonto", "nu_cns"),
    CnsColumn("public", "tb_fat_atvdd_coletiva_part", "nu_participante_cns"),
    CnsColumn("public", "tb_fat_avaliacao_elegibilidade", "nu_cns"),
    CnsColumn("public", "tb_fat_avaliacao_elegibilidade", "nu_cns_cuidador"),
    CnsColumn("public", "tb_fat_cad_dom_familia", "nu_cns_responsavel"),
    CnsColumn("public", "tb_fat_cad_individual", "nu_cns"),
    CnsColumn("public", "tb_fat_cad_individual", "nu_cns_responsavel"),
    CnsColumn("public", "tb_fat_cidadao", "nu_cns"),
    CnsColumn("public", "tb_fat_cidadao_pec", "nu_cns"),
    CnsColumn("public", "tb_fat_complementar", "nu_cns"),
    CnsColumn("public", "tb_fat_complementar", "nu_cns_responsavel"),
    CnsColumn("public", "tb_fat_cuidado_compartilhado", "nu_cns_cidadao"),
    CnsColumn("public", "tb_fat_familia", "nu_cns_responsavel"),
    CnsColumn("public", "tb_fat_ivcf", "nu_cns_cidadao"),
    CnsColumn("public", "tb_fat_marca_consumo_alimnt", "nu_cns"),
    CnsColumn("public", "tb_fat_proced_atend", "nu_cns"),
    CnsColumn("public", "tb_fat_proced_atend_proced", "nu_cns"),
    CnsColumn("public", "tb_fat_solicitacao_oci", "nu_cns_cidadao"),
    CnsColumn("public", "tb_fat_vacinacao", "nu_cns"),
    CnsColumn("public", "tb_fat_visita_domiciliar", "nu_cns"),
    CnsColumn("public", "tb_historico_cabecalho", "nu_cns_prof"),
    CnsColumn("public", "tb_historico_dados_fai", "nu_cns_finalizador_obs"),
    CnsColumn("public", "tb_historico_dados_fcc", "nu_cns_executante"),
    CnsColumn("public", "tb_historico_dados_fcc", "nu_cns_solicitante"),
    CnsColumn("public", "tb_prof", "nu_cns"),
    CnsColumn("public", "tb_prof_grupo_ativ_col", "nu_cns"),
    CnsColumn("public", "tb_prof_historico_cns", "nu_cns"),
    CnsColumn("public", "tb_revisao", "nu_cns"),
    CnsColumn("public", "tl_atend_prof_ad", "nu_cns_cuidador"),
    CnsColumn("public", "tl_cds_aval_elegibilidade", "nu_cns_cidadao"),
    CnsColumn("public", "tl_cds_aval_elegibilidade", "nu_cns_cuidador"),
    CnsColumn("public", "tl_cds_cad_domiciliar", "nu_cns_responsavel_tecnico"),
    CnsColumn("public", "tl_cds_cad_individual", "nu_cns_cidadao"),
    CnsColumn("public", "tl_cds_domicilio", "nu_cns_responsavel_tecnico"),
    CnsColumn("public", "tl_cds_ficha_consumo_alimentar", "nu_cns_cidadao"),
    CnsColumn("public", "tl_cds_ficha_zika_microcefalia", "nu_cns_cidadao"),
    CnsColumn("public", "tl_cds_ficha_zika_microcefalia", "nu_cns_responsavel_familiar"),
    CnsColumn("public", "tl_cds_prof", "nu_cns"),
    CnsColumn("public", "tl_cidadao", "nu_cns"),
    CnsColumn("public", "tl_cidadao", "nu_cns_cuidador"),
    CnsColumn("public", "tl_cidadao", "nu_cns_responsavel"),
    CnsColumn("public", "tl_cidadao_grupo", "nu_cns"),
    CnsColumn("public", "tl_cidadao_grupo_ativ_col", "nu_cns"),
    CnsColumn("public", "tl_cidadao_nucleo_familiar", "nu_cns_profissional"),
    CnsColumn("public", "tl_cns", "nu_cns"),
    CnsColumn("public", "tl_prof", "nu_cns"),
    CnsColumn("public", "tl_prof_grupo_ativ_col", "nu_cns"),
]

# Sal fixo do projeto - nao e segredo, so evita expor md5(valor) cru. Mesma
# ressalva de 08_anon_antropometrico.py: nao e protecao real contra forca
# bruta se o espaco de valores for pequeno (nao e o caso do CNS, que tem
# 15 digitos).
ANON_SALT = "anon-esus-cns-v1"

NUMERIC_TYPES = {"numeric", "double precision", "real", "integer", "bigint", "smallint"}
TEXT_TYPES = {"character varying", "character", "text"}
NUMERIC_HASH_MODULUS = 30_000


def _column_info(conn: Connection, col: CnsColumn) -> tuple[str, int | None] | None:
    row = conn.execute(
        text(
            """
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"schema": col.schema, "table": col.table, "column": col.column},
    ).first()
    return (row.data_type, row.character_maximum_length) if row else None


def _hash_expr(column_ref: str, data_type: str, max_length: int | None) -> str | None:
    salted = f"({column_ref}::text || '{ANON_SALT}')"
    if data_type in TEXT_TYPES:
        # CNS tem 15 digitos - o hash mira esse tamanho, mas nunca deve
        # estourar o limite real da coluna (character(N)/varchar(N)).
        length = 15 if max_length is None else min(15, max_length)
        return f"substr(md5({salted}), 1, {length})"
    if data_type in NUMERIC_TYPES:
        seed = f"(('x' || substr(md5({salted}), 1, 8))::bit(32)::bigint)"
        return f"({seed} % {NUMERIC_HASH_MODULUS})"
    return None


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao provisoria (hash) de CNS...")

    with engine.begin() as conn:
        total = 0
        for col in CNS_COLUMNS:
            info = _column_info(conn, col)
            if info is None:
                log.warning("coluna inexistente, pulando: %s", col.qualified)
                continue
            data_type, max_length = info

            expr = _hash_expr(f't."{col.column}"', data_type, max_length)
            if expr is None:
                log.warning(
                    "tipo de dado nao tratado (%s), pulando: %s", data_type, col.qualified
                )
                continue

            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" AS t '
                    f'SET "{col.column}" = {expr} '
                    f'WHERE t."{col.column}" IS NOT NULL '
                    f"  AND btrim(t.\"{col.column}\"::text) <> ''"
                )
            )
            log.info("%s: %d valor(es) substituido(s) por hash", col.qualified, result.rowcount)
            total += result.rowcount or 0

        log.info("concluido: %d valor(es) de CNS hasheado(s).", total)
