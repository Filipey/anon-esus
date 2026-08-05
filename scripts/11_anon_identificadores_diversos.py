"""Migration 11 - Identificadores diversos sem categoria propria na guideline.

Consolida seis categorias pequenas que a auditoria real do banco encontrou
mas a guideline original nao definiu explicitamente: prontuario, telefone,
NIS, naturalizacao, numero de documento de obito e identificacao mista
(campo que mistura CPF/CNS num so valor). Cada uma usa o tratamento mais
proximo ja em uso no projeto:

- Prontuario, NIS, naturalizacao (numero) e obito (numero): hash
  deterministico salgado, mesmo mecanismo de `08_anon_antropometrico.py` e
  `10_anon_cns.py`.
- Telefone: numero ficticio via Faker, mapa deterministico por valor
  (mesmo padrao de `05_anon_profissional.py`/`09_anon_nome_cidadao.py`).
  Inclui telefone de unidade/DSEI/polo - diferente do e-mail
  institucional, um telefone ficticio nao "rotula" a unidade como
  cidadao, entao nao precisa de um placeholder separado.
- Naturalizacao (data): mantem so o ano, zera dia e mes.
- Identificacao mista (CPF/CNS no mesmo campo): detecta o formato pelo
  numero de digitos (11 -> trata como CPF, 15 -> trata como CNS) e aplica
  hash do tamanho correspondente. Sem garantia de gerar o mesmo valor
  ficticio ja usado em `01_anon_cpf.py`/`10_anon_cns.py` para a mesma
  pessoa - simplificacao aceita para a fase 1.

Colunas puramente estruturais (chave substituta bigint, flag de status,
texto livre de antecedente familiar) foram deixadas de fora de proposito -
nao sao o dado que a categoria da auditoria buscava, so bateram no
heuristico por nome (ex.: "NIS" em "administracao", "obito" em texto de
antecedente).
"""

from __future__ import annotations

from dataclasses import dataclass

from faker import Faker
from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("11_anon_identificadores_diversos")


@dataclass(frozen=True)
class Column:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# Prontuario: so as 33 colunas `character varying` da categoria "Prontuario"
# da auditoria. As outras ~124 (chave bigint, flag de status) preservam
# vinculo e nao entram aqui.
# ---------------------------------------------------------------------------
PRONTUARIO_COLUMNS: list[Column] = [
    Column("public", "rl_cds_prontuario_unidade_saud", "nu_prontuario_interno"),
    Column("public", "ta_cidadao", "co_unico_cidadao_prontuario"),
    Column("public", "ta_cidadao", "co_unico_prontuario"),
    Column("public", "ta_prontuario_unidade_saude", "nu_prontuario"),
    Column("public", "tb_cds_atend_individual", "nu_prontuario"),
    Column("public", "tb_cds_atend_odonto", "nu_prontuario"),
    Column("public", "tb_cds_aval_elegibilidade", "nu_prontuario"),
    Column("public", "tb_cds_domicilio_familia", "nu_prontuario"),
    Column("public", "tb_cds_proced", "nu_prontuario"),
    Column("public", "tb_cds_vacinacao", "nu_prontuario"),
    Column("public", "tb_cds_visita_domiciliar", "nu_prontuario"),
    Column("public", "tb_familia", "nu_prontuario_familiar"),
    Column("public", "tb_fat_atendimento_individual", "nu_prontuario"),
    Column("public", "tb_fat_atendimento_odonto", "nu_prontuario"),
    Column("public", "tb_fat_cad_dom_familia", "nu_prontuario"),
    Column("public", "tb_fat_familia_territorio", "nu_prontuario"),
    Column("public", "tb_fat_proced_atend", "nu_prontuario"),
    Column("public", "tb_fat_vacinacao", "nu_prontuario"),
    Column("public", "tb_fat_visita_domiciliar", "nu_prontuario"),
    Column("public", "tb_prontuario_unidade_saude", "nu_prontuario"),
    Column("public", "tl_cds_atend_individual", "nu_prontuario"),
    Column("public", "tl_cds_atend_odonto", "nu_prontuario"),
    Column("public", "tl_cds_aval_elegibilidade", "nu_prontuario"),
    Column("public", "tl_cds_domicilio_familia", "nu_prontuario"),
    Column("public", "tl_cds_proced", "nu_prontuario"),
    Column("public", "tl_cds_vacinacao", "nu_prontuario"),
    Column("public", "tl_cds_visita_domiciliar", "nu_prontuario"),
    Column("public", "tl_cidadao", "co_unico_cidadao_prontuario"),
    Column("public", "tl_cidadao", "co_unico_prontuario"),
    Column("public", "tl_familia", "nu_prontuario_familiar"),
    Column("public", "tl_prontuario", "co_unico_cidadao_prontuario"),
    Column("public", "tl_prontuario", "co_unico_prontuario"),
    Column("public", "tl_prontuario_unidade_saude", "nu_prontuario"),
]

