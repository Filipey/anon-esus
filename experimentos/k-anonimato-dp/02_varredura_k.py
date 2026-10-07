"""Experimento 02 - varredura de k: risco x utilidade de cada componente.

Para cada k (e, no núcleo, cada variante do algoritmo), aplica em memória o
tratamento completo da metodologia final e mede:

Núcleo (sexo, nascimento, equipe, tercil, raça/cor) — `_kanon.nucleo_adaptativo`
  k mínimo alcançado; % de equipe, raça/cor e tercil suprimidos; deslocamento
  da data de nascimento (mediana e p95, em dias) por faixa de idade; % de
  pessoas com nascimento publicado depois da primeira medição registrada.
QI fora do núcleo (municípios, ocupação, escolaridade...) — valor raro -> nulo
  % de valores recodificados; risco residual: % únicos e % em classe < k com
  o núcleo publicado + todos os QI de fora.
Antropometria — corte de extremos + microagregação por valor
  por variável: erro absoluto médio, distância de Wasserstein relativa ao
  desvio padrão, correlação peso x altura antes/depois.
Diagnósticos — código raro sobe na hierarquia, k global ou por sexo x ciclo
  % de códigos e de pares pessoa-código generalizados.
l-diversidade — sobre as classes do núcleo publicado
  % de classes (e de pessoas) em que todos os membros têm a mesma condição
  sensível (ataque de homogeneidade).

Sem `--rapido`, roda k em {2, 3, 5, 10, 15, 20, 30}. Só agregado é gravado.
"""

from __future__ import annotations

import argparse
import time
from datetime import date

import numpy as np
import pandas as pd
import _kanon as K
import _populacao as P
from _conexao import conectar, gravar, titulo

KS = (2, 3, 5, 10, 15, 20, 30)
# Variante escolhida: corte por ciclo de vida. m=2 e "sem ciclo" ficam como
# referência da fronteira.
VARIANTES_NUCLEO = {
    "ciclo, m=1": dict(m=1, por_ciclo=True),
    "ciclo, m=2": dict(m=2, por_ciclo=True),
    "sem ciclo, m=1": dict(m=1, por_ciclo=False),
}
FAIXAS = {"<2": (0, 1), "2-9": (2, 9), "10-19": (10, 19), "20-59": (20, 59), "60+": (60, 200)}
# Modelo de ameaça (decisão de 07/10/2026): o atacante conhece sexo,
# nascimento, equipe, tercil, raça/cor, escolaridade e estado civil.
# Os demais QI ficam fora do k, com valor raro recodificado.
FORA_NUCLEO = ["mun_nasc", "mun_resid", "ocupacao", "nacionalidade", "orient_sexual", "ident_genero"]
RECODIFICAR = ["mun_nasc", "mun_resid", "ocupacao"]
SUPRIMIVEIS = [c for c, _ in K.SUPRIMIVEIS]
NUCLEO_PUB = ["sexo_pub", "equipe_pub", *[f"{c}_pub" for c in SUPRIMIVEIS], "dt_nasc_pub"]
VARS_ANTRO = ["peso", "altura", "imc", "perimetro_cefalico", "altura_uterina"]


def medir_nucleo(pes: pd.DataFrame, r: pd.DataFrame, k: int, primeira_medicao: pd.Series) -> dict:
    cl = K.classes(r, NUCLEO_PUB)
    a = r["desloc_dias"].abs()
    out = {
        "k_min": int(cl.min()),
        "pct_equipe_suprimida": round(100 * float(r["equipe_suprimida"].mean()), 2),
        # % dos que tinham o atributo preenchido e o perderam
        "pct_suprimido": {
            c: round(100 * float(r[f"{c}_suprimido"].sum() / max(1, r[c].notna().sum())), 2)
            for c in SUPRIMIVEIS
        },
        "desloc": {},
    }
    for rot, (lo, hi) in FAIXAS.items():
        sel = pes["idade"].between(lo, hi)
        out["desloc"][rot] = {"mediana": float(a[sel].median()), "p95": float(a[sel].quantile(0.95))}
    pm = r["id"].map(primeira_medicao)
    tem = pm.notna()
    out["pct_nasc_depois_1a_medicao"] = round(100 * float((r.loc[tem, "dt_nasc_pub"] > pm[tem]).mean()), 2)
    return out


def medir_fora(pes: pd.DataFrame, r: pd.DataFrame, k: int) -> dict:
    pub = r[["id", *NUCLEO_PUB]].merge(pes[["id", *FORA_NUCLEO]], on="id")
    recod = {}
    for col in RECODIFICAR:
        novo = K.raros_para_outro(pub[col], pub["id"], k)
        recod[col] = round(100 * float((pub[col].notna() & novo.isna()).sum() / max(1, pub[col].notna().sum())), 2)
        pub[col] = novo
    cl = K.classes(pub, NUCLEO_PUB + FORA_NUCLEO)
    return {
        "pct_recodificado": recod,
        "risco_residual": {
            "pct_unicos": round(100 * float((cl == 1).mean()), 2),
            "pct_menor_k": round(100 * float((cl < k).mean()), 2),
        },
    }


def wasserstein(a: pd.Series, b: pd.Series) -> float:
    """W1 entre duas amostras do mesmo tamanho: média |ordenada(a) - ordenada(b)|."""
    return float(np.mean(np.abs(np.sort(a.to_numpy()) - np.sort(b.to_numpy()))))


