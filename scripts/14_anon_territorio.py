"""Migration 14 - Supressao de geografia fina: coordenada de visita e micro-area.

Fecha as duas representacoes de localizacao que sobreviviam a migration 06
por estarem em colunas que ela nao declara.

**Coordenada da visita domiciliar.** As tres tabelas de visita guardam
`nu_latitude`/`nu_longitude` capturados pelo aparelho do agente
comunitario no momento da visita - na porta da casa. Medido no banco real
antes de qualquer anonimizacao: 105.317 visitas geolocalizadas com 102.380
pontos distintos (praticamente um ponto por visita), mediana de 11 pontos
por cidadao, e dispersao mediana de 15,2 m em torno do centro robusto do
aglomerado. Isso e ruido de sensor, nao dispersao real: o centro estima a
residencia com erro da ordem de 5 m, contra uma testada de lote urbano de
10-12 m. Resultado: 4.813 cidadaos - 41% da base - com a casa localizavel
a menos de 50 m.

E a chave que liga visita a cidadao **sobrevive a anonimizacao**, porque a
substituicao de identificadores e deliberadamente consistente entre
tabelas (e o que da utilidade de pesquisa). Entao a troca de endereco da
migration 06 era contornavel por join, e para os 1.842 cidadaos que tem as
duas coisas a coordenada verdadeira permitia **inverter a propria troca**
(o endereco real e o mais proximo do centro do aglomerado).

**Micro-area.** O cadastro de cidadaos e domicilios e feito por agente
comunitario dentro de uma micro-area, que pertence a uma equipe. Com ~950
cidadaos por equipe e 2 a 4 agentes por equipe, chega-se a algo entre 22 e
44 micro-areas de ~240 a ~475 pessoas cada - provavelmente **mais fina que
o setor censitario**. Suprimir o endereco e deixar a micro-area de pe
repetiria o erro acima: anonimizar uma representacao da localizacao e
deixar outra, mais precisa, intacta em outra coluna.

`co_equipe`/`co_dim_equipe` continuam intocadas de proposito - sao chaves
substitutas opacas que preservam o vinculo sem revelar territorio, e o
identificador publico da equipe e tratado na migration 13.

**Fora de escopo de proposito.** `st_microarea_polo_base` (4 colunas,
`integer`) marca micro-area de polo base de saude indigena. Nao e
identificador geografico: e um marcador de origem etnica, portanto dado
pessoal **sensivel** pela LGPD, e pertence a analise de atributo sensivel
da fase 2 - nao a esta supressao de identificador. Tratar aqui seria
classificar errado.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("14_anon_territorio")


@dataclass(frozen=True)
class Column:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# Coordenada capturada na visita domiciliar - a residencia do cidadao em
# outro formato, com precisao de metros.
# ---------------------------------------------------------------------------
COORDINATE_COLUMNS: list[Column] = [
    Column("public", "tb_cds_visita_domiciliar", "nu_latitude"),
    Column("public", "tb_cds_visita_domiciliar", "nu_longitude"),
    Column("public", "tb_fat_visita_domiciliar", "nu_latitude"),
    Column("public", "tb_fat_visita_domiciliar", "nu_longitude"),
    Column("public", "tl_cds_visita_domiciliar", "nu_latitude"),
    Column("public", "tl_cds_visita_domiciliar", "nu_longitude"),
]

# ---------------------------------------------------------------------------
# 21 colunas de micro-area confirmadas por enumeracao do schema real.
# ---------------------------------------------------------------------------
MICRO_AREA_COLUMNS: list[Column] = [
    Column("public", "ta_cds_domicilio", "nu_micro_area"),
    Column("public", "ta_cidadao", "nu_micro_area"),
    Column("public", "tb_acomp_cidadaos_vinculados", "nu_micro_area_domicilio"),
    Column("public", "tb_acomp_cidadaos_vinculados", "nu_micro_area_tb_cidadao"),
    Column("public", "tb_cds_cad_domiciliar", "nu_micro_area"),
    Column("public", "tb_cds_cad_individual", "nu_micro_area"),
    Column("public", "tb_cds_domicilio", "nu_micro_area"),
    Column("public", "tb_cds_visita_domiciliar", "nu_micro_area"),
    Column("public", "tb_cidadao", "nu_micro_area"),
    Column("public", "tb_dim_agrupador_filtro", "nu_micro_area"),
    Column("public", "tb_fat_cad_dom_familia", "nu_micro_area"),
    Column("public", "tb_fat_cad_domiciliar", "nu_micro_area"),
    Column("public", "tb_fat_cad_individual", "nu_micro_area"),
    Column("public", "tb_fat_cidadao_territorio", "nu_micro_area"),
    Column("public", "tb_fat_familia_territorio", "nu_micro_area"),
    Column("public", "tb_fat_visita_domiciliar", "nu_micro_area"),
    Column("public", "tl_cds_cad_domiciliar", "nu_micro_area"),
    Column("public", "tl_cds_cad_individual", "nu_micro_area"),
    Column("public", "tl_cds_domicilio", "nu_micro_area"),
    Column("public", "tl_cds_visita_domiciliar", "nu_micro_area"),
    Column("public", "tl_cidadao", "nu_micro_area"),
]

# Usado quando a coluna e NOT NULL e de texto, e portanto nao aceita NULL.
GENERIC_TEXT = ""

TEXT_TYPES = {"character varying", "character", "text"}


def _column_info(conn: Connection, col: Column) -> tuple[bool, str] | None:
    """Retorna (nullable, data_type) ou None se a coluna nao existir."""
    row = conn.execute(
        text(
            """
            SELECT is_nullable, data_type
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"schema": col.schema, "table": col.table, "column": col.column},
    ).first()
    if row is None:
        return None
    return row[0] == "YES", row[1]


def _suppress(conn: Connection, columns: list[Column], rotulo: str) -> int:
    total = 0
    for col in columns:
        info = _column_info(conn, col)
        if info is None:
            log.warning("coluna inexistente, pulando: %s", col.qualified)
            continue
        nullable, data_type = info

        if nullable:
            new_value_sql = "NULL"
            params: dict[str, str] = {}
        elif data_type in TEXT_TYPES:
            new_value_sql = ":placeholder"
            params = {"placeholder": GENERIC_TEXT}
        else:
            # Coluna NOT NULL nao textual (ex.: coordenada `double precision`
            # obrigatoria). Zerar criaria uma coordenada ficticia plausivel
            # em vez de ausencia de dado, o que e pior que nao tratar -
            # entao para com aviso, para a auditoria sinalizar.
            log.warning(
                "coluna NOT NULL nao textual (%s), pulando sem suprimir: %s",
                data_type,
                col.qualified,
            )
            continue

        result = conn.execute(
            text(
                f'UPDATE "{col.schema}"."{col.table}" '
                f'SET "{col.column}" = {new_value_sql} '
                f'WHERE "{col.column}" IS NOT NULL'
            ),
            params,
        )
        log.info("%s: %d %s suprimido(s)", col.qualified, result.rowcount, rotulo)
        total += result.rowcount or 0
    return total


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando supressao de coordenada de visita e micro-area...")

    with engine.begin() as conn:
        coord_total = _suppress(conn, COORDINATE_COLUMNS, "coordenada(s)")
        micro_total = _suppress(conn, MICRO_AREA_COLUMNS, "micro-area(s)")
        log.info(
            "concluido: %d coordenada(s) e %d micro-area(s) suprimida(s), total=%d.",
            coord_total,
            micro_total,
            coord_total + micro_total,
        )