# ---------------------------------------------------------------------------
# Telefone: cidadao, profissional e unidade/DSEI/polo base.
# ---------------------------------------------------------------------------
PHONE_COLUMNS: list[Column] = [
    Column("public", "ta_agend_compartilhado", "nu_telefone_prof_participante"),
    Column("public", "ta_cds_domicilio", "nu_fone_referencia"),
    Column("public", "ta_cds_domicilio", "nu_fone_residencia"),
    Column("public", "ta_cidadao", "nu_telefone_celular"),
    Column("public", "ta_cidadao", "nu_telefone_contato"),
    Column("public", "ta_cidadao", "nu_telefone_residencial"),
    Column("public", "ta_prof", "nu_telefone"),
    Column("public", "ta_unidade_saude", "nu_telefone_comercial"),
    Column("public", "ta_unidade_saude", "nu_telefone_comercial2"),
    Column("public", "ta_unidade_saude", "nu_telefone_fax"),
    Column("public", "tb_acomp_cidadaos_vinculados", "nu_fone_residencial"),
    Column("public", "tb_acomp_cidadaos_vinculados", "nu_telefone_celular"),
    Column("public", "tb_acomp_cidadaos_vinculados", "nu_telefone_contato"),
    Column("public", "tb_cds_aval_elegibilidade", "nu_fone_referencia"),
    Column("public", "tb_cds_aval_elegibilidade", "nu_fone_residencia"),
    Column("public", "tb_cds_cad_domiciliar", "nu_fone_referencia"),
    Column("public", "tb_cds_cad_domiciliar", "nu_fone_residencia"),
    Column("public", "tb_cds_cad_domiciliar", "nu_fone_responsavel_tecnico"),
    Column("public", "tb_cds_cad_individual", "nu_celular_cidadao"),
    Column("public", "tb_cds_domicilio", "nu_fone_referencia"),
    Column("public", "tb_cds_domicilio", "nu_fone_residencia"),
    Column("public", "tb_cidadao", "nu_telefone_celular"),
    Column("public", "tb_cidadao", "nu_telefone_contato"),
    Column("public", "tb_cidadao", "nu_telefone_residencial"),
    Column("public", "tb_dado_recebido_info_instalac", "nu_telefone"),
    Column("public", "tb_dsei", "nu_telefone1"),
    Column("public", "tb_dsei", "nu_telefone2"),
    Column("public", "tb_fat_avaliacao_elegibilidade", "nu_telefone_contato"),
    Column("public", "tb_fat_avaliacao_elegibilidade", "nu_telefone_residencia"),
    Column("public", "tb_fat_cad_domiciliar", "nu_instituicao_telefone"),
    Column("public", "tb_fat_cad_domiciliar", "nu_telefone_contato"),
    Column("public", "tb_fat_cad_domiciliar", "nu_telefone_residencia"),
    Column("public", "tb_fat_cad_individual", "nu_celular"),
    Column("public", "tb_fat_cidadao_pec", "nu_telefone_celular"),
    Column("public", "tb_polo_base", "nu_telefone1"),
    Column("public", "tb_polo_base", "nu_telefone2"),
    Column("public", "tb_prof", "nu_telefone"),
    Column("public", "tb_unidade_saude", "nu_telefone_comercial"),
    Column("public", "tb_unidade_saude", "nu_telefone_comercial2"),
    Column("public", "tb_unidade_saude", "nu_telefone_fax"),
    Column("public", "tl_cds_aval_elegibilidade", "nu_fone_referencia"),
    Column("public", "tl_cds_aval_elegibilidade", "nu_fone_residencia"),
    Column("public", "tl_cds_cad_domiciliar", "nu_fone_referencia"),
    Column("public", "tl_cds_cad_domiciliar", "nu_fone_residencia"),
    Column("public", "tl_cds_cad_domiciliar", "nu_fone_responsavel_tecnico"),
    Column("public", "tl_cds_cad_individual", "nu_celular_cidadao"),
    Column("public", "tl_cds_domicilio", "nu_fone_referencia"),
    Column("public", "tl_cds_domicilio", "nu_fone_residencia"),
    Column("public", "tl_cidadao", "nu_telefone_celular"),
    Column("public", "tl_cidadao", "nu_telefone_contato"),
    Column("public", "tl_cidadao", "nu_telefone_residencial"),
    Column("public", "tl_prof", "nu_telefone"),
    Column("public", "tl_unidade_saude", "nu_telefone_comercial"),
    Column("public", "tl_unidade_saude", "nu_telefone_comercial2"),
    Column("public", "tl_unidade_saude", "nu_telefone_fax"),
]

