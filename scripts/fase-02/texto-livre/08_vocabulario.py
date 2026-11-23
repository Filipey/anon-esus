"""Análise 08 - palavras únicas (vocabulário) por campo.

Por campo e no total: # tokens, # palavras únicas (tipos), # hapax (palavra
que aparece uma vez só) e a razão tipo/token (TTR); por texto, # palavras
únicas e TTR (só textos com >= 10 tokens, porque TTR de texto curto é ~1).
Tudo com stopwords incluídas: aqui o interesse é a riqueza do vocabulário.

Saída: `vocabulario.csv` (resumo), `frequencia_<campo>.csv` (cada palavra
única com # ocorrências e # textos em que aparece) e figuras
- `08a_zipf` (6x4): frequência x posto, log-log, por campo;
- `08b_vocabulario` (4x3): # palavras únicas por campo, com a parte hapax;
- `08c_unicas_por_texto` (6x4): boxplot de # palavras únicas por texto.

Uso: 08_vocabulario.py [--campos ...] [--distintos] [--entrada pasta]"""

from collections import Counter

import numpy as np
import pandas as pd

from _corpus import (COR, GRANDE, PEQUENA, ROTULO, argumentos, carrega, estilo, figura,
                     milhar, pasta_saida, salvar, tokens)


def main() -> None:
    args = argumentos(__doc__.splitlines()[0]).parse_args()
    estilo()
    df = carrega(args.entrada, args.campos, args.distintos)
    df["tokens"] = [tokens(t) for t in df["texto"]]
    pasta = pasta_saida("08_vocabulario")

    linhas, freq_por_campo = [], {}
    grupos = list(df.groupby("campo", sort=False)) + [("todos", df)]
    for campo, g in grupos:
        ocorr = Counter(t for toks in g["tokens"] for t in toks)
        docs = Counter(t for toks in g["tokens"] for t in set(toks))
        freq_por_campo[campo] = ocorr
        n_tok = sum(ocorr.values())
        hapax = sum(1 for v in ocorr.values() if v == 1)
        unicas_texto = g["tokens"].map(lambda t: len(set(t)))
        longos = g["tokens"][g["tokens"].map(len) >= 10]
        linhas.append({
            "campo": campo, "textos": len(g), "tokens": n_tok, "palavras_unicas": len(ocorr),
            "hapax": hapax, "hapax_pct": 100 * hapax / max(len(ocorr), 1),
            "ttr_global": len(ocorr) / max(n_tok, 1),
            "unicas_por_texto_media": unicas_texto.mean(),
            "unicas_por_texto_mediana": unicas_texto.median(),
            "ttr_por_texto_media_10mais": longos.map(lambda t: len(set(t)) / len(t)).mean(),
        })
        pd.DataFrame({"palavra": list(ocorr), "ocorrencias": list(ocorr.values()),
                      "textos": [docs[p] for p in ocorr]}) \
            .sort_values("ocorrencias", ascending=False) \
            .to_csv(pasta / f"frequencia_{campo}.csv", sep=";", index=False, encoding="utf-8-sig")
    tab = pd.DataFrame(linhas)
    tab.round(4).to_csv(pasta / "vocabulario.csv", sep=";", index=False, encoding="utf-8-sig")
    print(tab[["campo", "tokens", "palavras_unicas", "hapax_pct", "ttr_global"]].to_string(index=False))

    campos = [c for c in tab["campo"] if c != "todos"]

    # a. Zipf
    fig, ax = figura(GRANDE)
    for campo in campos:
        f = np.sort(np.fromiter(freq_por_campo[campo].values(), dtype=float))[::-1]
        ax.plot(np.arange(1, len(f) + 1), f, color=COR[campo], lw=1.5, label=ROTULO[campo])
    ax.set_xscale("log")
    ax.set_yscale("log")
    milhar(ax)
    milhar(ax, "y")
    ax.set_xlabel("posto da palavra (escala log)")
    ax.set_ylabel("# ocorrências (escala log)")
    ax.legend(loc="upper right")
    salvar(fig, pasta, "08a_zipf")

    # b. # palavras únicas, parte hapax mais clara
    fig, ax = figura(PEQUENA)
    t = tab.set_index("campo").loc[campos]
    x = np.arange(len(campos))
    cores = [COR[c] for c in campos]
    ax.bar(x, t["palavras_unicas"] - t["hapax"], 0.65, color=cores)
    ax.bar(x, t["hapax"], 0.65, bottom=t["palavras_unicas"] - t["hapax"], color=cores, alpha=0.4)
    ax.set_xticks(x, [ROTULO[c] for c in campos], rotation=35, ha="right")
    ax.set_ylabel("# palavras únicas")
    milhar(ax, "y")
    ax.grid(axis="x", visible=False)
    from matplotlib.patches import Patch
    ax.legend([Patch(facecolor="0.35"), Patch(facecolor="0.35", alpha=0.4)],
              ["2+ ocorrências", "hapax (1 ocorrência)"])
    salvar(fig, pasta, "08b_vocabulario")

    # c. # palavras únicas por texto
    fig, ax = figura(GRANDE)
    dados = [df.loc[df["campo"] == c, "tokens"].map(lambda t: len(set(t))) for c in campos][::-1]
    dados = [d[d > 0] for d in dados]
    caixa = ax.boxplot(dados, orientation="horizontal", showfliers=False, widths=0.6, patch_artist=True,
                       medianprops={"color": "0.1", "lw": 1.4})
    for patch, campo in zip(caixa["boxes"], campos[::-1]):
        patch.set(facecolor=COR[campo], alpha=0.75, edgecolor="0.3")
    ax.set_yticks(range(1, len(campos) + 1), [ROTULO[c] for c in campos[::-1]])
    ax.set_xscale("log")
    milhar(ax)
    ax.set_xlabel("# palavras únicas por texto (escala log)")
    ax.grid(axis="y", visible=False)
    salvar(fig, pasta, "08c_unicas_por_texto")


if __name__ == "__main__":
    main()
