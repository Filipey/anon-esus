"""Experimento 03 - kit de marginais com differential privacy e varredura de ε.

A base guardada depois do prazo é a anonimizada por k-anonimato, que engrossa
o dado de forma permanente (idade em blocos, doença rara em categoria, peso
microagregado). O kit guarda a resolução fina que a geração de população
sintética vai querer, medida AGORA na original, com garantia formal: tabelas
de contagem (marginais) com ruído gaussiano discreto (OpenDP), contabilizadas
em zCDP e convertidas para (ε, δ). Qualquer coisa derivada do kit continua
protegida (pós-processamento).

Marginais (cada pessoa contribui com 1 em cada; diagnósticos até `C_DIAG`
códigos por pessoa; antropometria = última medição de cada variável):

- modelo de pessoas (entram no estimador): sexo x idade5 x equipe;
  sexo x idade5 x raça x escolaridade; sexo x idade5 x equipe x tercil;
  sexo x idade5 x estado civil; idade5 x raça x equipe;
- detalhe: sexo x idade em anos; pessoas por diagnóstico (CID-10 categoria /
  CIAP-2); capítulo do diagnóstico x sexo x faixa de 10 anos; peso (2,5 kg),
  altura (2,5 cm) e IMC (1 unidade) x sexo x idade em grupos de 5 anos.

Varredura (padrão): para cada ε, sorteia o kit, mede o erro de cada marginal
(distância de variação total e erro nas células raras, com 1-4 pessoas) e
ajusta um modelo gráfico (private-pgm / mbi, como no MST) só com as
marginais de pessoas, medindo a fidelidade em três combinações de 3
atributos que NÃO foram medidas. Nenhum kit é gravado na varredura.

`--gravar --epsilon X`: sorteia UM kit com o ε escolhido e o grava em
`resultados/kit_dp_eps<X>.json`. Só esse pode ser guardado: kits com ε
diferentes, guardados juntos, somam o custo de privacidade.
"""

from __future__ import annotations

import argparse
import math
import warnings
from datetime import date

import numpy as np
import pandas as pd

import _populacao as P
from _kanon import capitulo_cid
from _conexao import conectar, gravar, titulo

warnings.filterwarnings("ignore", module="mbi")

EPSILONS = (0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0)
DELTA = 1e-6
C_DIAG = 10
SEMENTE = 20261007

ATRIBUTOS = {  # atributo do modelo de pessoas -> tamanho do domínio
    "sexo": 2, "idade5": 21, "equipe": 7, "tercil": 4, "raca": 6, "escol": 16, "civil": 6,
}
MARGINAIS_PESSOA = [
    ("sexo", "idade5", "equipe"),
    ("sexo", "idade5", "raca", "escol"),
    ("sexo", "idade5", "equipe", "tercil"),
    ("sexo", "idade5", "civil"),
    ("idade5", "raca", "equipe"),
]
FORA_DO_MODELO = [("equipe", "raca", "escol"), ("tercil", "raca", "civil"), ("idade5", "escol", "tercil")]
# Granularidade ajustada ao tamanho da população: com 1 kg x idade em anos
# (~30 mil células para 11 mil pessoas) o ruído apagava tudo (TVD ~0,8 com ε = 1).
BINS_ANTRO = {"peso": (0, 150, 2.5), "altura": (40, 200, 2.5), "imc": (10, 50, 1.0)}


