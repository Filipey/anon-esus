"""Migration 08 - Anonimizacao provisoria de dados antropometricos.

Guideline final (microagregacao/truncamento/differential privacy) ainda nao
foi definida. Como medida provisoria, esta migration substitui o valor de
cada campo antropometrico por um hash deterministico do valor original.

Por serem campos numericos de baixa cardinalidade (poucos milhares de
valores plausiveis para peso/altura/perimetro), um hash - mesmo com sal -
nao impede um ataque de forca bruta que pre-calcule o hash de todo o range
plausivel. Isto NAO substitui o DP planejado; e so uma medida de contencao
enquanto o DP nao entra.

Lista de colunas confirmada contra o schema fisico real
(`docs/auditoria_schema.md`, categoria "Antropometria"). A versao anterior,
baseada so na documentacao do DW, tinha dois nomes de coluna errados
(`nu_medicao_circ_abdominal`/`nu_medicao_perim_pantrlha` - os nomes reais
sao `nu_circ_abdominal`/`nu_perim_panturrilha`) e nao cobria a tabela
`ta_medicao`/`tb_medicao`/`tl_medicao`, que concentra os sinais vitais de
cada atendimento.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("08_anon_antropometrico")


@dataclass(frozen=True)
class AnthroColumn:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# Colunas antropometricas (peso, altura, perimetro cefalico, circunferencia
# abdominal, perimetro de panturrilha, IMC, altura uterina).
# ---------------------------------------------------------------------------
ANTHRO_COLUMNS: list[AnthroColumn] = [
    AnthroColumn("public", "tb_fat_atendimento_individual", "nu_circ_abdominal"),
    AnthroColumn("public", "tb_fat_atendimento_individual", "nu_perim_panturrilha"),
    AnthroColumn("public", "tb_fat_atendimento_individual", "nu_peso"),
    AnthroColumn("public", "tb_fat_atendimento_individual", "nu_altura"),
    AnthroColumn("public", "tb_fat_atendimento_individual", "nu_perimetro_cefalico"),
    AnthroColumn("public", "tb_fat_atendimento_odonto", "nu_peso"),
    AnthroColumn("public", "tb_fat_atendimento_odonto", "nu_altura"),
    AnthroColumn("public", "tb_fat_atendimento_odonto", "nu_circ_abdominal"),
    AnthroColumn("public", "tb_fat_atendimento_odonto", "nu_perim_panturrilha"),
    AnthroColumn("public", "tb_fat_proced_atend", "nu_circ_abdominal"),
    AnthroColumn("public", "tb_fat_proced_atend", "nu_perim_panturrilha"),
    AnthroColumn("public", "tb_fat_proced_atend", "nu_peso"),
    AnthroColumn("public", "tb_fat_proced_atend", "nu_altura"),
    AnthroColumn("public", "tb_fat_proced_atend", "nu_perimetro_cefalico"),
    AnthroColumn("public", "tb_fat_consolidado_cidadao_fai", "nu_altura"),
    AnthroColumn("public", "tb_fat_consolidado_cidadao_fai", "nu_peso"),
    AnthroColumn("public", "tb_fat_consolidado_cidadao_fai", "nu_perimetro_cefalico_prcltra"),
    AnthroColumn("public", "tb_fat_consolidado_cidadao_fai", "nu_altura_prcltra"),
    AnthroColumn("public", "tb_fat_consolidado_cidadao_fai", "nu_peso_prcltra"),
    # ta_/tb_/tl_medicao concentram os sinais vitais/antropometria de cada
    # atendimento - descobertos so na auditoria contra o schema real, nao
    # apareciam na documentacao do DW.
    AnthroColumn("public", "ta_medicao", "nu_medicao_peso"),
    AnthroColumn("public", "ta_medicao", "nu_medicao_altura"),
    AnthroColumn("public", "ta_medicao", "nu_medicao_perimetro_cefalico"),
    AnthroColumn("public", "ta_medicao", "nu_medicao_circunf_abdominal"),
    AnthroColumn("public", "ta_medicao", "nu_perimetro_panturrilha"),
    AnthroColumn("public", "ta_medicao", "nu_medicao_imc"),
    AnthroColumn("public", "ta_medicao", "nu_medicao_altura_uterina"),
    AnthroColumn("public", "tb_medicao", "nu_medicao_peso"),
    AnthroColumn("public", "tb_medicao", "nu_medicao_altura"),
    AnthroColumn("public", "tb_medicao", "nu_medicao_perimetro_cefalico"),
    AnthroColumn("public", "tb_medicao", "nu_medicao_circunf_abdominal"),
    AnthroColumn("public", "tb_medicao", "nu_perimetro_panturrilha"),
    AnthroColumn("public", "tb_medicao", "nu_medicao_imc"),
    AnthroColumn("public", "tb_medicao", "nu_medicao_altura_uterina"),
    AnthroColumn("public", "tl_medicao", "nu_medicao_peso"),
    AnthroColumn("public", "tl_medicao", "nu_medicao_altura"),
    AnthroColumn("public", "tl_medicao", "nu_medicao_perimetro_cefalico"),
    AnthroColumn("public", "tl_medicao", "nu_medicao_circunf_abdominal"),
    AnthroColumn("public", "tl_medicao", "nu_perimetro_panturrilha"),
    AnthroColumn("public", "tl_medicao", "nu_medicao_imc"),
    AnthroColumn("public", "tl_medicao", "nu_medicao_altura_uterina"),
]

# Sal fixo do projeto. Nao e segredo (fica no codigo-fonte) - serve so para
# nao expor o hash "cru" de md5(valor), nao para resistir a forca bruta.
ANON_SALT = "anon-esus-antropometrico-v1"

NUMERIC_TYPES = {"numeric", "double precision", "real", "integer", "bigint", "smallint"}
TEXT_TYPES = {"character varying", "character", "text"}

# Cabe com folga em smallint (max 32767), mantendo o mesmo range para
# qualquer um dos NUMERIC_TYPES.
NUMERIC_HASH_MODULUS = 30_000


def _column_info(
    conn: Connection, col: AnthroColumn
) -> tuple[str, int | None, int | None, int | None] | None:
    row = conn.execute(
        text(
            """
            SELECT data_type, character_maximum_length, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"schema": col.schema, "table": col.table, "column": col.column},
    ).first()
    return (
        (row.data_type, row.character_maximum_length, row.numeric_precision, row.numeric_scale)
        if row
        else None
    )


