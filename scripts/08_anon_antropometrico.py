"""Migration 08 - Antropometria: corte de extremos + microagregação (k-anonimato).

Substitui o hash provisório, que destruía o dado (nenhuma distribuição de
peso/altura sobrevivia) e nem protegia: campo numérico de poucos milhares de
valores plausíveis, o hash era revertido por força bruta.

Por variável (peso, altura, IMC, perímetro cefálico, circunferência
abdominal, perímetro de panturrilha, altura uterina):

1. **Corte de extremos**: valores abaixo do quantil 0,1% ou acima do 99,9%
   vão para a faixa da ponta. Pega erro de digitação (peso de 500 kg, IMC de
   2.721) e o extremo real visível (pessoa muito alta), que identifica.
2. **Microagregação por valor**: os valores ordenados são agrupados em
   blocos com pelo menos `K` pessoas distintas, e cada valor vira a mediana
   do seu bloco (robusta a erro de digitação que escape do corte). Vira uma tabela de faixas [início, fim) -> publicado
   (`scripts/k_anonimato.py`); como a regra depende só do valor, o mesmo
   peso vira o mesmo número em qualquer tabela, operacional ou DW, sem
   precisar ligar cada linha à sua medição.

As faixas são calculadas a partir de `tb_medicao` (operacional, com a
pessoa de cada medição) e aplicadas a todas as colunas de `ANTHRO_COLUMNS`.
O IMC de `ta_/tb_/tl_medicao` é recalculado a partir do peso e da altura já
publicados quando os dois existem, para continuar coerente com eles; senão
segue a própria faixa. Valor que não é número vira nulo.

`K` acompanha o k-anonimato do núcleo (migration 15, decisão de
07/10/2026). Medido em `experimentos/k-anonimato-dp/02_varredura_k.py`: a
distorção é desprezível (Wasserstein ~0,1% do desvio padrão) e a
correlação peso x altura se mantém.

Atômica: tudo numa transação.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

import k_anonimato

log = get_logger("08_anon_antropometrico")

K = 5
CORTE = (0.001, 0.999)
CASAS = 1


@dataclass(frozen=True)
class AnthroColumn:
    schema: str
    table: str
    column: str
    variavel: str

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"."{self.column}"'


def _medicao(tabela: str) -> list[AnthroColumn]:
    return [
        AnthroColumn("public", tabela, "nu_medicao_peso", "peso"),
        AnthroColumn("public", tabela, "nu_medicao_altura", "altura"),
        AnthroColumn("public", tabela, "nu_medicao_perimetro_cefalico", "perimetro_cefalico"),
        AnthroColumn("public", tabela, "nu_medicao_circunf_abdominal", "circ_abdominal"),
        AnthroColumn("public", tabela, "nu_perimetro_panturrilha", "panturrilha"),
        AnthroColumn("public", tabela, "nu_medicao_altura_uterina", "altura_uterina"),
        AnthroColumn("public", tabela, "nu_medicao_imc", "imc"),
    ]


def _fat(tabela: str, *pares: tuple[str, str]) -> list[AnthroColumn]:
    return [AnthroColumn("public", tabela, col, var) for col, var in pares]


_DW_ATENDIMENTO = (
    ("nu_peso", "peso"), ("nu_altura", "altura"), ("nu_perimetro_cefalico", "perimetro_cefalico"),
    ("nu_circ_abdominal", "circ_abdominal"), ("nu_perim_panturrilha", "panturrilha"),
)

ANTHRO_COLUMNS: list[AnthroColumn] = [
    *_medicao("ta_medicao"),
    *_medicao("tb_medicao"),
    *_medicao("tl_medicao"),
    *_fat("tb_fat_atendimento_individual", *_DW_ATENDIMENTO),
    *_fat("tb_fat_atendimento_odonto", *_DW_ATENDIMENTO),
    *_fat("tb_fat_proced_atend", *_DW_ATENDIMENTO),
    *_fat("tb_fat_consolidado_cidadao_fai",
          ("nu_peso", "peso"), ("nu_altura", "altura"), ("nu_peso_prcltra", "peso"),
          ("nu_altura_prcltra", "altura"), ("nu_perimetro_cefalico_prcltra", "perimetro_cefalico")),
    # achadas no inventário da fase 2 (set/2026), fora da lista anterior
    *_fat("tb_fat_rel_op_crianca",
          ("nu_peso", "peso"), ("nu_altura", "altura"), ("nu_perimetro_cefalico", "perimetro_cefalico")),
    *_fat("tb_fat_visita_domiciliar", ("nu_peso", "peso"), ("nu_altura", "altura")),
]

# Fonte das faixas: medição com a pessoa (para contar pessoas distintas).
FONTE_SQL = """
    SELECT p.co_cidadao AS pessoa, {colunas}
    FROM public.tb_medicao m
    JOIN public.tb_atend_prof ap ON ap.co_seq_atend_prof = m.co_atend_prof
    JOIN public.tb_atend a ON a.co_seq_atend = ap.co_atend
    JOIN public.tb_prontuario p ON p.co_seq_prontuario = a.co_prontuario
