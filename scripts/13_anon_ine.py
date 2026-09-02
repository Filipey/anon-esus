"""Migration 13 - Anonimizacao do INE (Identificador Nacional de Equipe).

O INE identifica a equipe de saude no cadastro nacional e e **publico**,
exatamente como o CNES. O argumento que justifica a migration 02 vale
palavra por palavra aqui: o codigo sozinho permite reidentificar a
entidade mesmo depois de todo o resto ter sido trocado. A diferenca e que
o INE nunca foi tratado - nao aparece em nenhuma migration nem existe como
categoria em `audit_schema.py`, entao a lacuna nunca apareceu na auditoria.

A cadeia de reidentificacao que isso abre:

    INE -> equipe real -> CNES da unidade -> unidade real -> endereco real

ou seja, desfaz o trabalho da migration 02 por um caminho lateral. E como
os extratos publicos do cadastro nacional trazem a composicao de
profissionais por equipe, enfraquece tambem a migration 05.

Caracteristicas (mesmas garantias das migrations 01/02):
- **Atomica**: roda inteira dentro de uma unica transacao.
- **Consistente entre tabelas**: o mesmo INE original recebe sempre o
  mesmo valor ficticio em todas as 29 colunas, preservando os joins de
  equipe.
- **Preserva o comprimento**: o valor ficticio tem a mesma quantidade de
  digitos do original, o que garante que cabe em qualquer coluna onde o
  original ja cabia. Foi exatamente o descuido oposto que derrubou a
  migration 11 no banco real (telefone de 11 digitos em `varchar(10)`).

**Migration nova em vez de extensao da 02.** A mecanica e a mesma, mas a
02 ja foi aplicada em bases reais e a pipeline nao e idempotente -
re-rodar re-hashearia CNES que ja e ficticio. Como migration propria, esta
etapa e aplicavel e reversivel de forma independente.

**Limitacao conhecida, mesma das migrations 08/10.** O sal esta no
codigo-fonte e o espaco de INEs reais no Brasil e da ordem de dezenas de
milhares, entao um atacante pode pre-computar o mapa. Isto reduz o
vazamento casual, nao resiste a forca bruta dirigida. Substituir por um
gerador de INE ficticio com formato valido fica para a mesma fase que o
gerador de CNS.

**Fora de escopo de proposito.** `co_equipe`/`co_dim_equipe` sao chaves
substitutas opacas - preservam o vinculo sem revelar a equipe real e nao
devem ser tocadas. O conteudo serializado de `tb_dado_transp` nao e
parseado: se o INE tambem estiver dentro do blob, ele sobrevive - mesma
classe de lacuna do texto livre, tratada na fase 2.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("13_anon_ine")


@dataclass(frozen=True)
class IneColumn:
    schema: str
    table: str
    column: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


# ---------------------------------------------------------------------------
# 29 colunas confirmadas por enumeracao do schema fisico real. Inclui as
# variantes de papel (`_vinc_equipe`, `_executante`, `_solicitante`,
# `_finalizador_obs`) - se so as tabelas "mestras" de equipe fossem
# trocadas, o INE original sobreviveria nas outras e permitiria religar a
# equipe ficticia a equipe real via join, exatamente o problema que a
# migration 02 documenta para o CNES.
# ---------------------------------------------------------------------------
INE_COLUMNS: list[IneColumn] = [
    IneColumn("public", "ta_cds_domicilio", "nu_ine"),
    IneColumn("public", "ta_cidadao_vinculacao_equipe", "nu_ine"),
    IneColumn("public", "ta_equipe", "nu_ine"),
    IneColumn("public", "ta_equipe_unificacao_base", "nu_ine"),
    IneColumn("public", "tb_acomp_cidadaos_vinculados", "nu_ine_vinc_equipe"),
    IneColumn("public", "tb_cds_domicilio", "nu_ine"),
    IneColumn("public", "tb_cds_prof", "nu_ine"),
    IneColumn("public", "tb_cidadao_nucleo_familiar", "nu_ine"),
    IneColumn("public", "tb_cidadao_vinculacao_equipe", "nu_ine"),
    IneColumn("public", "tb_criador_reserva_unif_base", "nu_ine"),
    IneColumn("public", "tb_dado_transp", "nu_ine_dado_serializado"),
    IneColumn("public", "tb_dado_transp_recebido_online", "nu_ine_dado_serializado"),
    IneColumn("public", "tb_dim_equipe", "nu_ine"),
    IneColumn("public", "tb_equipe", "nu_ine"),
    IneColumn("public", "tb_equipe_unificacao_base", "nu_ine"),
    IneColumn("public", "tb_familia", "nu_ine"),
    IneColumn("public", "tb_historico_cabecalho", "nu_ine"),
    IneColumn("public", "tb_historico_dados_fai", "nu_ine_finalizador_obs"),
    IneColumn("public", "tb_historico_dados_fcc", "nu_ine_executante"),
    IneColumn("public", "tb_historico_dados_fcc", "nu_ine_solicitante"),
    IneColumn("public", "tb_lotacao_env_unificacao_base", "nu_ine"),
    IneColumn("public", "tb_prof_grupo_ativ_col", "nu_ine"),
    IneColumn("public", "tl_cds_domicilio", "nu_ine"),
    IneColumn("public", "tl_cds_prof", "nu_ine"),
    IneColumn("public", "tl_cidadao_nucleo_familiar", "nu_ine"),
    IneColumn("public", "tl_cidadao_vinculacao_equipe", "nu_ine"),
    IneColumn("public", "tl_equipe", "nu_ine"),
    IneColumn("public", "tl_familia", "nu_ine"),
    IneColumn("public", "tl_prof_grupo_ativ_col", "nu_ine"),
]

INE_SALT = "anon-esus-equipe-ine-v1"

_NON_DIGITS = re.compile(r"\D")


def _column_exists(conn: Connection, col: IneColumn) -> bool:
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


def _collect_raw_values(conn: Connection, col: IneColumn) -> set[str]:
    rows = conn.execute(
        text(
            f'SELECT DISTINCT "{col.column}" AS v '
            f'FROM "{col.schema}"."{col.table}" '
            f'WHERE "{col.column}" IS NOT NULL '
            f"  AND btrim(\"{col.column}\"::text) <> ''"
        )
    )
    return {str(r.v) for r in rows}


def _fake_ine(value: str) -> str:
    """INE ficticio deterministico, com a mesma quantidade de digitos.

    Preservar o comprimento garante que o valor cabe em qualquer coluna
    onde o original ja cabia, sem precisar clampar por coluna - o que
    quebraria a consistencia do mapa entre tabelas.
    """
    digits = len(_NON_DIGITS.sub("", value)) or 10
    digest = hashlib.md5(f"{value}{INE_SALT}".encode()).hexdigest()
    number = int(digest[:12], 16) % (10**digits)
    return f"{number:0{digits}d}"


def run(engine: Engine) -> None:
    """Executa a migration de forma atomica."""
    log.info("iniciando anonimizacao do INE (identificador de equipe)...")

    with engine.begin() as conn:
        targets = []
        for col in INE_COLUMNS:
            if _column_exists(conn, col):
                targets.append(col)
            else:
                log.warning("coluna inexistente, pulando: %s", col.qualified)

        if not targets:
            log.info("nenhuma coluna de INE encontrada - nada a fazer.")
            return

        values: set[str] = set()
        for col in targets:
            encontrados = _collect_raw_values(conn, col)
            log.debug("%s: %d INE(s) distinto(s)", col.qualified, len(encontrados))
            values |= encontrados

        if not values:
            log.info("nenhum INE a anonimizar.")
            return

        value_to_fake = {value: _fake_ine(value) for value in sorted(values)}
        log.info("%d INE(s) distinto(s) a anonimizar", len(value_to_fake))

        conn.execute(
            text(
                "CREATE TEMP TABLE _ine_map "
                "(old_ine text PRIMARY KEY, new_ine text NOT NULL) "
                "ON COMMIT DROP"
            )
        )
        conn.execute(
            text("INSERT INTO _ine_map (old_ine, new_ine) VALUES (:old, :new)"),
            [{"old": old, "new": new} for old, new in value_to_fake.items()],
        )

        total = 0
        for col in targets:
            result = conn.execute(
                text(
                    f'UPDATE "{col.schema}"."{col.table}" AS t '
                    f'SET "{col.column}" = m.new_ine '
                    f"FROM _ine_map m "
                    f'WHERE t."{col.column}"::text = m.old_ine'
                )
            )
            log.info("%s: %d linha(s) atualizada(s)", col.qualified, result.rowcount)
            total += result.rowcount or 0

        log.info(
            "concluido: %d INE(s) distinto(s) anonimizado(s), %d linha(s) atualizada(s).",
            len(value_to_fake),
            total,
        )