# ---------------------------------------------------------------------------
# NIS/PIS/PASEP real (exclui os 4 falsos-positivos de "via_administracao"
# que bateram a substring "nis" no heuristico da auditoria).
# ---------------------------------------------------------------------------
NIS_COLUMNS: list[Column] = [
    Column("public", "ta_cidadao", "nu_nis_pis_pasep"),
    Column("public", "tb_cds_aval_elegibilidade", "nu_nis_pis_pasep"),
    Column("public", "tb_cidadao", "nu_nis_pis_pasep"),
    Column("public", "tb_fat_avaliacao_elegibilidade", "nu_nis"),
    Column("public", "tb_fat_cad_individual", "nu_nis"),
    Column("public", "tl_cds_aval_elegibilidade", "nu_nis_pis_pasep"),
    Column("public", "tl_cidadao", "nu_nis_pis_pasep"),
]

# ---------------------------------------------------------------------------
# Naturalizacao: numero da portaria (hash) e data (so preserva o ano).
# ---------------------------------------------------------------------------
NATURALIZACAO_NUMBER_COLUMNS: list[Column] = [
    Column("public", "ta_cidadao", "nu_portaria_naturalizacao"),
    Column("public", "tb_cds_aval_elegibilidade", "ds_portaria_naturalizacao"),
    Column("public", "tb_cds_cad_individual", "ds_portaria_naturalizacao"),
    Column("public", "tb_cidadao", "nu_portaria_naturalizacao"),
    Column("public", "tb_fat_avaliacao_elegibilidade", "nu_portaria_naturalizacao"),
    Column("public", "tb_fat_cad_individual", "nu_portaria_naturalizacao"),
    Column("public", "tl_cds_aval_elegibilidade", "ds_portaria_naturalizacao"),
    Column("public", "tl_cds_cad_individual", "ds_portaria_naturalizacao"),
    Column("public", "tl_cidadao", "nu_portaria_naturalizacao"),
]

NATURALIZACAO_DATE_COLUMNS: list[Column] = [
    Column("public", "ta_cidadao", "dt_naturalizacao"),
    Column("public", "tb_cds_aval_elegibilidade", "dt_naturalizacao"),
    Column("public", "tb_cds_cad_individual", "dt_naturalizacao"),
    Column("public", "tb_cidadao", "dt_naturalizacao"),
    Column("public", "tb_fat_avaliacao_elegibilidade", "dt_naturalizacao"),
    Column("public", "tb_fat_cad_individual", "dt_naturalizacao"),
    Column("public", "tl_cds_aval_elegibilidade", "dt_naturalizacao"),
    Column("public", "tl_cds_cad_individual", "dt_naturalizacao"),
    Column("public", "tl_cidadao", "dt_naturalizacao"),
]

