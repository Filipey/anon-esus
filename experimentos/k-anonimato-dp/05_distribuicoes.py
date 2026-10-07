"""Experimento 05 - mudança das distribuições: original x tratada.

Para cada variável que o tratamento altera, compara a distribuição na base
original com a distribuição publicada, em memória (mesmos algoritmos das
migrations, `scripts/k_anonimato.py`), para k em {2, 3, 5, 10, 15, 20, 30}:

- idade em anos (0-100) e, abaixo de 5 anos, em meses — vem da data de
  nascimento microagregada (migration 15);
- raça/cor, escolaridade (5 níveis) e estado civil — supressão vira a
  categoria "não informado" (15);
- peso, altura e IMC — corte de extremos + microagregação (08);
- diagnósticos — distribuição sobre os códigos CID-10/CIAP-2 publicados;
  código suprimido vira "suprimido" (16).

Medida: divergência de Kullback-Leibler KL(original || tratada), em nats —
quanta informação se perde ao usar a tratada no lugar da original — e
Jensen-Shannon (base 2, simétrica, entre 0 e 1). As duas são calculadas
sobre faixas fixas, as mesmas para original e tratada, com suavização
aditiva de 0,5 por célula: sem ela a KL é infinita sempre que a tratada zera
uma célula que a original tem (a microagregação e a supressão fazem isso).

Grava `resultados/05_distribuicoes_<ts>.json` com as distribuições de k = 5
(para as figuras) e as divergências de todos os k. Só agregado.
"""

from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd

import _kanon as K
import _populacao as P
from _conexao import conectar, gravar, titulo

KS = (2, 3, 5, 10, 15, 20, 30)
K_FIGURA = 5
ALFA = 0.5
BINS_ANTRO = {"peso": (0, 150, 1.0), "altura": (40, 200, 1.0), "imc": (10, 50, 0.5)}
NI = "não informado"
ROT_ESCOL = {"nenhuma": "nenhuma", "infantil": "infantil", "fundamental": "fundamental",
             "medio": "médio", "superior": "superior"}


def divergencias(p_cont: np.ndarray, q_cont: np.ndarray) -> dict:
    p = (p_cont + ALFA) / (p_cont + ALFA).sum()
    q = (q_cont + ALFA) / (q_cont + ALFA).sum()
    m = (p + q) / 2
    kl = float(np.sum(p * np.log(p / q)))
    js = float(0.5 * np.sum(p * np.log2(p / m)) + 0.5 * np.sum(q * np.log2(q / m)))
    return {"kl": round(kl, 5), "js": round(js, 5)}


def contar(valores: pd.Series, categorias: list) -> np.ndarray:
    c = valores.value_counts()
    return np.array([int(c.get(x, 0)) for x in categorias], dtype=float)


