"""Migration 07 - Exclusao de documentos e anexos.

Cobre a orientacao da guideline para "Documentos em PDF" e "Documentos
clinicos anexados em SOAP/Objetivo": o conteudo e o nome de arquivos
anexados sao excluidos (colocados em NULL).

Lista construida a partir da categoria "Documento/anexo" da auditoria real
do banco (`docs/auditoria_schema.md`), filtrada a mao: a categoria mistura
chave estrangeira (bigint, preserva vinculo - nao deve ser tocada), flags
de status, vocabulario de categoria de arquivo e numero de documento (que
nao e um "arquivo" e foi realocado para `11_anon_identificadores_diversos.py`).
Aqui ficam so as colunas que de fato guardam conteudo binario ou nome de
arquivo.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("07_anon_documentos")


@dataclass(frozen=True)
class DocumentColumn:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# Conteudo binario de arquivo anexado (bytea) e nome de arquivo (metadado
# que por si so pode identificar o documento/paciente). Colunas que sao so
# chave substituta (co_arquivo, co_seq_arquivo*) ou vocabulario de
# categoria (no_categoria_arquivo_atendprof) nao entram aqui de proposito.
# ---------------------------------------------------------------------------
DOCUMENT_COLUMNS: list[DocumentColumn] = [
    DocumentColumn("public", "tb_arquivo_temporario", "bl_arquivo"),
    DocumentColumn("public", "tb_assinatura_eletronica_atend", "bl_arquivo_assinado"),
    DocumentColumn("public", "ta_arquivo", "no_arquivo"),
    DocumentColumn("public", "tb_arquivo", "no_arquivo"),
    DocumentColumn("public", "tb_recebimento_item", "no_arquivo"),
    DocumentColumn("public", "tb_migracao_estrutura", "no_arquivo_migracao"),
]

# Placeholder usado quando a coluna e NOT NULL no banco real (ex.:
# `tb_arquivo.no_arquivo`) e por isso nao pode simplesmente virar NULL.
GENERIC_FILENAME = "arquivo_removido"


def _column_info(conn: Connection, col: DocumentColumn) -> tuple[bool, str] | None:
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


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando exclusao de documentos/anexos...")

    with engine.begin() as conn:
        total = 0
        for col in DOCUMENT_COLUMNS:
            info = _column_info(conn, col)
            if info is None:
                log.warning("coluna inexistente, pulando: %s", col.qualified)
                continue
            nullable, data_type = info

            if nullable:
                new_value_sql = "NULL"
            elif data_type == "bytea":
                new_value_sql = "''::bytea"
            else:
                new_value_sql = ":placeholder"

            params = {} if new_value_sql != ":placeholder" else {"placeholder": GENERIC_FILENAME}
            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" '
                    f'SET "{col.column}" = {new_value_sql} '
                    f'WHERE "{col.column}" IS NOT NULL'
                ),
                params,
            )
            log.info("%s: %d valor(es) excluido(s)", col.qualified, result.rowcount)
            total += result.rowcount or 0

        log.info("concluido: %d documento(s)/anexo(s) excluido(s).", total)