# ---------------------------------------------------------------------------
# Obito/DO: so o numero do documento (character varying). `dt_obito`/
# `dt_reg_obito` ficam para a migration 04 (se a tabela tiver nu_cpf +
# dt_nascimento); `co_unico_ad_cidadao_obito` e bigint (chave substituta,
# nao toca); os campos `ds_obito_*` sao texto livre, fora da fase 1.
# ---------------------------------------------------------------------------
OBITO_COLUMNS: list[Column] = [
    Column("public", "tb_cds_cad_individual", "nu_declaracao_obito"),
    Column("public", "tl_cds_cad_individual", "nu_declaracao_obito"),
    Column("public", "tb_fat_cad_individual", "nu_obito_do"),
]

# ---------------------------------------------------------------------------
# Identificacao mista: campo unico que pode guardar CPF ou CNS. Exclui as
# 4 colunas `ds_cpf_cnpj` de credencial/sistema externo (identidade de
# sistema, nao de pessoa).
# ---------------------------------------------------------------------------
MIXED_ID_COLUMNS: list[Column] = [
    Column("public", "tb_cidadao_nucleo_familiar", "nu_cpf_cns_responsavel"),
    Column("public", "tb_familia", "nu_cpf_cns_responsavel"),
    Column("public", "tb_historico_cabecalho", "nu_cpf_cns_cidadao"),
    Column("public", "tb_historico_dados_exames", "nu_cpf_cns_cidadao"),
    Column("public", "tb_historico_dados_fad", "nu_cpf_cns_cidadao"),
    Column("public", "tb_historico_dados_fai", "nu_cpf_cns_cidadao"),
    Column("public", "tb_historico_dados_fao", "nu_cpf_cns_cidadao"),
    Column("public", "tb_historico_dados_fcc", "nu_cpf_cns_cidadao"),
    Column("public", "tb_historico_dados_proced", "nu_cpf_cns_cidadao"),
    Column("public", "tb_historico_dados_vacina", "nu_cpf_cns_cidadao"),
    Column("public", "tl_cidadao_nucleo_familiar", "nu_cpf_cns_responsavel"),
    Column("public", "tl_familia", "nu_cpf_cns_responsavel"),
]

ANON_SALT = "anon-esus-identificadores-v1"
FAKER_LOCALE = "pt_BR"
FAKER_SEED = 20260803

TEXT_TYPES = {"character varying", "character", "text"}


def _column_exists(conn: Connection, col: Column) -> bool:
    return _column_info(conn, col) is not None


def _column_info(conn: Connection, col: Column) -> tuple[str, int | None] | None:
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


def _hash_columns(conn: Connection, columns: list[Column], desired_length: int) -> int:
    """Hash deterministico salgado, respeitando o tamanho real da coluna."""
    total = 0
    for col in columns:
        info = _column_info(conn, col)
        if info is None:
            log.warning("coluna inexistente, pulando: %s", col.qualified)
            continue
        data_type, max_length = info
        if data_type not in TEXT_TYPES:
            log.warning("tipo de dado nao tratado (%s), pulando: %s", data_type, col.qualified)
            continue
        length = desired_length if max_length is None else min(desired_length, max_length)
        expr = f"substr(md5(t.\"{col.column}\"::text || '{ANON_SALT}'), 1, {length})"

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
    return total


def _fake_phone(index: int) -> str:
    fake = Faker(FAKER_LOCALE)
    fake.seed_instance(FAKER_SEED + index)
    return fake.numerify("###########")


def _collect_raw_values(conn: Connection, col: Column) -> set[str]:
    rows = conn.execute(
        text(
            f'SELECT DISTINCT "{col.column}" AS v '
            f'FROM "{col.schema}"."{col.table}" '
            f'WHERE "{col.column}" IS NOT NULL '
            f"  AND btrim(\"{col.column}\"::text) <> ''"
        )
    )
    return {str(r.v) for r in rows}


