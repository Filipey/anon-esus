"""Migration 01 — Anonimização de CPFs.

Substitui todos os CPFs reais da base por CPFs aleatórios e válidos.

Características:
- **Atômica**: roda inteira dentro de uma única transação. Qualquer
  falha faz rollback e o banco permanece no estado original.
- **Determinística**: o mesmo CPF original é sempre mapeado para o mesmo
  CPF falso em todas as colunas, preservando vínculos entre tabelas.
- **Preserva o formato**: se o valor armazenado tinha pontuação
  (`000.000.000-00`) ou zeros à esquerda, o CPF falso é gravado no mesmo
  formato.

As colunas a anonimizar são declaradas explicitamente em `CPF_COLUMNS`.
Antes de aplicar, o script valida que cada coluna existe; entradas
inexistentes são puladas com aviso (não abortam a migration).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from cpf_generator import CPF
from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("01_anon_cpf")


@dataclass(frozen=True)
class CpfColumn:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# Lista explícita de colunas que armazenam CPF.
#
# Pré-populada com colunas conhecidas do e-SUS APS/PEC. AJUSTE conforme o
# schema real da sua base. Colunas inexistentes são apenas puladas.
# ---------------------------------------------------------------------------
CPF_COLUMNS: list[CpfColumn] = [
    CpfColumn("public", "tb_cidadao", "nu_cpf"),
    CpfColumn("public", "tb_cidadao", "nu_cpf_responsavel"),
    CpfColumn("public", "tb_prof", "nu_cpf"),
    CpfColumn("public", "tb_pessoa_fisica", "nu_cpf"),
]


_NON_DIGITS = re.compile(r"\D")


def _normalize(raw: str) -> str:
    """Reduz um CPF ao seu núcleo de 11 dígitos (sem pontuação/zeros perdidos)."""
    return _NON_DIGITS.sub("", raw).zfill(11)


def _apply_format(template: str, fake_digits: str) -> str:
    """Formata `fake_digits` (11 dígitos) imitando o `template` original."""
    if "." in template or "-" in template:
        return CPF.format(fake_digits)
    # mantém o mesmo comprimento do valor original (preserva zeros à esquerda)
    return fake_digits.zfill(len(_NON_DIGITS.sub("", template)) or 11)


def _generate_unique(used: set[str]) -> str:
    """Gera um CPF válido de 11 dígitos ainda não utilizado."""
    while True:
        candidate = CPF.generate()
        if candidate not in used:
            used.add(candidate)
            return candidate


def _column_exists(conn: Connection, col: CpfColumn) -> bool:
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


def _collect_raw_values(conn: Connection, col: CpfColumn) -> set[str]:
    rows = conn.execute(
        text(
            f'SELECT DISTINCT "{col.column}" AS v '
            f'FROM "{col.schema}"."{col.table}" '
            f'WHERE "{col.column}" IS NOT NULL '
            f"  AND btrim(\"{col.column}\"::text) <> ''"
        )
    )
    return {str(r.v) for r in rows}


def run(engine: Engine) -> None:
    """Executa a migration de forma atômica."""
    log.info("iniciando anonimização de CPFs...")

    with engine.begin() as conn:
        # 1) Resolve quais colunas realmente existem na base.
        targets = []
        for col in CPF_COLUMNS:
            if _column_exists(conn, col):
                log.debug("coluna-alvo encontrada: %s", col.qualified)
                targets.append(col)
            else:
                log.warning("coluna inexistente, pulando: %s", col.qualified)

        if not targets:
            log.info("nenhuma coluna de CPF encontrada — nada a fazer.")
            return

        # 2) Coleta todos os valores brutos distintos de todas as colunas.
        raw_values: set[str] = set()
        for col in targets:
            valores = _collect_raw_values(conn, col)
            log.debug("%s: %d valor(es) distinto(s) coletado(s)", col.qualified, len(valores))
            raw_values |= valores

        if not raw_values:
            log.info("nenhum CPF a anonimizar.")
            return

        # 3) Mapeamento determinístico:
        #    norma (11 dígitos) -> CPF falso (11 dígitos), 1:1 e único.
        norm_to_fake: dict[str, str] = {}
        used_fakes: set[str] = set()
        for raw in raw_values:
            norm = _normalize(raw)
            if norm not in norm_to_fake:
                norm_to_fake[norm] = _generate_unique(used_fakes)

        #    valor bruto -> CPF falso já formatado como o original.
        raw_to_fake = {
            raw: _apply_format(raw, norm_to_fake[_normalize(raw)])
            for raw in raw_values
        }
        log.info(
            "%d valor(es) bruto(s) -> %d CPF(s) distinto(s) a anonimizar",
            len(raw_to_fake),
            len(norm_to_fake),
        )

        # 4) Tabela temporária de mapeamento + UPDATE por join (rápido e atômico).
        conn.execute(
            text(
                "CREATE TEMP TABLE _cpf_map "
                "(old_cpf text PRIMARY KEY, new_cpf text NOT NULL) "
                "ON COMMIT DROP"
            )
        )
        conn.execute(
            text("INSERT INTO _cpf_map (old_cpf, new_cpf) VALUES (:old, :new)"),
            [{"old": old, "new": new} for old, new in raw_to_fake.items()],
        )

        total = 0
        for col in targets:
            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" AS t '
                    f"SET \"{col.column}\" = m.new_cpf "
                    f'FROM _cpf_map m '
                    f"WHERE t.\"{col.column}\"::text = m.old_cpf"
                )
            )
            log.info("%s: %d linha(s) atualizada(s)", col.qualified, result.rowcount)
            total += result.rowcount or 0

        log.info(
            "concluído: %d CPF(s) distinto(s) anonimizado(s), %d linha(s) atualizada(s).",
            len(norm_to_fake),
            total,
        )
