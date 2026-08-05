"""Migration 12 - Exclusao de logs de acesso/auditoria e do IP.

Guideline: "Endereco IP das maquinas que acessaram: Sera excluido" e
"Logs de dados, incluindo data e hora dos acessos, relatorios que foram
visualizados: Serao excluidos".

Tabelas confirmadas por nome de tabela contra o schema real, nao por nome
de coluna - colunas de log tem nomes genericos (`dt_acesso`, `co_usuario`)
que so fazem sentido como log no contexto da tabela. `tl_acesso` foi
conferida e excluida de proposito - e controle de permissao (RBAC), nao
log de acesso.

A maioria das tabelas e removida por completo (`DELETE` - unico caso do
projeto que nao e `UPDATE`). `tb_auditoria_evento` e excecao confirmada:
existe uma FK de `tb_retificacao_atend.co_auditoria_evento_retificado`
apontando pra ela, com `NO ACTION` on delete - um `DELETE` quebraria a
integridade referencial. Em vez disso, todas as colunas exceto a chave
primaria sao zeradas, esvaziando o conteudo do log sem remover a linha.
Antes de deletar qualquer uma das outras tabelas, o script confere de novo
se apareceu alguma FK apontando pra ela (schema pode mudar) - se sim, pula
com aviso em vez de deletar.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("12_anon_ip_logs")


@dataclass(frozen=True)
class LogTable:
    schema: str
    table: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"'


# Tabelas removidas por completo. `tb_historico_acesso` guarda o IP
# (coluna `co_ip`) junto com o resto do log de acesso.
DELETE_TABLES: list[LogTable] = [
    LogTable("public", "tb_auditoria_processo"),
    LogTable("public", "tb_envio_log"),
    LogTable("public", "tb_historico_acesso"),
    LogTable("public", "tb_sessao_sincronizacao"),
    LogTable("public", "tb_ad_transmissao_sessao"),
]

# tb_auditoria_evento tem uma FK apontando pra ela
# (tb_retificacao_atend.co_auditoria_evento_retificado, NO ACTION on
# delete) - nao da pra deletar linha. Zera todas as colunas exceto a
# chave primaria.
SCRUB_SCHEMA = "public"
SCRUB_TABLE = "tb_auditoria_evento"
SCRUB_TABLE_PK = "co_seq_auditoria_evento"


def _table_exists(conn: Connection, schema: str, table: str) -> bool:
    found = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
            """
        ),
        {"schema": schema, "table": table},
    ).first()
    return found is not None


def _has_inbound_fk(conn: Connection, schema: str, table: str) -> bool:
    """True se alguma outra tabela tem FK apontando para esta."""
    found = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND ccu.table_schema = :schema
              AND ccu.table_name = :table
            """
        ),
        {"schema": schema, "table": table},
    ).first()
    return found is not None


def _columns_of(conn: Connection, schema: str, table: str) -> list[str]:
    rows = conn.execute(
        text(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table
            ORDER BY ordinal_position
            """
        ),
        {"schema": schema, "table": table},
    )
    return [r.column_name for r in rows]


def _delete_tables(conn: Connection) -> int:
    total = 0
    for t in DELETE_TABLES:
        if not _table_exists(conn, t.schema, t.table):
            log.warning("tabela inexistente, pulando: %s", t.qualified)
            continue
        if _has_inbound_fk(conn, t.schema, t.table):
            log.warning(
                "tabela tem FK apontando para ela (schema mudou?), pulando: %s", t.qualified
            )
            continue

        result = conn.execute(text(f'DELETE FROM "{t.schema}"."{t.table}"'))
        log.info("%s: %d linha(s) excluida(s)", t.qualified, result.rowcount)
        total += result.rowcount or 0
    return total


def _scrub_auditoria_evento(conn: Connection) -> int:
    if not _table_exists(conn, SCRUB_SCHEMA, SCRUB_TABLE):
        log.warning("tabela inexistente, pulando: %s.%s", SCRUB_SCHEMA, SCRUB_TABLE)
        return 0
    if not _column_exists(conn, SCRUB_SCHEMA, SCRUB_TABLE, SCRUB_TABLE_PK):
        log.warning(
            "chave primaria esperada ausente (%s), pulando esvaziamento de %s.%s",
            SCRUB_TABLE_PK,
            SCRUB_SCHEMA,
            SCRUB_TABLE,
        )
        return 0

    columns = _columns_of(conn, SCRUB_SCHEMA, SCRUB_TABLE)
    to_null = [c for c in columns if c != SCRUB_TABLE_PK]
    if not to_null:
        return 0

    assignments = ", ".join(f'"{c}" = NULL' for c in to_null)
    result = conn.execute(text(f'UPDATE "{SCRUB_SCHEMA}"."{SCRUB_TABLE}" SET {assignments}'))
    log.info(
        '"%s"."%s": %d linha(s) esvaziada(s) (%d coluna(s) zerada(s), preservando so "%s")',
        SCRUB_SCHEMA,
        SCRUB_TABLE,
        result.rowcount,
        len(to_null),
        SCRUB_TABLE_PK,
    )
    return result.rowcount or 0


def _column_exists(conn: Connection, schema: str, table: str, column: str) -> bool:
    found = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table AND column_name = :column
            """
        ),
        {"schema": schema, "table": table, "column": column},
    ).first()
    return found is not None


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando exclusao de logs de acesso/auditoria e IP...")

    with engine.begin() as conn:
        deleted_total = _delete_tables(conn)
        scrubbed_total = _scrub_auditoria_evento(conn)
        log.info(
            "concluido: %d linha(s) excluida(s), %d linha(s) esvaziada(s) em %s.",
            deleted_total,
            scrubbed_total,
            SCRUB_TABLE,
        )