def medir_antro(med: pd.DataFrame, k: int) -> dict:
    out = {}
    pub = {}
    for var in VARS_ANTRO:
        ok = med[var].notna()
        novo, info = K.antropometria(med[var], med["id"], k)
        pub[var] = novo
        orig, trat = med.loc[ok, var], novo[ok]
        dp = float(orig.std()) or 1.0
        out[var] = {
            "n": int(ok.sum()),
            "blocos": len(set(info["mapa"].values())),
            "erro_abs_medio": round(float((orig - trat).abs().mean()), 3),
            "wasserstein_rel_dp": round(wasserstein(orig, trat) / dp, 4),
        }
    ambos = med["peso"].notna() & med["altura"].notna()
    out["corr_peso_altura"] = {
        "original": round(float(np.corrcoef(med.loc[ambos, "peso"], med.loc[ambos, "altura"])[0, 1]), 4),
        "tratado": round(float(np.corrcoef(pub["peso"][ambos], pub["altura"][ambos])[0, 1]), 4),
    }
    return out


def medir_diag(diag: pd.DataFrame, pes: pd.DataFrame, k: int) -> dict:
    ctx = pes[["id"]].assign(ctx=pes["sexo"].astype(str) + "|" + pes["ciclo"].astype(str))
    out = {}
    for nome, contexto in (("global", None), ("sexo x ciclo", ctx)):
        d = K.diagnosticos(diag, contexto, k)
        gen = d["publicado"] != d["codigo"]
        codigos = d.groupby(["sistema", "codigo"])["nivel"].max()
        out[nome] = {
            "pct_codigos_generalizados": round(100 * float((codigos > 0).mean()), 2),
            "pct_pares_generalizados": round(100 * float(gen.mean()), 2),
            "pct_pessoas_afetadas": round(100 * float(d.loc[gen, "id"].nunique() / d["id"].nunique()), 2),
            "codigos_publicados": int(d.groupby("sistema")["publicado"].nunique().sum()),
        }
    return out


def medir_ldiv(r: pd.DataFrame, sens: pd.DataFrame) -> dict:
    cl = r[["id", *NUCLEO_PUB]].copy()
    cl["classe"] = cl[NUCLEO_PUB].astype(str).agg("|".join, axis=1)
    tam = cl.groupby("classe")["id"].size()
    out = {"_classes": int(len(tam))}
    for cat, g in sens.groupby("sensivel"):
        com = cl[cl["id"].isin(g["id"])].groupby("classe")["id"].size()
        homog = com[com == tam.reindex(com.index)]
        maioria = com[com >= 0.5 * tam.reindex(com.index)]
        out[cat] = {
            # pessoas da população com a condição: base para as frações expostas
            "pessoas_com_condicao": int(com.sum()),
            "classes_homogeneas": int(len(homog)),
            "pessoas_em_classe_homogenea": int(homog.sum()),
            "classes_com_maioria": int(len(maioria)),
            "pessoas_em_classe_com_maioria": int(maioria.sum()),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--referencia", default=date.today().isoformat())
    ap.add_argument("--rapido", action="store_true", help="só k em {5, 10, 20}")
    args = ap.parse_args()
    ks = (5, 10, 20) if args.rapido else KS

    conn = conectar()
    titulo("02 - varredura de k")
    pes = P.pessoas(conn, date.fromisoformat(args.referencia), apenas_ativos=False)
    diag = P.diagnosticos(conn)
    med = P.medicoes(conn)
    sens = K.sensiveis_por_pessoa(diag)
    primeira = med.groupby("id")["dt_medicao"].min()
    print(f"  pessoas publicadas: {len(pes):,}  medições: {len(med):,}  "
          f"pares pessoa-diagnóstico: {len(diag):,}")

    resultados = []
    for k in ks:
        t = time.time()
        linha = {"k": k, "nucleo": {}, "antropometria": medir_antro(med, k),
                 "diagnosticos": medir_diag(diag, pes, k)}
        for nome, kw in VARIANTES_NUCLEO.items():
            r = K.nucleo_adaptativo(pes, k, **kw)
            linha["nucleo"][nome] = {
                **medir_nucleo(pes, r, k, primeira),
                **medir_fora(pes, r, k),
                "l_diversidade": medir_ldiv(r, sens),
            }
        resultados.append(linha)
        print(f"\n  k = {k}  ({time.time() - t:.0f}s)")
        for nome, n in linha["nucleo"].items():
            d = n["desloc"]
            sp = n["pct_suprimido"]
            print(f"    núcleo [{nome:14}] sup: est.civil {sp['estado_civil']:5.1f}% escol "
                  f"{sp['escolaridade_nivel']:5.1f}% raça {sp['raca_cor']:5.1f}% tercil "
                  f"{sp['tercil']:5.1f}%  desloc. <2a {d['<2']['mediana']:4.0f}d  "
                  f"20-59 {d['20-59']['mediana']:4.0f}d  60+ {d['60+']['mediana']:4.0f}d  "
                  f"residual únicos {n['risco_residual']['pct_unicos']:5.2f}%")
        a = linha["antropometria"]
        print(f"    antropometria: peso W/dp {a['peso']['wasserstein_rel_dp']:.3f}, altura "
              f"{a['altura']['wasserstein_rel_dp']:.3f}; corr peso-altura "
              f"{a['corr_peso_altura']['original']:.3f} -> {a['corr_peso_altura']['tratado']:.3f}")
        for nome, d in linha["diagnosticos"].items():
            print(f"    diagnósticos [{nome:12}] códigos generalizados {d['pct_codigos_generalizados']:5.1f}%  "
                  f"pares {d['pct_pares_generalizados']:5.1f}%  pessoas afetadas {d['pct_pessoas_afetadas']:5.1f}%")

    gravar("02_varredura_k", {"referencia": args.referencia, "pessoas": len(pes), "resultados": resultados})


if __name__ == "__main__":
    main()
