"""Análise 07 - tamanho do texto por campo.

Por campo: # textos, # textos distintos, e a distribuição de caracteres e de
palavras por texto (média, desvio, quartis, p95, máximo). Palavra = sequência
de letras (`_corpus.TOKEN`), então número e pontuação não contam.

Saída: `tamanho.csv` e figuras
- `07a_palavras_ecdf` (6x4): distribuição acumulada de # palavras por texto;
- `07b_palavras_box` (6x4): boxplot de # palavras por texto;
- `07c_textos_por_campo` (4x3): # textos e # textos distintos por campo.

Uso: 07_tamanho.py [--campos ...] [--distintos] [--entrada pasta]"""

import numpy as np
import pandas as pd

from _corpus import (COR, GRANDE, PEQUENA, ROTULO, argumentos, carrega, estilo, figura,
                     milhar, pasta_saida, salvar, tokens)


def resumo(serie: pd.Series) -> dict:
    return {"media": serie.mean(), "desvio": serie.std(), "p25": serie.quantile(.25),
            "mediana": serie.median(), "p75": serie.quantile(.75), "p95": serie.quantile(.95),
            "max": serie.max()}


def main() -> None:
    args = argumentos(__doc__.splitlines()[0]).parse_args()
    estilo()
    df = carrega(args.entrada, args.campos, args.distintos)
    df["caracteres"] = df["texto"].str.len()
    df["palavras"] = [len(tokens(t)) for t in df["texto"]]
    pasta = pasta_saida("07_tamanho")

    linhas = []
    for campo, g in df.groupby("campo", sort=False):
        linha = {"campo": campo, "textos": len(g), "textos_distintos": g["texto"].nunique()}
        for medida in ("caracteres", "palavras"):
            linha |= {f"{medida}_{k}": v for k, v in resumo(g[medida]).items()}
        linhas.append(linha)
    tab = pd.DataFrame(linhas)
    tab.round(2).to_csv(pasta / "tamanho.csv", sep=";", index=False, encoding="utf-8-sig")
    print(tab[["campo", "textos", "textos_distintos", "palavras_mediana", "palavras_p95"]]
          .to_string(index=False))

    campos = list(tab["campo"])
    com_palavra = df[df["palavras"] > 0]

    # a. ECDF de # palavras por texto
    fig, ax = figura(GRANDE)
    for campo in campos:
        x = np.sort(com_palavra.loc[com_palavra["campo"] == campo, "palavras"].to_numpy())
        ax.step(x, np.arange(1, len(x) + 1) / len(x) * 100, where="post",
                color=COR[campo], lw=1.6, label=ROTULO[campo])
    ax.set_xscale("log")
    milhar(ax)
    ax.set_xlabel("# palavras por texto (escala log)")
    ax.set_ylabel("% dos textos")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right")
    salvar(fig, pasta, "07a_palavras_ecdf")

    # b. boxplot de # palavras por texto (sem outlier; o p95 está na tabela)
    fig, ax = figura(GRANDE)
    dados = [com_palavra.loc[com_palavra["campo"] == c, "palavras"] for c in campos][::-1]
    caixa = ax.boxplot(dados, orientation="horizontal", showfliers=False, widths=0.6, patch_artist=True,
                       medianprops={"color": "0.1", "lw": 1.4})
    for patch, campo in zip(caixa["boxes"], campos[::-1]):
        patch.set(facecolor=COR[campo], alpha=0.75, edgecolor="0.3")
    ax.set_yticks(range(1, len(campos) + 1), [ROTULO[c] for c in campos[::-1]])
    ax.set_xscale("log")
    milhar(ax)
    ax.set_xlabel("# palavras por texto (escala log)")
    ax.grid(axis="y", visible=False)
    salvar(fig, pasta, "07b_palavras_box")

    # c. # textos e # distintos por campo
    fig, ax = figura(PEQUENA)
    x = np.arange(len(campos))
    ax.bar(x - 0.2, tab["textos"], 0.4, color=[COR[c] for c in campos], label="todos")
    ax.bar(x + 0.2, tab["textos_distintos"], 0.4, color=[COR[c] for c in campos], alpha=0.45,
           label="distintos")
    ax.set_xticks(x, [ROTULO[c] for c in campos], rotation=35, ha="right")
    ax.set_ylabel("# textos")
    milhar(ax, "y")
    ax.grid(axis="x", visible=False)
    # legenda em cinza: a cor da barra é do campo, o tom é que distingue
    from matplotlib.patches import Patch
    ax.legend([Patch(facecolor="0.35"), Patch(facecolor="0.35", alpha=0.45)],
              ["todos", "distintos"])
    salvar(fig, pasta, "07c_textos_por_campo")


if __name__ == "__main__":
    main()
