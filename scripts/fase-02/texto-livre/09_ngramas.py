"""Análise 09 - unigramas, bigramas e trigramas mais frequentes por campo.

Como nos bigramas do ICWSM 2026 (`CountVectorizer(stop_words=...)`): tira as
stopwords (`_corpus.stopwords()`, que mantém a negação) e monta o n-grama
sobre o que sobra, dentro de cada frase/bloco (`_corpus.segmentos`). Conta
# ocorrências e # textos em que o n-grama aparece.

Saída: `ngramas_<campo>_<n>.csv` (top `--tabela`) e figuras
`09_<campo>_<n>gramas` (6x4, top `--top`) para cada campo, mais "todos".

Uso: 09_ngramas.py [--top 15] [--tabela 200] [--campos ...] [--distintos]"""

from collections import Counter

import pandas as pd

from _corpus import (COR, COR_UNICA, GRANDE, ROTULO, argumentos, barras_horizontais, carrega,
                     estilo, pasta_saida, segmentos, stopwords)

NOME = {1: "unigramas", 2: "bigramas", 3: "trigramas"}


def ngramas(toks: list[str], n: int) -> list[str]:
    return [" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)]


def main() -> None:
    p = argumentos(__doc__.splitlines()[0])
    p.add_argument("--top", type=int, default=15, help="n-gramas por figura")
    p.add_argument("--tabela", type=int, default=200, help="n-gramas por CSV")
    args = p.parse_args()
    estilo()
    pare = stopwords()
    df = carrega(args.entrada, args.campos, args.distintos)
    df["frases"] = [[[t for t in s if t not in pare and len(t) > 1] for s in segmentos(x)]
                    for x in df["texto"]]
    pasta = pasta_saida("09_ngramas")

    grupos = list(df.groupby("campo", sort=False)) + [("todos", df)]
    for campo, g in grupos:
        for n in (1, 2, 3):
            ocorr, textos = Counter(), Counter()
            for frases in g["frases"]:
                ng = [x for s in frases for x in ngramas(s, n)]
                ocorr.update(ng)
                textos.update(set(ng))
            top = ocorr.most_common(args.tabela)
            pd.DataFrame({"ngrama": [k for k, _ in top], "ocorrencias": [v for _, v in top],
                          "textos": [textos[k] for k, _ in top],
                          "pct_textos": [100 * textos[k] / len(g) for k, _ in top]}) \
                .round(3).to_csv(pasta / f"ngramas_{campo}_{n}.csv", sep=";", index=False,
                                 encoding="utf-8-sig")
            fig_top = top[:args.top]
            if fig_top:
                barras_horizontais(pasta, f"09_{campo}_{NOME[n]}", [k for k, _ in fig_top],
                                   [v for _, v in fig_top], "# ocorrências", GRANDE,
                                   COR.get(campo, COR_UNICA))
        print(f"  {ROTULO[campo]}: {len(g)} textos")


if __name__ == "__main__":
    main()
