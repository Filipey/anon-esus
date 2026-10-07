"""Medição 00 - k-anonimato sobre os quase-identificadores que sobram.

A fase 1 garantiu k >= 20 só para a geografia (classe equipe x tercil de
distância, migration 06). Mas a base mantém de propósito outros
quase-identificadores (QI): sexo, mês/ano de nascimento (a 04 só troca o
dia), raça/cor, município de nascimento e de residência, escolaridade,
ocupação... A literatura (Sweeney 2002; de Montjoye 2013) mostra que a
combinação de poucos deles costuma isolar a pessoa. Este script mede isso.

Unidade: cidadão ativo e vivo em `tb_cidadao`. Os QI vêm da própria
`tb_cidadao`, a equipe de `tb_cidadao_vinculacao_equipe` e o tercil do
domicílio pelo caminho do DW (cidadão -> território da família -> cadastro
domiciliar -> `tb_cds_domicilio`), calculado com a função da migration 06.
Valor ausente conta como categoria própria ("não informado"), como faria um
atacante que vê a célula vazia.

Mede, sempre sobre a base ORIGINAL (os QI medidos não mudam na fase 1:
a 04 preserva mês/ano, a 13 troca o INE 1:1, a 06 deriva o mesmo tercil):

1. escada de cenários - cada degrau acrescenta um QI ao anterior;
2. cada QI isolado - cardinalidade e fração de valores únicos;
3. generalização do nascimento sobre o cenário geográfico + raça/cor;
4. "tira um" - no cenário completo, quanto cai o risco sem cada QI.

Métricas por cenário: classes de equivalência, k mínimo e % de cidadãos em
classe de tamanho 1 (reidentificação garantida pela combinação), < 5, < 10
e < 20 (o k adotado na geografia). Só agregado sai do script.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from datetime import date

import pandas as pd

from _conexao import RAIZ, conectar, consulta, gravar, titulo

K_ALVO = 20
LIMIARES = (1, 5, 10, K_ALVO)

ROTULOS = {
    "sexo": "sexo",
    "nasc_mes": "mês/ano de nascimento",
    "equipe": "equipe (INE)",
    "tercil": "tercil de distância",
    "raca_cor": "raça/cor",
    "mun_nasc": "município de nascimento",
    "mun_resid": "município de residência",
    "escolaridade": "escolaridade",
    "ocupacao": "ocupação (CBO)",
    "nacionalidade": "nacionalidade",
    "estado_civil": "estado civil",
    "orient_sexual": "orientação sexual",
    "ident_genero": "identidade de gênero",
}

# Escada: cada cenário acrescenta um QI. O primeiro é o que a base publica
# hoje sobre qualquer cidadão, mesmo sem geografia.
ESCADA = [
    "sexo",
    "nasc_mes",
    "equipe",
    "tercil",
    "raca_cor",
    "mun_nasc",
    "mun_resid",
    "escolaridade",
    "ocupacao",
    "estado_civil",
    "nacionalidade",
    "orient_sexual",
    "ident_genero",
]

GENERALIZACOES_NASC = {
    "data exata (antes da 04)": "nasc_dia",
    "mês/ano (publicado hoje)": "nasc_mes",
    "ano": "nasc_ano",
    "faixa de 5 anos": "faixa5",
    "faixa de 10 anos": "faixa10",
    "ciclo de vida": "ciclo",
}
BASE_GENERALIZACAO = ["sexo", "equipe", "tercil", "raca_cor"]


def _m06():
    """Migration 06, para calcular o tercil exatamente como ela calcula."""
    scripts = RAIZ / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location("_m06_kanon", scripts / "06_anon_endereco.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_m06_kanon"] = mod
    spec.loader.exec_module(mod)
    return mod


def _sql(conn, sql: str) -> list[tuple]:
    r = consulta(conn, sql)
    if isinstance(r, dict):
        raise SystemExit(f"consulta falhou: {r['erro']}")
    return r


def carregar(conn, referencia: date) -> pd.DataFrame:
    pop = pd.DataFrame(
        _sql(
            conn,
            """
            SELECT co_seq_cidadao, no_sexo, dt_nascimento, co_raca_cor, co_localidade,
                   co_localidade_endereco, co_escolaridade, co_cbo, co_nacionalidade,
                   co_estado_civil, tp_orientacao_sexual, tp_identidade_genero
            FROM tb_cidadao
            WHERE st_ativo = 1 AND st_faleceu = 0
            """,
        ),
        columns=["id", "sexo", "dt_nasc", "raca_cor", "mun_nasc", "mun_resid", "escolaridade",
                 "ocupacao", "nacionalidade", "estado_civil", "orient_sexual", "ident_genero"],
    )

    equipe = pd.DataFrame(
        _sql(conn, "SELECT co_cidadao, max(nu_ine) FROM tb_cidadao_vinculacao_equipe GROUP BY 1"),
        columns=["id", "equipe"],
    )

    # cidadão -> domicílio pelo DW; o território de família mais recente vence.
    domicilio = pd.DataFrame(
        _sql(
            conn,
            """
            SELECT DISTINCT ON (p.co_cidadao) p.co_cidadao, d.co_seq_cds_domicilio
            FROM tb_fat_cidadao_pec p
            JOIN tb_fat_cidadao_territorio ct ON ct.co_fat_cidadao_pec = p.co_seq_fat_cidadao_pec
            JOIN tb_fat_familia_territorio ft
              ON ft.co_seq_fat_familia_territorio = ct.co_fat_familia_territorio
            JOIN tb_fat_cad_domiciliar fd ON fd.co_seq_fat_cad_domiciliar = ft.co_fat_cad_domiciliar
            JOIN tb_cds_cad_domiciliar cd ON cd.co_unico_ficha::text = fd.nu_uuid_ficha::text
            JOIN tb_cds_domicilio d ON d.co_unico_domicilio = cd.co_unico_domicilio
            ORDER BY p.co_cidadao, ft.co_seq_fat_familia_territorio DESC
            """,
        ),
        columns=["id", "domicilio"],
    )

    m06 = _m06()
    linhas = _sql(
        conn,
        "SELECT co_seq_cds_domicilio, nu_latitude::float8, nu_longitude::float8, "
        "nu_ine::text, nu_cnes::text FROM tb_cds_domicilio",
    )
    tercis = m06.calcular_tercis(linhas, m06.carregar_unidades())
    domicilio["tercil"] = domicilio["domicilio"].map(tercis)

    df = pop.merge(equipe, on="id", how="left").merge(
        domicilio[["id", "tercil"]], on="id", how="left"
    )

    nasc = pd.to_datetime(df["dt_nasc"])
    idade = (pd.Timestamp(referencia) - nasc).dt.days // 365.25
    df["nasc_dia"] = nasc.dt.strftime("%Y-%m-%d")
    df["nasc_mes"] = nasc.dt.strftime("%Y-%m")
    df["nasc_ano"] = nasc.dt.year
    df["faixa5"] = (idade // 5 * 5).astype("Int64")
    df["faixa10"] = (idade // 10 * 10).astype("Int64")
    df["ciclo"] = pd.cut(
        idade, bins=[-1, 1, 9, 19, 59, 200],
        labels=["0-1 (lactente)", "2-9 (criança)", "10-19 (adolescente)", "20-59 (adulto)", "60+ (idoso)"],
    )
    return df


def medir(df: pd.DataFrame, cols: list[str]) -> dict:
    chave = df[cols].astype(str)
    tamanho = chave.groupby(cols, dropna=False)[cols[0]].transform("size")
    n = len(df)
    out = {
        "qi": cols,
        "registros": n,
        "classes": int(chave.drop_duplicates().shape[0]),
        "k_min": int(tamanho.min()),
        "k_mediano": float(tamanho.median()),
    }
    for lim in LIMIARES:
        rot = "k1" if lim == 1 else f"k_menor_{lim}"
        sel = tamanho == 1 if lim == 1 else tamanho < lim
        out[f"pct_{rot}"] = round(100 * float(sel.mean()), 2)
        out[f"n_{rot}"] = int(sel.sum())
    return out


def linha(rot: str, m: dict) -> str:
    return (f"  {rot:42} {m['classes']:>6} {m['k_min']:>5} {m['pct_k1']:>7.1f}% "
            f"{m['pct_k_menor_5']:>7.1f}% {m['pct_k_menor_10']:>7.1f}% {m[f'pct_k_menor_{K_ALVO}']:>7.1f}%")


CAB = (f"  {'cenário':42} {'classes':>6} {'k mín':>5} {'k=1':>8} {'k<5':>8} {'k<10':>8} "
       f"{f'k<{K_ALVO}':>8}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--referencia", default=date.today().isoformat(),
                    help="data de referência para idade/faixa (padrão: hoje)")
    args = ap.parse_args()
    referencia = date.fromisoformat(args.referencia)

    conn = conectar()
    titulo("00 - k-anonimato sobre os quase-identificadores restantes")
    df = carregar(conn, referencia)
    n = len(df)
    print(f"  cidadãos ativos e vivos: {n:,}")
    print(f"  com equipe: {df['equipe'].notna().sum():,}   com tercil: {df['tercil'].notna().sum():,}")

    titulo("1. Escada de cenários (cada linha acrescenta um QI)")
    print(CAB)
    escada = []
    for i in range(1, len(ESCADA) + 1):
        cols = ESCADA[:i]
        m = medir(df, cols)
        m["acrescenta"] = ESCADA[i - 1]
        escada.append(m)
        print(linha(("+ " if i > 1 else "") + ROTULOS[ESCADA[i - 1]], m))

    titulo("2. Cada QI isolado")
    print(f"  {'QI':28} {'preench.':>9} {'distintos':>9} {'valor único':>12} {'k mín':>6}")
    marginais = {}
    for qi in ESCADA + ["nasc_dia"]:
        preench = float(df[qi].notna().mean())
        m = medir(df, [qi])
        marginais[qi] = {"preenchimento": round(preench, 4), "distintos": int(df[qi].nunique()),
                         "pct_valor_unico": m["pct_k1"], "k_min": m["k_min"]}
        print(f"  {ROTULOS.get(qi, 'data exata de nascimento'):28} {preench:>8.1%} "
              f"{marginais[qi]['distintos']:>9} {m['pct_k1']:>11.1f}% {m['k_min']:>6}")

    titulo(f"3. Generalização do nascimento sobre {' + '.join(ROTULOS[c] for c in BASE_GENERALIZACAO)}")
    print(CAB)
    generalizacao = {}
    for rot, col in GENERALIZACOES_NASC.items():
        m = medir(df, BASE_GENERALIZACAO + [col])
        generalizacao[rot] = m
        print(linha(rot, m))

    titulo("4. Cenário completo: risco sem cada QI")
    completo = medir(df, ESCADA)
    print(CAB)
    print(linha("todos", completo))
    tira_um = {}
    for qi in ESCADA:
        m = medir(df, [c for c in ESCADA if c != qi])
        m["queda_pct_k1"] = round(completo["pct_k1"] - m["pct_k1"], 2)
        tira_um[qi] = m
        print(linha(f"sem {ROTULOS[qi]}", m))

    gravar("00_quase_identificadores", {
        "referencia": referencia.isoformat(),
        "k_alvo": K_ALVO,
        "populacao": n,
        "com_equipe": int(df["equipe"].notna().sum()),
        "com_tercil": int(df["tercil"].notna().sum()),
        "escada": escada,
        "marginais": marginais,
        "generalizacao_nascimento": {"base": BASE_GENERALIZACAO, "cenarios": generalizacao},
        "completo": completo,
        "tira_um": tira_um,
    })


if __name__ == "__main__":
    main()
