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


def _column_exists(conn: Connection, col: DocumentColumn) -> bool:
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
        {"schema": col.schema, "table": col.table, "column": col.column},
    ).first()
    return found is not None


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando exclusao de documentos/anexos...")

    with engine.begin() as conn:
        total = 0
        for col in DOCUMENT_COLUMNS:
            if not _column_exists(conn, col):
                log.warning("coluna inexistente, pulando: %s", col.qualified)
                continue

            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" '
                    f'SET "{col.column}" = NULL '
                    f'WHERE "{col.column}" IS NOT NULL'
                )
            )
            log.info("%s: %d valor(es) excluido(s)", col.qualified, result.rowcount)
            total += result.rowcount or 0

        log.info("concluido: %d documento(s)/anexo(s) excluido(s).", total)
