"""Migration 03 — Anonimização de e-mails.

Substitui e-mail de cidadão/profissional por um termo genérico único
(`cidadao@teste.br`) e e-mail institucional (unidade de saúde, DSEI, polo
base) por outro termo genérico (`unidade@teste.br`) - são categorias
diferentes e não deveriam compartilhar o mesmo placeholder (um contato
institucional rotulado como "cidadao@..." é uma inconsistência, não uma
anonimização). Diferente das migrations 01/02, não há mapeamento por
valor: todos os e-mails de uma categoria viram a mesma constante.

Características:
- **Atômica**: roda inteira dentro de uma única transação; qualquer
  falha faz rollback e o banco permanece no estado original.

As colunas a anonimizar são declaradas explicitamente em
`PERSONAL_EMAIL_COLUMNS` e `INSTITUTIONAL_EMAIL_COLUMNS`. Antes de
aplicar, o script valida que cada coluna existe; entradas inexistentes são
puladas com aviso (não abortam a migration). Valores nulos ou vazios são
preservados.

Colunas deixadas de fora de propósito: `ta_credencial_integracao.ds_email`,
`ta_servidor_smtp.ds_email`, `ta_sistema_externo.ds_email` e
`tb_dado_recebido_info_instalac.ds_email` (e pares `tb_`/`tl_`) são
configuração de infraestrutura (SMTP, integração de sistemas), não dado
pessoal nem institucional de saúde - não devem ser tocadas.
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
# E-mail de cidadão e de profissional de saúde.
# ---------------------------------------------------------------------------
PERSONAL_EMAIL_COLUMNS: list[EmailColumn] = [
    EmailColumn("public", "ta_agend_compartilhado", "ds_email_prof_participante"),
    EmailColumn("public", "ta_cidadao", "ds_email"),
    EmailColumn("public", "ta_prof", "ds_email"),
    EmailColumn("public", "tb_cds_aval_elegibilidade", "ds_email_cidadao"),
    EmailColumn("public", "tb_cds_cad_individual", "ds_email_cidadao"),
    EmailColumn("public", "tb_cidadao", "ds_email"),
    EmailColumn("public", "tb_fat_avaliacao_elegibilidade", "no_email"),
    EmailColumn("public", "tb_fat_cad_individual", "no_email"),
    EmailColumn("public", "tb_prof", "ds_email"),
    EmailColumn("public", "tl_cds_aval_elegibilidade", "ds_email_cidadao"),
    EmailColumn("public", "tl_cds_cad_individual", "ds_email_cidadao"),
    EmailColumn("public", "tl_cidadao", "ds_email"),
    EmailColumn("public", "tl_prof", "ds_email"),
]

# ---------------------------------------------------------------------------
# E-mail institucional: unidade de saúde, DSEI, polo base (inclui contato
# de "chefe" - é o e-mail do cargo/instituição, não o e-mail pessoal do
# cidadão).
# ---------------------------------------------------------------------------
INSTITUTIONAL_EMAIL_COLUMNS: list[EmailColumn] = [
    EmailColumn("public", "ta_unidade_saude", "ds_email"),
    EmailColumn("public", "tb_dsei", "ds_email"),
    EmailColumn("public", "tb_dsei", "ds_email_chefe"),
    EmailColumn("public", "tb_polo_base", "ds_email"),
    EmailColumn("public", "tb_polo_base", "ds_email_chefe"),
    EmailColumn("public", "tb_unidade_saude", "ds_email"),
    EmailColumn("public", "tl_unidade_saude", "ds_email"),
]

GENERIC_EMAIL = "cidadao@teste.br"
GENERIC_INSTITUTIONAL_EMAIL = "unidade@teste.br"


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


def _anon_emails(conn: Connection, columns: list[EmailColumn], generic_value: str) -> int:
    targets = [col for col in columns if _column_exists(conn, col)]
    for col in columns:
        if col not in targets:
            log.warning("coluna inexistente, pulando: %s", col.qualified)

    total = 0
    for col in targets:
        result = conn.execute(
            text(
                f'UPDATE "{col.schema}"."{col.table}" '
                f'SET "{col.column}" = :email '
                f'WHERE "{col.column}" IS NOT NULL '
                f"  AND btrim(\"{col.column}\"::text) <> ''"
            ),
            {"email": generic_value},
        )
        log.info("%s: %d linha(s) atualizada(s)", col.qualified, result.rowcount)
        total += result.rowcount or 0
    return total


def run(engine: Engine) -> None:
    """Executa a migration de forma atômica."""
    log.info(
        "iniciando anonimização de e-mails (pessoal -> %s, institucional -> %s)...",
        GENERIC_EMAIL,
        GENERIC_INSTITUTIONAL_EMAIL,
    )

    with engine.begin() as conn:
        personal_total = _anon_emails(conn, PERSONAL_EMAIL_COLUMNS, GENERIC_EMAIL)
        institutional_total = _anon_emails(
            conn, INSTITUTIONAL_EMAIL_COLUMNS, GENERIC_INSTITUTIONAL_EMAIL
        )
        log.info(
            "concluído: %d e-mail(s) pessoal(is) e %d institucional(is) anonimizado(s).",
            personal_total,
            institutional_total,
        )