def idade_anos(nasc: pd.Series, ref: pd.Timestamp) -> pd.Series:
    return ((ref - nasc).dt.days // 365.25).clip(0, 100).astype(int)


def medir_nucleo(pes: pd.DataFrame, r: pd.DataFrame, ref: pd.Timestamp) -> tuple[dict, dict]:
    dist, div = {}, {}
    anos = list(range(101))
    o, t = idade_anos(pes["dt_nasc"], ref), idade_anos(r["dt_nasc_pub"], ref)
    dist["idade"] = {"eixo": anos, "original": contar(o, anos).tolist(), "tratada": contar(t, anos).tolist()}

    # menores de 5 anos na original; a tratada é medida nas mesmas pessoas. Quem
    # passa de 59 meses na tratada vai para a faixa 60 (">= 60"), que entra na
    # KL mas não no gráfico (antes era cortado em 59 e virava um pico falso).
    meses = list(range(61))
    mo = ((ref - pes["dt_nasc"]).dt.days // 30.4375)
    mt = ((ref - r["dt_nasc_pub"]).dt.days // 30.4375)
    sel = mo < 60
    dist["idade_meses_menores_5"] = {"eixo": meses, "original": contar(mo[sel].astype(int), meses).tolist(),
                                     "tratada": contar(mt[sel].clip(0, 60).astype(int), meses).tolist()}

    for nome, col_orig, col_pub, rotulo in (
        ("raca_cor", "raca_cor", "raca_cor_pub", None),
        ("escolaridade", "escolaridade_nivel", "escolaridade_nivel_pub", ROT_ESCOL),
        ("estado_civil", "estado_civil", "estado_civil_pub", None),
    ):
        orig = r[col_orig].astype(object).where(r[col_orig].notna(), NI).astype(str)
        pub = r[col_pub].where(r[col_pub] != K.NULO, NI).astype(str)
        orig = orig.str.replace(r"\.0$", "", regex=True)
        pub = pub.str.replace(r"\.0$", "", regex=True)
        cats = sorted(set(orig) | set(pub), key=lambda x: (x == NI, x))
        dist[nome] = {"eixo": [rotulo.get(c, c) if rotulo else c for c in cats],
                      "original": contar(orig, cats).tolist(), "tratada": contar(pub, cats).tolist()}
    for nome, d in dist.items():
        div[nome] = divergencias(np.array(d["original"]), np.array(d["tratada"]))
    return dist, div


def medir_antro(med: pd.DataFrame, k: int) -> tuple[dict, dict]:
    dist, div = {}, {}
    for var, (lo, hi, passo) in BINS_ANTRO.items():
        ok = med[var].notna()
        orig = med.loc[ok, var]
        trat, _ = K.antropometria(med[var], med["id"], k)
        trat = trat[ok]
        bordas = np.arange(lo, hi + passo, passo)
        po, _ = np.histogram(orig.clip(lo, hi), bins=bordas)
        pt, _ = np.histogram(trat.clip(lo, hi), bins=bordas)
        dist[var] = {"eixo": bordas[:-1].tolist(), "original": po.tolist(), "tratada": pt.tolist()}
        div[var] = divergencias(po.astype(float), pt.astype(float))
    return dist, div


def medir_diag(diag: pd.DataFrame, k: int) -> dict:
    d = K.diagnosticos(diag, None, k)
    # migration 16: CID sobe para a categoria (nível 1) e acima disso é suprimido; CIAP raro é suprimido
    pub = np.where(d["nivel"] == 0, d["codigo"],
                   np.where((d["sistema"] == "CID") & (d["nivel"] == 1), d["publicado"], "suprimido"))
    orig = d["sistema"] + ":" + d["codigo"]
    pub = pd.Series(np.where(pub == "suprimido", "suprimido", d["sistema"] + ":" + pub))
    cats = sorted(set(orig) | set(pub))
    return divergencias(contar(orig, cats), contar(pub, cats))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--referencia", default=date.today().isoformat())
    args = ap.parse_args()
    ref = pd.Timestamp(args.referencia)

    conn = conectar()
    titulo("05 - mudança das distribuições (original x tratada)")
    pes = P.pessoas(conn, date.fromisoformat(args.referencia), apenas_ativos=False)
    diag, med = P.diagnosticos(conn), P.medicoes(conn)

    por_k, figura = [], {}
    for k in KS:
        r = K.nucleo_adaptativo(pes, k, 1, True)
        dn, divn = medir_nucleo(pes, r, ref)
        da, diva = medir_antro(med, k)
        divs = {**divn, **diva, "diagnosticos": medir_diag(diag, k)}
        por_k.append({"k": k, "divergencias": divs})
        if k == K_FIGURA:
            figura = {**dn, **da}
        print(f"  k = {k:>2}  " + "  ".join(f"{n} KL={v['kl']:.4f}" for n, v in divs.items()))

    gravar("05_distribuicoes", {"referencia": args.referencia, "k_figura": K_FIGURA, "alfa": ALFA,
                                "distribuicoes_k5": figura, "por_k": por_k})


if __name__ == "__main__":
    main()
