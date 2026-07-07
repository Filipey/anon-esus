"""Migration 03 — Anonimização de e-mails de cidadãos.

Substitui todo e-mail de cidadão por um termo genérico único
(`cidadao@teste.br`). Diferente das migrations 01/02, não há mapeamento:
todos os e-mails viram a mesma constante.

Características:
- **Atômica**: roda inteira dentro de uma única transação; qualquer
  falha faz rollback e o banco permanece no estado original.

As colunas a anonimizar são declaradas explicitamente em `EMAIL_COLUMNS`.
Antes de aplicar, o script valida que cada coluna existe; entradas
inexistentes são puladas com aviso (não abortam a migration). Valores
nulos ou vazios são preservados.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("03_anon_email")


@dataclass(frozen=True)
class EmailColumn:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# Lista explícita de colunas que armazenam e-mail de cidadão.
#
# Pré-populada com colunas conhecidas do e-SUS APS/PEC. AJUSTE conforme o
# schema real da sua base. Colunas inexistentes são apenas puladas.
# ---------------------------------------------------------------------------
EMAIL_COLUMNS: list[EmailColumn] = [
    EmailColumn("public", "tb_cidadao", "no_email"),
    EmailColumn("public", "tb_pessoa_fisica", "no_email"),
]

# Termo genérico que substitui todos os e-mails.
GENERIC_EMAIL = "cidadao@teste.br"


def _column_exists(conn: Connection, col: EmailColumn) -> bool:
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
    """Executa a migration de forma atômica."""
    log.info("iniciando anonimização de e-mails (-> %s)...", GENERIC_EMAIL)

    with engine.begin() as conn:
        # 1) Resolve quais colunas realmente existem na base.
        targets = []
        for col in EMAIL_COLUMNS:
            if _column_exists(conn, col):
                log.debug("coluna-alvo encontrada: %s", col.qualified)
                targets.append(col)
            else:
                log.warning("coluna inexistente, pulando: %s", col.qualified)

        if not targets:
            log.info("nenhuma coluna de e-mail encontrada — nada a fazer.")
            return

        # 2) Substitui todos os e-mails não nulos/não vazios pela constante.
        total = 0
        for col in targets:
            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" '
                    f'SET "{col.column}" = :email '
                    f'WHERE "{col.column}" IS NOT NULL '
                    f"  AND btrim(\"{col.column}\"::text) <> ''"
                ),
                {"email": GENERIC_EMAIL},
            )
            log.info("%s: %d linha(s) atualizada(s)", col.qualified, result.rowcount)
            total += result.rowcount or 0

        log.info("concluído: %d e-mail(s) anonimizado(s).", total)
