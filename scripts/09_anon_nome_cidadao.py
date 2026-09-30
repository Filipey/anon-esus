"""Migration 09 - Anonimizacao do nome do cidadao.

A guideline original define regra de nome ficticio para profissional e
denominacao generica para unidade de saude, mas nao menciona o nome do
proprio cidadao. Substitui por nome completo ficticio comum todo nome de
cidadao (proprio, mae, pai, social, responsavel, cuidador) em texto claro.

Cobertura: a primeira versao desta migration so tratava as colunas
`no_nome*` do DW e de atividade coletiva (11 colunas). A tabela mestra do
cidadao (`tb_cidadao` e as copias `ta_`/`tl_`), o cadastro individual CDS,
o `tb_fat_cidadao_pec`, o Bolsa Familia e o cache de acompanhamento ficavam
com o nome real - mais de um milhao de celulas, achado no levantamento de
texto livre da fase 2 (set/2026). A lista abaixo vem de uma varredura do
schema real por `no_cidadao%`, `no_mae%`, `no_pai%`, `no_social%`,
`no_responsavel%`, `no_cuidador%` e `no_nome%`.

Consistencia: o mapa nome real -> ficticio e unico para todas as colunas, e
a chave e o nome normalizado (sem acento, minusculo, espaco simples). Assim
"MARIA DA SILVA" em `tb_cidadao` e "Maria da Silva" no cadastro individual
viram o mesmo nome ficticio, e a mae registrada como cidada recebe o mesmo
nome ficticio no `no_mae` dos filhos. O ficticio sai no mesmo estilo de
caixa do original (tudo maiusculo, tudo minusculo ou normal).

Colunas de busca (`*_filtro`): o PEC guarda uma copia normalizada do nome
para pesquisa - `nome social + nome` (ou so o nome), minusculo e sem acento.
Elas sao recalculadas a partir dos nomes ja trocados (`FILTER_COLUMNS`), senao
continuariam guardando o nome real e a busca por nome deixaria de funcionar.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from faker import Faker
from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("09_anon_nome_cidadao")


@dataclass(frozen=True)
class NameColumn:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


@dataclass(frozen=True)
class FilterColumn:
    """`column` = normalizar(' '.join(parts nao vazias)), recalculada depois
    da troca dos nomes."""

    schema: str
    table: str
    column: str
    parts: tuple[str, ...]

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


def _cols(table: str, *columns: str) -> list[NameColumn]:
    return [NameColumn("public", table, c) for c in columns]


_CIDADAO = ("no_cidadao", "no_mae", "no_pai", "no_social", "no_responsavel", "no_cuidador")
_CAD_INDIVIDUAL = ("no_cidadao", "no_mae_cidadao", "no_pai_cidadao", "no_social_cidadao")

# ---------------------------------------------------------------------------
# Colunas de nome de cidadao (proprio, mae, pai, social, responsavel,
# cuidador) confirmadas no schema real. Colunas inexistentes sao puladas.
# ---------------------------------------------------------------------------
NAME_COLUMNS: list[NameColumn] = [
    *_cols("ta_ativ_col_cidadao_particip", "no_nome"),
    *_cols("tb_ativ_col_cidadao_particip", "no_nome"),
    *_cols("tb_fat_avaliacao_elegibilidade", "no_nome", "no_nome_mae", "no_nome_pai", "no_nome_social"),
    *_cols("tb_fat_cad_individual", "no_nome", "no_nome_mae", "no_nome_pai", "no_nome_social"),
    *_cols("tb_fat_marca_consumo_alimnt", "no_nome"),
    # tabela mestra do cidadao e copias de auditoria/revisao
    *_cols("tb_cidadao", *_CIDADAO),
    *_cols("ta_cidadao", *_CIDADAO),
    *_cols("tl_cidadao", *_CIDADAO),
    # cadastro individual e avaliacao de elegibilidade (CDS)
    *_cols("tb_cds_cad_individual", *_CAD_INDIVIDUAL),
    *_cols("tl_cds_cad_individual", *_CAD_INDIVIDUAL),
    *_cols("tb_cds_aval_elegibilidade", *_CAD_INDIVIDUAL),
    *_cols("tl_cds_aval_elegibilidade", *_CAD_INDIVIDUAL),
    # demais
    *_cols("tb_fat_cidadao_pec", "no_cidadao", "no_social_cidadao"),
    *_cols("tb_cidadao_bolsa_familia", "no_cidadao"),
    *_cols("tb_acomp_cidadaos_vinculados", "no_cidadao", "no_social_cidadao", "no_responsavel"),
    *_cols("tb_cds_ficha_consumo_alimentar", "no_identificacao_cidadao"),
    *_cols("tl_cds_ficha_consumo_alimentar", "no_identificacao_cidadao"),
    *_cols("tb_cidadao_grupo_ativ_col", "no_cidadao_grupo"),
    *_cols("tl_cidadao_grupo_ativ_col", "no_cidadao_grupo"),
    *_cols("tb_cidadao_aldeado", "no_responsavel_legal"),
    *_cols("ta_cidadao_aldeado", "no_responsavel_legal"),
    *_cols("tb_fat_cidadao_aldeado", "no_responsavel_legal"),
    *_cols("tb_atend_prof_ad", "no_cuidador"),
    *_cols("tl_atend_prof_ad", "no_cuidador"),
]

# Ordem das partes = a observada no banco real (nome social antes do nome).
FILTER_COLUMNS: list[FilterColumn] = [
    *[
        FilterColumn("public", t, "no_cidadao_filtro", ("no_social", "no_cidadao"))
        for t in ("tb_cidadao", "ta_cidadao", "tl_cidadao")
    ],
    *[
        FilterColumn("public", t, "no_mae_filtro", ("no_mae",))
        for t in ("tb_cidadao", "ta_cidadao", "tl_cidadao")
    ],
    FilterColumn("public", "tl_cidadao", "no_pai_filtro", ("no_pai",)),
    *[
        FilterColumn("public", t, "no_cidadao_filtro", ("no_social_cidadao", "no_cidadao"))
        for t in ("tb_cds_cad_individual", "tl_cds_cad_individual")
    ],
]

FAKER_LOCALE = "pt_BR"
FAKER_SEED = 20260803

_ESPACOS = re.compile(r"\s+")


def normalizar(nome: str) -> str:
    """Sem acento, minusculo, espaco simples — e a forma das colunas
    `*_filtro` e a chave do mapa de nomes."""
    sem_acento = "".join(
        ch for ch in unicodedata.normalize("NFD", nome) if unicodedata.category(ch) != "Mn"
    )
    return _ESPACOS.sub(" ", sem_acento).strip().lower()


def _mesma_caixa(ficticio: str, original: str) -> str:
    letras = [ch for ch in original if ch.isalpha()]
    if letras and all(ch.isupper() for ch in letras):
        return ficticio.upper()
    if letras and all(ch.islower() for ch in letras):
        return ficticio.lower()
    return ficticio


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


def _collect_raw_values(conn: Connection, col: NameColumn) -> set[str]:
    rows = conn.execute(
        text(
            f'SELECT DISTINCT "{col.column}" AS v '
            f'FROM "{col.schema}"."{col.table}" '
            f'WHERE "{col.column}" IS NOT NULL '
            f"  AND btrim(\"{col.column}\"::text) <> ''"
        )
    )
    return {str(r.v) for r in rows}


def _fake_name(index: int) -> str:
    fake = Faker(FAKER_LOCALE)
    fake.seed_instance(FAKER_SEED + index)
    return fake.name()


def build_name_map(names: set[str]) -> dict[str, str]:
    """valor bruto -> nome ficticio. Grafias que normalizam igual recebem o
    mesmo ficticio; a ordem e o indice vem das chaves normalizadas ordenadas,
    entao o resultado e reprodutivel."""
    chaves = sorted({normalizar(n) for n in names} - {""})
    ficticio = {chave: _fake_name(i) for i, chave in enumerate(chaves)}
    return {
        n: _mesma_caixa(ficticio[normalizar(n)], n)
        for n in names
        if normalizar(n)
    }


def _recompute_filter(conn: Connection, col: FilterColumn) -> int:
    parts = [p for p in col.parts if _column_exists(conn, col.schema, col.table, p)]
    if not parts:
        log.warning("nenhuma coluna-fonte de %s existe; pulando.", col.qualified)
        return 0
    sel = ", ".join(f't."{p}"' for p in parts)
    combos = conn.execute(
        text(
            f'SELECT DISTINCT {sel} FROM "{col.schema}"."{col.table}" AS t '
            f'WHERE t."{col.column}" IS NOT NULL'
        )
    ).all()
    if not combos:
        return 0
    conn.execute(
        text(
            "CREATE TEMP TABLE _filtro_map ("
            + ", ".join(f"p{i} text" for i in range(len(parts)))
            + ", novo text NOT NULL) ON COMMIT DROP"
        )
    )
    linhas = []
    for combo in combos:
        valores = [None if v is None else str(v) for v in combo]
        novo = normalizar(" ".join(v for v in valores if v and v.strip()))
        linhas.append({**{f"p{i}": v for i, v in enumerate(valores)}, "novo": novo})
    conn.execute(
        text(
            "INSERT INTO _filtro_map ("
            + ", ".join(f"p{i}" for i in range(len(parts)))
            + ", novo) VALUES ("
            + ", ".join(f":p{i}" for i in range(len(parts)))
            + ", :novo)"
        ),
        linhas,
    )
    cond = " AND ".join(
        f't."{p}"::text IS NOT DISTINCT FROM m.p{i}' for i, p in enumerate(parts)
    )
    result = conn.execute(
        text(
            f'UPDATE "{col.schema}"."{col.table}" AS t SET "{col.column}" = m.novo '
            f"FROM _filtro_map m WHERE {cond} AND t.\"{col.column}\" IS NOT NULL"
        )
    )
    conn.execute(text("DROP TABLE _filtro_map"))
    return result.rowcount or 0


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao de nomes de cidadaos...")

    with engine.begin() as conn:
        targets = [c for c in NAME_COLUMNS if _column_exists(conn, c.schema, c.table, c.column)]
        for col in NAME_COLUMNS:
            if col not in targets:
                log.warning("coluna inexistente, pulando: %s", col.qualified)

        if not targets:
            log.info("nenhuma coluna de nome de cidadao encontrada — nada a fazer.")
            return

        names: set[str] = set()
        for col in targets:
            values = _collect_raw_values(conn, col)
            log.debug("%s: %d nome(s) distinto(s) coletado(s)", col.qualified, len(values))
            names |= values

        if not names:
            log.info("nenhum nome de cidadao a anonimizar.")
            return

        name_to_fake = build_name_map(names)
        conn.execute(
            text(
                "CREATE TEMP TABLE _nome_cidadao_map "
                "(old_name text PRIMARY KEY, new_name text NOT NULL) "
                "ON COMMIT DROP"
            )
        )
        conn.execute(
            text("INSERT INTO _nome_cidadao_map (old_name, new_name) VALUES (:old, :new)"),
            [{"old": old, "new": new} for old, new in name_to_fake.items()],
        )

        total = 0
        for col in targets:
            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" AS t '
                    f'SET "{col.column}" = m.new_name '
                    f"FROM _nome_cidadao_map m "
                    f'WHERE t."{col.column}"::text = m.old_name'
                )
            )
            log.info("%s: %d nome(s) atualizado(s)", col.qualified, result.rowcount)
            total += result.rowcount or 0

        filtros = 0
        for fcol in FILTER_COLUMNS:
            if not _column_exists(conn, fcol.schema, fcol.table, fcol.column):
                log.warning("coluna de busca inexistente, pulando: %s", fcol.qualified)
                continue
            n = _recompute_filter(conn, fcol)
            log.info("%s: %d linha(s) de busca recalculada(s)", fcol.qualified, n)
            filtros += n

        log.info(
            "concluido: %d grafia(s) -> %d nome(s) ficticio(s), %d linha(s) atualizada(s), "
            "%d linha(s) de busca recalculada(s).",
            len(name_to_fake),
            len(set(name_to_fake.values())),
            total,
            filtros,
        )