def _anon_phones(conn: Connection) -> int:
    targets = [col for col in PHONE_COLUMNS if _column_exists(conn, col)]
    for col in PHONE_COLUMNS:
        if col not in targets:
            log.warning("coluna inexistente, pulando: %s", col.qualified)

    values: set[str] = set()
    for col in targets:
        values |= _collect_raw_values(conn, col)

    if not values:
        return 0

    value_to_fake = {value: _fake_phone(i) for i, value in enumerate(sorted(values))}
    conn.execute(
        text(
            "CREATE TEMP TABLE _telefone_map "
            "(old_value text PRIMARY KEY, new_value text NOT NULL) "
            "ON COMMIT DROP"
        )
    )
    conn.execute(
        text("INSERT INTO _telefone_map (old_value, new_value) VALUES (:old, :new)"),
        [{"old": old, "new": new} for old, new in value_to_fake.items()],
    )

    total = 0
    for col in targets:
        result = conn.execute(
            text(
                f'UPDATE "{col.schema}"."{col.table}" AS t '
                f'SET "{col.column}" = m.new_value '
                f"FROM _telefone_map m "
                f'WHERE t."{col.column}"::text = m.old_value'
            )
        )
        log.info("%s: %d telefone(s) atualizado(s)", col.qualified, result.rowcount)
        total += result.rowcount or 0
    return total


def _anon_naturalizacao_dates(conn: Connection) -> int:
    total = 0
    for col in NATURALIZACAO_DATE_COLUMNS:
        info = _column_info(conn, col)
        if info is None:
            log.warning("coluna inexistente, pulando: %s", col.qualified)
            continue
        data_type, _ = info
        year_expr = f'extract(year from t."{col.column}")::int'
        jan_first = f"make_date({year_expr}, 1, 1)"
        new_value = jan_first if data_type == "date" else f"{jan_first}::timestamp"

        result = conn.execute(
            text(
                f'UPDATE "{col.schema}"."{col.table}" AS t '
                f'SET "{col.column}" = {new_value} '
                f'WHERE t."{col.column}" IS NOT NULL'
            )
        )
        log.info(
            "%s: %d data(s) reduzida(s) a 1o de janeiro do ano", col.qualified, result.rowcount
        )
        total += result.rowcount or 0
    return total


def _anon_mixed_ids(conn: Connection) -> int:
    total = 0
    for col in MIXED_ID_COLUMNS:
        if not _column_exists(conn, col):
            log.warning("coluna inexistente, pulando: %s", col.qualified)
            continue

        digits = f"regexp_replace(t.\"{col.column}\"::text, '\\D', '', 'g')"
        salted = f"(t.\"{col.column}\"::text || '{ANON_SALT}')"
        expr = (
            "CASE "
            f"WHEN length({digits}) = 11 THEN substr(md5({salted}), 1, 11) "
            f"WHEN length({digits}) = 15 THEN substr(md5({salted}), 1, 15) "
            f"ELSE substr(md5({salted}), 1, 15) "
            "END"
        )
        result = conn.execute(
            text(
                f'UPDATE "{col.schema}"."{col.table}" AS t '
                f'SET "{col.column}" = {expr} '
                f'WHERE t."{col.column}" IS NOT NULL '
                f"  AND btrim(t.\"{col.column}\"::text) <> ''"
            )
        )
        log.info("%s: %d valor(es) substituido(s)", col.qualified, result.rowcount)
        total += result.rowcount or 0
    return total


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao de identificadores diversos...")

    with engine.begin() as conn:
        prontuario_total = _hash_columns(conn, PRONTUARIO_COLUMNS, desired_length=20)
        telefone_total = _anon_phones(conn)
        nis_total = _hash_columns(conn, NIS_COLUMNS, desired_length=11)
        naturalizacao_numero_total = _hash_columns(
            conn, NATURALIZACAO_NUMBER_COLUMNS, desired_length=20
        )
        naturalizacao_data_total = _anon_naturalizacao_dates(conn)
        obito_total = _hash_columns(conn, OBITO_COLUMNS, desired_length=20)
        mixed_id_total = _anon_mixed_ids(conn)

        log.info(
            "concluido: prontuario=%d, telefone=%d, nis=%d, "
            "naturalizacao(numero)=%d, naturalizacao(data)=%d, obito=%d, "
            "identificacao_mista=%d, total=%d",
            prontuario_total,
            telefone_total,
            nis_total,
            naturalizacao_numero_total,
            naturalizacao_data_total,
            obito_total,
            mixed_id_total,
            prontuario_total
            + telefone_total
            + nis_total
            + naturalizacao_numero_total
            + naturalizacao_data_total
            + obito_total
            + mixed_id_total,
        )
