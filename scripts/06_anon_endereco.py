"""Migration 06 - Anonimizacao de enderecos de cidadaos.

Substitui o endereco por outro endereco existente na propria base, dentro do
mesmo municipio. A troca acontece como um conjunto completo de campos
(logradouro, numero, bairro, complemento, referencia, CEP), evitando montar
enderecos artificiais por combinacao de partes de enderecos diferentes.

Se a tabela nao tiver uma coluna de municipio reconhecida, ela e pulada com
aviso. Isso evita violar a regra de manter a substituicao no mesmo municipio.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("06_anon_endereco")


@dataclass(frozen=True)
class AddressTable:
    schema: str
    table: str
    address_columns: tuple[str, ...]
    municipality_columns: tuple[str, ...]

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"'


DEFAULT_MUNICIPALITY_COLUMNS = (
    "co_dim_municipio",
    "co_dim_municipio_residencia",
    "co_dim_municipio_domicilio",
    "co_dim_municipio_cidadao",
    "co_localidade_endereco",
    "co_localidade_residencia",
    "co_localidade",
    "co_municipio",
    "co_municipio_residencia",
    "co_municipio_domicilio",
    "co_ibge",
    "co_ibge_municipio",
)

ADDRESS_TABLES: list[AddressTable] = [
    AddressTable(
        "public",
        "ta_cds_domicilio",
        (
            "ds_cep",
            "ds_complemento",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
            "no_logradouro",
            "no_logradouro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "ta_cidadao",
        (
            "ds_cep",
            "ds_complemento",
            "ds_logradouro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "ta_prof",
        (
            "ds_cep",
            "ds_complemento",
            "ds_logradouro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "ta_unidade_saude",
        (
            "ds_cep",
            "ds_complemento",
            "ds_logradouro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tb_cds_cad_domiciliar",
        (
            "ds_complemento",
            "ds_complemento_filtro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_logradouro",
            "no_logradouro_filtro",
            "nu_cep",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tb_cds_domicilio",
        (
            "ds_cep",
            "ds_complemento",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
            "no_logradouro",
            "no_logradouro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tb_cidadao",
        (
            "ds_cep",
            "ds_complemento",
            "ds_logradouro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tb_dsei",
        (
            "ds_complemento",
            "no_bairro",
            "no_logradouro",
            "nu_cep",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tb_fat_cad_domiciliar",
        (
            "no_bairro",
            "no_complemento",
            "no_logradouro",
            "no_ponto_referencia",
            "nu_cep",
            "nu_num_logradouro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tb_fat_avaliacao_elegibilidade",
        (
            "no_bairro_residencia",
            "no_complemento_residencia",
            "no_logradouro_residencia",
            "nu_cep_residencia",
            "nu_num_logradouro_residencia",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tb_polo_base",
        (
            "ds_complemento",
            "no_bairro",
            "no_logradouro",
            "nu_cep",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tb_prof",
        (
            "ds_cep",
            "ds_complemento",
            "ds_logradouro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tb_unidade_saude",
        (
            "ds_cep",
            "ds_complemento",
            "ds_logradouro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tl_cds_cad_domiciliar",
        (
            "ds_complemento",
            "ds_complemento_filtro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_logradouro",
            "no_logradouro_filtro",
            "nu_cep",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tl_cds_domicilio",
        (
            "ds_cep",
            "ds_complemento",
            "ds_ponto_referencia",
            "no_bairro",
            "no_logradouro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tl_cidadao",
        (
            "ds_cep",
            "ds_complemento",
            "ds_logradouro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tl_prof",
        (
            "ds_cep",
            "ds_complemento",
            "ds_logradouro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
    AddressTable(
        "public",
        "tl_unidade_saude",
        (
            "ds_cep",
            "ds_complemento",
            "ds_logradouro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
        ),
        DEFAULT_MUNICIPALITY_COLUMNS,
    ),
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


def _first_existing_municipality_column(conn: Connection, target: AddressTable) -> str | None:
    for column in target.municipality_columns:
        if _column_exists(conn, target.schema, target.table, column):
            return column
    return None


def _has_any_address_value(target_alias: str, columns: tuple[str, ...]) -> str:
    return " OR ".join(
        f'({target_alias}."{column}" IS NOT NULL AND btrim({target_alias}."{column}"::text) <> \'\')'
        for column in columns
    )


def _null_safe_distinct(left_alias: str, right_alias: str, columns: tuple[str, ...]) -> str:
    return " OR ".join(
        f'{left_alias}."{column}" IS DISTINCT FROM {right_alias}."{column}"'
        for column in columns
    )


def _anon_table(conn: Connection, target: AddressTable) -> int:
    missing_address_columns = [
        column
        for column in target.address_columns
        if not _column_exists(conn, target.schema, target.table, column)
    ]
    if missing_address_columns:
        log.warning(
            "coluna(s) de endereco ausente(s), pulando %s: %s",
            target.qualified,
            ", ".join(missing_address_columns),
        )
        return 0

    municipality_column = _first_existing_municipality_column(conn, target)
    if municipality_column is None:
        log.warning(
            "nenhuma coluna de municipio reconhecida, pulando %s",
            target.qualified,
        )
        return 0

    address_select = ", ".join(f'"{column}"' for column in target.address_columns)
    partition_columns = ", ".join(f'"{column}"' for column in target.address_columns)
    assignments = ", ".join(
        f'"{column}" = chosen."{column}"'
        for column in target.address_columns
    )
    has_value = _has_any_address_value("t", target.address_columns)
    candidate_has_value = _has_any_address_value("src", target.address_columns)
    distinct_from_original = _null_safe_distinct("t", "chosen", target.address_columns)

    result = conn.execute(
        text(
            f"""
            WITH candidates AS (
                SELECT
                    "{municipality_column}" AS municipality,
                    {address_select},
                    row_number() OVER (
                        PARTITION BY "{municipality_column}"
                        ORDER BY {partition_columns}
                    ) AS candidate_idx,
                    count(*) OVER (
                        PARTITION BY "{municipality_column}"
                    ) AS candidate_count
                FROM (
                    SELECT DISTINCT
                        "{municipality_column}",
                        {address_select}
                    FROM "{target.schema}"."{target.table}" AS src
                    WHERE src."{municipality_column}" IS NOT NULL
                      AND ({candidate_has_value})
                ) AS src
            ),
            picked AS (
                SELECT
                    t.ctid AS row_ctid,
                    t."{municipality_column}" AS municipality,
                    c.candidate_idx,
                    c.candidate_count,
                    CASE
                        WHEN c.candidate_count <= 1 THEN c.candidate_idx
                        ELSE (((
                            ('x' || substr(md5(t.ctid::text), 1, 8))::bit(32)::bigint
                        ) % (c.candidate_count - 1)) + 1)::int
                    END AS offset_idx
                FROM "{target.schema}"."{target.table}" AS t
                JOIN candidates AS c
                  ON c.municipality = t."{municipality_column}"
                 AND { " AND ".join(f'c."{column}" IS NOT DISTINCT FROM t."{column}"' for column in target.address_columns) }
                WHERE t."{municipality_column}" IS NOT NULL
                  AND ({has_value})
            ),
            chosen_rows AS (
                SELECT
                    p.row_ctid,
                    chosen.*
                FROM picked AS p
                JOIN candidates AS chosen
                  ON chosen.municipality = p.municipality
                 AND chosen.candidate_idx = (
                      ((p.candidate_idx - 1 + p.offset_idx) % p.candidate_count) + 1
                 )
            )
            UPDATE "{target.schema}"."{target.table}" AS t
            SET {assignments}
            FROM chosen_rows AS chosen
            WHERE t.ctid = chosen.row_ctid
              AND ({distinct_from_original})
            """
        )
    )
    log.info(
        "%s: %d endereco(s) substituido(s) usando municipio %s",
        target.qualified,
        result.rowcount,
        municipality_column,
    )
    return result.rowcount or 0


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao de enderecos...")

    with engine.begin() as conn:
        total = 0
        for target in ADDRESS_TABLES:
            total += _anon_table(conn, target)
        log.info("concluido: %d endereco(s) anonimizado(s).", total)