"""
NUMERO = r"^\s*[0-9]+([.,][0-9]+)?\s*$"
TEXT_TYPES = {"character varying", "character", "text"}


def _column_type(conn: Connection, col: AnthroColumn) -> str | None:
    row = conn.execute(
        text(
            """
            SELECT data_type FROM information_schema.columns
            WHERE table_schema = :s AND table_name = :t AND column_name = :c
            """
        ),
        {"s": col.schema, "t": col.table, "c": col.column},
    ).first()
    return row[0] if row else None


def _numero_sql(ref: str, data_type: str) -> str:
    if data_type in TEXT_TYPES:
        return f"(CASE WHEN {ref} ~ '{NUMERO}' THEN replace(btrim({ref}), ',', '.')::numeric END)"
    return f"{ref}::numeric"


def _tem_ligacao_pessoa(conn: Connection) -> bool:
    return all(
        _column_type(conn, AnthroColumn("public", t, c, ""))
        for t, c in (("tb_medicao", "co_atend_prof"), ("tb_atend_prof", "co_atend"),
                     ("tb_atend", "co_prontuario"), ("tb_prontuario", "co_cidadao"))
    )


def calcular_faixas(conn: Connection) -> dict[str, list[tuple[float, float, float]]]:
    """Faixas por variável. Fonte preferida: tb_medicao, com a pessoa de cada
    medição (k conta pessoas distintas). Variável sem dado lá usa as colunas
    do DW que existirem, contando cada linha como uma pessoa."""
    fonte = {c.variavel: c for c in ANTHRO_COLUMNS
             if c.table == "tb_medicao" and _column_type(conn, c)}
    medicao = pd.DataFrame()
    if fonte and _tem_ligacao_pessoa(conn):
        colunas = ", ".join(f"{_numero_sql('m.' + c.column, 'text')} AS {v}" for v, c in fonte.items())
        medicao = pd.DataFrame(conn.execute(text(FONTE_SQL.format(colunas=colunas))).mappings().all())

    faixas: dict[str, list[tuple[float, float, float]]] = {}
    for var in sorted({c.variavel for c in ANTHRO_COLUMNS}):
        if var in medicao and medicao[var].notna().any():
            valores = pd.to_numeric(medicao[var], errors="coerce")
            faixas[var] = k_anonimato.faixas_antropometria(valores, medicao["pessoa"], K, CORTE, CASAS)
            continue
        dw: list[float] = []
        for c in ANTHRO_COLUMNS:
            tipo = _column_type(conn, c) if c.variavel == var else None
            if tipo:
                expr = _numero_sql(f'"{c.column}"', tipo)
                dw += [float(v) for v in conn.execute(
                    text(f'SELECT {expr} FROM {c.schema}."{c.table}"')).scalars() if v is not None]
        if dw:
            valores = pd.Series(dw)
            faixas[var] = k_anonimato.faixas_antropometria(
                valores, pd.Series(range(len(valores))), K, CORTE, CASAS)
    return faixas


def _aplicar(conn: Connection, col: AnthroColumn, data_type: str) -> int:
    valor = _numero_sql(f't."{col.column}"', data_type)
    novo = "f.publicado::text" if data_type in TEXT_TYPES else "f.publicado"
    return conn.execute(
        text(
            f'UPDATE {col.schema}."{col.table}" AS t SET "{col.column}" = '
            f"CASE WHEN {valor} IS NULL THEN NULL ELSE {novo} END "
            f"FROM _faixa_antro f "
            f"WHERE f.variavel = :var AND t.\"{col.column}\" IS NOT NULL "
            f"  AND ({valor} IS NULL OR ((f.inicio IS NULL OR {valor} >= f.inicio) "
            f"                           AND (f.fim IS NULL OR {valor} < f.fim)))"
        ),
        {"var": col.variavel},
    ).rowcount


def _recalcular_imc(conn: Connection, tabela: str) -> int:
    peso = _numero_sql('"nu_medicao_peso"', "text")
    altura = _numero_sql('"nu_medicao_altura"', "text")
    return conn.execute(
        text(
            f'UPDATE public."{tabela}" SET "nu_medicao_imc" = '
            f"round({peso} / power({altura} / 100.0, 2), 2)::text "
            f"WHERE {peso} IS NOT NULL AND {altura} IS NOT NULL AND {altura} > 0"
        )
    ).rowcount


def run(engine: Engine) -> None:
    """Executa a migration de forma atômica."""
    log.info("iniciando corte de extremos e microagregação da antropometria (k=%d)...", K)
    with engine.begin() as conn:
        faixas = calcular_faixas(conn)
        if not faixas:
            log.info("nenhuma coluna antropométrica encontrada — nada a fazer.")
            return
        conn.execute(text(
            "CREATE TEMP TABLE _faixa_antro (variavel text, inicio numeric, fim numeric, "
            "publicado numeric) ON COMMIT DROP"
        ))
        conn.execute(
            text("INSERT INTO _faixa_antro VALUES (:v, :i, :f, :p)"),
            [
                {"v": var, "i": None if ini == float("-inf") else ini,
                 "f": None if fim == float("inf") else fim, "p": pub}
                for var, fx in faixas.items() for ini, fim, pub in fx
            ],
        )
        for var, fx in sorted(faixas.items()):
            log.info("%s: %d faixa(s)", var, len(fx))

        total = 0
        for col in ANTHRO_COLUMNS:
            if col.variavel == "imc":
                continue  # IMC depois do peso e da altura
            data_type = _column_type(conn, col)
            if data_type is None:
                log.warning("coluna inexistente, pulando: %s", col.qualified)
                continue
            if col.variavel not in faixas:
                log.warning("sem faixas para %s, pulando: %s", col.variavel, col.qualified)
                continue
            n = _aplicar(conn, col, data_type)
            log.info("%s: %d valor(es) microagregado(s)", col.qualified, n)
            total += n

        for col in [c for c in ANTHRO_COLUMNS if c.variavel == "imc"]:
            data_type = _column_type(conn, col)
            if data_type is None:
                log.warning("coluna inexistente, pulando: %s", col.qualified)
                continue
            if "imc" in faixas:
                total += _aplicar(conn, col, data_type)  # quem não tem peso e altura
            n = _recalcular_imc(conn, col.table)
            log.info("%s: %d IMC recalculado(s) do peso/altura publicados", col.qualified, n)

        log.info("concluído: %d valor(es) antropométrico(s) tratados.", total)
