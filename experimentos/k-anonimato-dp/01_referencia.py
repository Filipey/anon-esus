"""Experimento 01 - estatísticas de referência para medir utilidade.

Calcula, num banco qualquer (a original agora; as versões anonimizadas
depois), as estatísticas que o tratamento de k-anonimato altera e que a
geração de população sintética vai precisar:

- pirâmide etária (sexo x idade em anos; sexo x idade em meses abaixo de 5);
- território: equipe x sexo x faixa de 10 anos;
- raça/cor x faixa de 10 anos;
- antropometria: por variável x sexo x ciclo de vida na data da medição,
  n, média e quantis;
- prevalência de condições: pessoas por código CID-10 (categoria de 3
  caracteres e subcategoria) e CIAP-2, por sexo x ciclo de vida.

`--banco` troca o banco lido (padrão: `DB_NAME` do .env). Grava
`resultados/01_referencia_<banco>_<ts>.json`.

**As tabelas têm contagens pequenas** (doença rara num sexo e faixa): servem
para comparar enquanto a original existe e devem ser apagadas no fim do
prazo, junto com ela. O que fica para sempre é o kit DP.
"""

from __future__ import annotations

import argparse
import os
from datetime import date

import pandas as pd

from _conexao import conectar, gravar, titulo

QUANTIS = (0.05, 0.25, 0.5, 0.75, 0.95)


def _contagem(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    g = df.groupby(cols, dropna=False, observed=True).size().reset_index(name="n")
    return g.astype({c: str for c in cols}).to_dict(orient="records")


def antropometria(med: pd.DataFrame, pes: pd.DataFrame, P) -> list[dict]:
    m = med.merge(pes[["id", "sexo", "dt_nasc"]], on="id", how="inner")
    m["idade"] = P.idade_na_data(m["dt_nasc"], m["dt_medicao"])
    m["ciclo"] = P.faixas_idade(m["idade"])["ciclo"]
    out = []
    for var in P.VARIAVEIS_ANTRO:
        sub = m[m[var].notna()]
        for (sexo, ciclo), g in sub.groupby(["sexo", "ciclo"], observed=True):
            q = g[var].quantile(list(QUANTIS))
            out.append({
                "variavel": var, "sexo": sexo, "ciclo": ciclo, "n": int(len(g)),
                "media": round(float(g[var].mean()), 3),
                **{f"p{int(k * 100)}": round(float(v), 3) for k, v in q.items()},
            })
    return out


def prevalencia(diag: pd.DataFrame, pes: pd.DataFrame) -> list[dict]:
    d = diag.merge(pes[["id", "sexo", "ciclo"]], on="id", how="inner")
    cid = d[d["sistema"] == "CID"]
    partes = [
        cid.assign(nivel="subcategoria"),
        cid.assign(nivel="categoria", codigo=cid["codigo"].str[:3]),
        d[d["sistema"] == "CIAP"].assign(nivel="ciap"),
    ]
    tudo = pd.concat(partes, ignore_index=True).drop_duplicates(["id", "nivel", "codigo"])
    g = tudo.groupby(["nivel", "codigo", "sexo", "ciclo"], observed=True)["id"].nunique()
    return g.reset_index(name="pessoas").to_dict(orient="records")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--banco", help="banco a ler (padrão: DB_NAME do .env)")
    ap.add_argument("--referencia", default=date.today().isoformat(),
                    help="data de referência da idade (padrão: hoje)")
    args = ap.parse_args()
    if args.banco:
        os.environ["DB_NAME"] = args.banco

    import _populacao as P  # depois do --banco, que o _conexao lê do ambiente

    referencia = date.fromisoformat(args.referencia)
    conn = conectar()
    banco = conn.info.dbname
    titulo(f"01 - estatísticas de referência ({banco})")

    pes = P.pessoas(conn, referencia)
    menores = pes[pes["idade"] < 5].assign(
        meses=lambda d: ((pd.Timestamp(referencia) - d["dt_nasc"]).dt.days // 30.4375).astype(int)
    )
    diag = P.diagnosticos(conn)
    med = P.medicoes(conn)

    dados = {
        "banco": banco,
        "referencia": referencia.isoformat(),
        "pessoas": len(pes),
        "piramide_anos": _contagem(pes.assign(idade=pes["idade"].astype("Int64")), ["sexo", "idade"]),
        "piramide_meses_menores_5": _contagem(menores, ["sexo", "meses"]),
        "territorio": _contagem(pes, ["equipe", "sexo", "faixa10"]),
        "raca_cor": _contagem(pes, ["raca_cor", "faixa10"]),
        "antropometria": antropometria(med, pes, P),
        "prevalencia": prevalencia(diag, pes),
    }
    print(f"  pessoas: {len(pes):,}  medições: {len(med):,}  "
          f"pares pessoa-diagnóstico: {len(diag):,}")
    print(f"  células: pirâmide {len(dados['piramide_anos'])}, antropometria "
          f"{len(dados['antropometria'])}, prevalência {len(dados['prevalencia'])}")
    gravar(f"01_referencia_{banco}", dados)


if __name__ == "__main__":
    main()