def _numeric_modulus(precision: int | None, scale: int | None) -> int:
    """Maior modulo que cabe na coluna sem estourar `numeric(precision, scale)`.

    Ex.: `numeric(3, 1)` aceita valores com so 2 digitos antes da virgula
    (< 100) - usar o modulo padrao (30000) estouraria a coluna. Tipos sem
    precisao declarada (bigint, double precision, numeric sem parametros,
    ...) usam o modulo padrao, que ja cabe com folga em smallint (32767).
    """
    if precision is None:
        return NUMERIC_HASH_MODULUS
    digits_before_point = max(1, precision - (scale or 0))
    max_exclusive = 10**digits_before_point
    return min(NUMERIC_HASH_MODULUS, max_exclusive)


def _hash_expr(
    column_ref: str,
    data_type: str,
    max_length: int | None,
    numeric_precision: int | None,
    numeric_scale: int | None,
) -> str | None:
    salted = f"({column_ref}::text || '{ANON_SALT}')"
    if data_type in NUMERIC_TYPES:
        seed = f"(('x' || substr(md5({salted}), 1, 8))::bit(32)::bigint)"
        modulus = _numeric_modulus(numeric_precision, numeric_scale)
        return f"({seed} % {modulus})"
    if data_type in TEXT_TYPES:
        # Nunca estoura o limite real da coluna (character(N)/varchar(N)).
        length = 16 if max_length is None else min(16, max_length)
        return f"substr(md5({salted}), 1, {length})"
    return None


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao provisoria (hash) de dados antropometricos...")

    with engine.begin() as conn:
        total = 0
        for col in ANTHRO_COLUMNS:
            info = _column_info(conn, col)
            if info is None:
                log.warning("coluna inexistente, pulando: %s", col.qualified)
                continue
            data_type, max_length, numeric_precision, numeric_scale = info

            expr = _hash_expr(
                f't."{col.column}"', data_type, max_length, numeric_precision, numeric_scale
            )
            if expr is None:
                log.warning(
                    "tipo de dado nao tratado (%s), pulando: %s", data_type, col.qualified
                )
                continue

            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" AS t '
                    f'SET "{col.column}" = {expr} '
                    f'WHERE t."{col.column}" IS NOT NULL'
                )
            )
            log.info("%s: %d valor(es) substituido(s) por hash", col.qualified, result.rowcount)
            total += result.rowcount or 0

        log.info("concluido: %d valor(es) antropometrico(s) hasheado(s).", total)