# ------------------------------------------------------------ dados
def codificar_pessoas(pes: pd.DataFrame) -> pd.DataFrame:
    """Atributos inteiros 0..n-1 (ausente vira a última categoria)."""
    def cat(serie: pd.Series, n: int) -> np.ndarray:
        valores = sorted(v for v in serie.dropna().unique())[: n - 1]
        idx = {v: i for i, v in enumerate(valores)}
        return serie.map(idx).fillna(n - 1).astype(int).to_numpy()

    return pd.DataFrame({
        "id": pes["id"].to_numpy(),
        "sexo": (pes["sexo"] == "FEMININO").astype(int).to_numpy(),
        "idade": pes["idade"].clip(0, 100).astype(int).to_numpy(),
        "idade5": (pes["idade"].clip(0, 100) // 5).astype(int).to_numpy(),
        "faixa10": (pes["idade"].clip(0, 100) // 10).astype(int).to_numpy(),
        "equipe": cat(pes["equipe"], 7),
        "tercil": pes["tercil"].fillna(0).astype(int).to_numpy() if pes["tercil"].notna().any()
        else np.zeros(len(pes), int),
        "raca": pes["raca_cor"].fillna(6).clip(1, 6).astype(int).to_numpy() - 1,
        "escol": pes["escolaridade"].fillna(16).clip(1, 16).astype(int).to_numpy() - 1,
        "civil": pes["estado_civil"].fillna(6).clip(1, 6).astype(int).to_numpy() - 1,
    })


def histograma(df: pd.DataFrame, cols: tuple[str, ...], formas: tuple[int, ...]) -> np.ndarray:
    h = np.zeros(formas, dtype=np.int64)
    np.add.at(h, tuple(df[c].to_numpy() for c in cols), 1)
    return h


def montar_marginais(pes: pd.DataFrame, diag: pd.DataFrame, med: pd.DataFrame, rng) -> dict:
    """{nome: (contagens verdadeiras, sensibilidade L2, eixos)}."""
    x = codificar_pessoas(pes)
    out = {}
    for cols in MARGINAIS_PESSOA:
        out["x".join(cols)] = (histograma(x, cols, tuple(ATRIBUTOS[c] for c in cols)), 1.0, cols)
    out["sexoxidade"] = (histograma(x, ("sexo", "idade"), (2, 101)), 1.0, ("sexo", "idade"))

    # diagnósticos: categoria CID (3 caracteres) ou código CIAP; até C_DIAG por pessoa
    d = diag.assign(cod=np.where(diag["sistema"] == "CID", "CID:" + diag["codigo"].str[:3],
                                 "CIAP:" + diag["codigo"]))[["id", "cod"]].drop_duplicates()
    d = d[d["id"].isin(x["id"])]
    d = d.sample(frac=1.0, random_state=SEMENTE).groupby("id").head(C_DIAG)
    codigos = sorted(d["cod"].unique())
    d = d.merge(x[["id", "sexo", "faixa10"]], on="id")
    d["c"] = d["cod"].map({c: i for i, c in enumerate(codigos)})
    # prevalência por código (onde ficam as doenças raras) e capítulo x sexo x
    # faixa (distribuição por idade e sexo); o cruzamento código x sexo x faixa
    # tinha ~40 mil células e virava só ruído.
    out["diagnostico"] = (histograma(d, ("c",), (len(codigos),)), math.sqrt(C_DIAG), ("diagnostico",))
    capitulos = sorted({_capitulo(c) for c in codigos})
    d["cap"] = d["cod"].map(lambda c: capitulos.index(_capitulo(c)))
    out["capitulo_diagxsexoxfaixa10"] = (
        histograma(d, ("cap", "sexo", "faixa10"), (len(capitulos), 2, 11)), math.sqrt(C_DIAG),
        ("capitulo", "sexo", "faixa10"))
    out["_codigos"] = codigos
    out["_capitulos"] = capitulos

    # antropometria: última medição de cada variável por pessoa
    m = med.merge(pes[["id", "dt_nasc"]], on="id")
    m["idade"] = P.idade_na_data(m["dt_nasc"], m["dt_medicao"]).clip(0, 100)
    m = m.merge(x[["id", "sexo"]], on="id")
    for var, (lo, hi, passo) in BINS_ANTRO.items():
        ult = m[m[var].notna()].sort_values("dt_medicao").groupby("id").tail(1)
        nb = int(round((hi - lo) / passo)) + 1
        ult = ult.assign(b=((ult[var].clip(lo, hi) - lo) / passo).round().astype(int),
                         idade5=(ult["idade"] // 5).astype(int))
        out[f"{var}xsexoxidade5"] = (histograma(ult, ("b", "sexo", "idade5"), (nb, 2, 21)), 1.0,
                                     (f"{var}_bin", "sexo", "idade5"))
    return out


def _capitulo(codigo: str) -> str:
    """CID:A00 -> capítulo da CID-10; CIAP:K86 -> capítulo (letra) da CIAP."""
    sistema, cod = codigo.split(":", 1)
    if sistema == "CID":
        return capitulo_cid(cod)
    return f"CIAP-{cod[0]}" if cod[:1].isalpha() else "CIAP-proc"


# ------------------------------------------------------------ privacidade
def rho_de_epsilon(eps: float, delta: float = DELTA) -> float:
    """Maior ρ (zCDP) com ρ + 2 sqrt(ρ ln(1/δ)) <= ε."""
    l = math.log(1 / delta)
    return (math.sqrt(l + eps) - math.sqrt(l)) ** 2


def sortear(marginais: dict, eps: float, rng_seed: int) -> dict:
    """Mesmo ρ para cada marginal; ruído gaussiano discreto do OpenDP."""
    import opendp.prelude as dp
    dp.enable_features("contrib")
    nomes = [n for n in marginais if not n.startswith("_")]
    rho_cada = rho_de_epsilon(eps) / len(nomes)
    espaco = dp.vector_domain(dp.atom_domain(T=int)), dp.l2_distance(T=int)
    out = {}
    for nome in nomes:
        verdade, sens, eixos = marginais[nome]
        sigma = sens / math.sqrt(2 * rho_cada)
        mec = dp.m.make_gaussian(*espaco, scale=sigma)
        assert mec.map(1) * sens ** 2 <= rho_cada * (1 + 1e-9)
        ruidoso = np.array(mec(verdade.ravel().tolist()), dtype=np.int64).reshape(verdade.shape)
        out[nome] = {"ruidoso": ruidoso, "sigma": sigma, "eixos": eixos, "rho": rho_cada}
    return out


# ------------------------------------------------------------ métricas
def erro_marginal(verdade: np.ndarray, ruidoso: np.ndarray) -> dict:
    n = verdade.sum()
    pos = np.clip(ruidoso, 0, None)
    raras = (verdade >= 1) & (verdade <= 4)
    grandes = verdade >= 20
    return {
        "tvd": round(float(0.5 * np.abs(pos / max(1, pos.sum()) - verdade / max(1, n)).sum()), 4),
        "erro_abs_medio_celulas_raras": round(float(np.abs(ruidoso - verdade)[raras].mean()), 2) if raras.any() else None,
        "erro_rel_medio_celulas_grandes": round(float((np.abs(ruidoso - verdade) / np.maximum(verdade, 1))[grandes].mean()), 4)
        if grandes.any() else None,
    }


def fidelidade_modelo(kit: dict, x: pd.DataFrame) -> dict:
    """Ajusta o modelo gráfico só com as marginais de pessoas e mede as
    combinações de fora do modelo."""
    import jax
    jax.config.update("jax_enable_x64", True)
    from mbi import Domain, LinearMeasurement
    from mbi.estimation import MirrorDescent

    dominio = Domain(list(ATRIBUTOS), [ATRIBUTOS[a] for a in ATRIBUTOS])
    medidas = []
    for cols in MARGINAIS_PESSOA:
        k = kit["x".join(cols)]
        medidas.append(LinearMeasurement(k["ruidoso"].ravel().astype(float), cols, stddev=k["sigma"]))
    modelo = MirrorDescent().estimate(dominio, medidas, iters=500)
    out = {}
    for cols in FORA_DO_MODELO:
        verdade = histograma(x, cols, tuple(ATRIBUTOS[c] for c in cols)).astype(float)
        est = np.asarray(modelo.project(list(cols)).datavector(flatten=False))
        out["x".join(cols)] = round(float(0.5 * np.abs(est / est.sum() - verdade / verdade.sum()).sum()), 4)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--referencia", default=date.today().isoformat())
    ap.add_argument("--epsilons", nargs="*", type=float, default=list(EPSILONS))
    ap.add_argument("--gravar", action="store_true", help="grava UM kit com --epsilon")
    ap.add_argument("--epsilon", type=float)
    ap.add_argument("--sem-modelo", action="store_true", help="pula o ajuste do modelo gráfico")
    args = ap.parse_args()

    conn = conectar()
    pes = P.pessoas(conn, date.fromisoformat(args.referencia), apenas_ativos=False)
    diag, med = P.diagnosticos(conn), P.medicoes(conn)
    rng = np.random.default_rng(SEMENTE)
    marginais = montar_marginais(pes, diag, med, rng)
    x = codificar_pessoas(pes)

    if args.gravar:
        if args.epsilon is None:
            raise SystemExit("--gravar exige --epsilon")
        kit = sortear(marginais, args.epsilon, SEMENTE)
        gravar(f"kit_dp_eps{args.epsilon:g}", {
            "epsilon": args.epsilon, "delta": DELTA, "rho_total": rho_de_epsilon(args.epsilon),
            "mecanismo": "gaussiano discreto (OpenDP), zCDP, mesmo rho por marginal",
            "c_diag": C_DIAG, "codigos_diagnostico": marginais["_codigos"],
            "capitulos_diagnostico": marginais["_capitulos"],
            "referencia_idade": args.referencia, "pessoas_aprox": int(len(pes)),
            "marginais": {n: {"eixos": k["eixos"], "sigma": k["sigma"], "rho": k["rho"],
                              "forma": list(k["ruidoso"].shape), "contagens": k["ruidoso"].ravel().tolist()}
                          for n, k in kit.items()},
        })
        print("Kit gravado. Apague qualquer outro kit gerado com ε diferente.")
        return

    titulo("03 - varredura de ε do kit DP")
    nomes = [n for n in marginais if not n.startswith("_")]
    print(f"  {len(pes):,} pessoas; {len(nomes)} marginais; "
          f"{sum(marginais[n][0].size for n in nomes):,} células; δ = {DELTA:g}")
    resultados = []
    for eps in args.epsilons:
        kit = sortear(marginais, eps, SEMENTE)
        linha = {"epsilon": eps, "rho_total": rho_de_epsilon(eps), "marginais": {}}
        for n in nomes:
            linha["marginais"][n] = {"sigma": round(kit[n]["sigma"], 2),
                                     **erro_marginal(marginais[n][0], kit[n]["ruidoso"])}
        if not args.sem_modelo:
            linha["fidelidade_fora_do_modelo_tvd"] = fidelidade_modelo(kit, x)
        resultados.append(linha)
        mg = linha["marginais"]
        print(f"\n  ε = {eps:g}  (ρ = {linha['rho_total']:.4f})")
        for n in nomes:
            e = mg[n]
            print(f"    {n:34} σ={e['sigma']:8.2f}  TVD={e['tvd']:.3f}  "
                  f"raras: erro {e['erro_abs_medio_celulas_raras']}  grandes: erro rel {e['erro_rel_medio_celulas_grandes']}")
        if "fidelidade_fora_do_modelo_tvd" in linha:
            print(f"    modelo, combinações não medidas (TVD): {linha['fidelidade_fora_do_modelo_tvd']}")
    gravar("03_varredura_epsilon", {"delta": DELTA, "c_diag": C_DIAG, "resultados": resultados})


if __name__ == "__main__":
    main()
