"""Análise 13 - atributos linguísticos do LFTK por campo.

Só os atributos `language="general"` do LFTK (141): contagens, médias por
frase e por palavra, razões tipo/token, variação e proporção de cada classe
gramatical (POS). Os de legibilidade e dificuldade de palavra ficam de fora:
são fórmulas e listas do inglês. O documento vem do spaCy `pt_core_news_md`.

O " | " da limpeza do HTML (fim de bloco) vira ". " antes do spaCy, para o
bloco contar como frase.

Custo: spaCy + LFTK fazem ~ centenas de textos/s; por isso o padrão é uma
amostra aleatória de `--amostra` textos por campo (semente fixa). `--amostra 0`
usa todos.

Saída: `lftk_textos.csv` (campo + os 141 atributos por texto; sem o texto),
`lftk_campos.csv` (média e mediana por campo) e figuras
- `13a_classes_gramaticais` (6x4): % das palavras em cada classe, por campo;
- `13b_<atributo>` (4x3): boxplot por campo de cada atributo de `FIGURAS`.

Uso: 13_lftk.py [--amostra 10000] [--processos 2] [--campos ...] [--distintos]"""

import re

import lftk
import numpy as np
import pandas as pd
import spacy

from _corpus import (CAMPOS, COR, GRANDE, PEQUENA, ROTULO, argumentos, carrega, estilo, figura,
                     pasta_saida, salvar)

FIGURAS = {
    "a_word_ps": "# palavras por frase",
    "a_char_pw": "# caracteres por palavra",
    "corr_ttr": "TTR corrigida",
    "t_sent": "# frases por texto",
}
CLASSES = {"noun": "substantivo", "verb": "verbo", "adj": "adjetivo", "adv": "advérbio",
           "pron": "pronome", "adp": "preposição", "det": "determinante", "num": "numeral",
           "propn": "nome próprio"}


def para_spacy(texto: str) -> str:
    """Fim de bloco vira fim de frase; texto quase todo em maiúscula vai para
    minúscula, senão o spaCy marca boa parte como nome próprio (PROPN)."""
    t = re.sub(r"(?<![.;:!?])\s\|\s", ". ", texto).replace(" | ", " ")
    letras = [c for c in t if c.isalpha()]
    if letras and sum(c.isupper() for c in letras) >= 0.8 * len(letras):
        t = t.lower()
    return t


def main() -> None:
    p = argumentos(__doc__.splitlines()[0])
    p.add_argument("--amostra", type=int, default=10000, help="textos por campo (0 = todos)")
    p.add_argument("--processos", type=int, default=2, help="processos do spaCy")
    args = p.parse_args()
    estilo()
    df = carrega(args.entrada, args.campos, args.distintos)
    if args.amostra:
        df = df.sample(frac=1, random_state=42).groupby("campo", sort=False).head(args.amostra)
        df = df.sort_values("campo", key=lambda s: s.map(list(CAMPOS).index), kind="stable")
    pasta = pasta_saida("13_lftk")
    atributos = [f["key"] for f in lftk.search_features(language="general", return_format="list_dict")]

    nlp = spacy.load("pt_core_news_md")
    docs = nlp.pipe((para_spacy(t) for t in df["texto"]), batch_size=256, n_process=args.processos)
    linhas = []
    for i, doc in enumerate(docs):
        ext = lftk.Extractor(docs=doc)
        ext.customize(round_decimal=4)
        linhas.append(ext.extract(features=atributos))
        if (i + 1) % 10000 == 0:
            print(f"  {i + 1}/{len(df)}")
    tab = pd.DataFrame(linhas)
    tab.insert(0, "campo", df["campo"].to_numpy())
    tab.to_csv(pasta / "lftk_textos.csv", sep=";", index=False, encoding="utf-8-sig")

    campos = list(dict.fromkeys(tab["campo"]))
    g = tab.groupby("campo", sort=False)[atributos]
    pd.concat({"media": g.mean(), "mediana": g.median()}, names=["medida", "campo"]) \
        .round(4).to_csv(pasta / "lftk_campos.csv", sep=";", encoding="utf-8-sig")

    # a. perfil de classes gramaticais: % das palavras (média de a_<pos>_pw)
    fig, ax = figura(GRANDE)
    perfil = tab.groupby("campo", sort=False)[[f"a_{c}_pw" for c in CLASSES]].mean().loc[campos] * 100
    x = np.arange(len(CLASSES))
    larg = 0.8 / len(campos)
    for k, campo in enumerate(campos):
        ax.bar(x - 0.4 + larg * (k + 0.5), perfil.loc[campo], larg, color=COR[campo],
               label=ROTULO[campo])
    ax.set_xticks(x, list(CLASSES.values()), rotation=35, ha="right")
    ax.set_ylabel("% das palavras")
    ax.grid(axis="x", visible=False)
    ax.legend(ncol=2)
    salvar(fig, pasta, "13a_classes_gramaticais")

    # b. um boxplot por atributo
    for atributo, rotulo in FIGURAS.items():
        fig, ax = figura(PEQUENA)
        dados = [tab.loc[tab["campo"] == c, atributo] for c in campos][::-1]
        caixa = ax.boxplot(dados, orientation="horizontal", showfliers=False, widths=0.6,
                           patch_artist=True, medianprops={"color": "0.1", "lw": 1.2})
        for patch, campo in zip(caixa["boxes"], campos[::-1]):
            patch.set(facecolor=COR[campo], alpha=0.75, edgecolor="0.3")
        ax.set_yticks(range(1, len(campos) + 1), [ROTULO[c] for c in campos[::-1]], fontsize=9)
        ax.set_xlabel(rotulo)
        ax.grid(axis="y", visible=False)
        salvar(fig, pasta, f"13b_{atributo}")
    print(f"{len(tab)} textos, {len(atributos)} atributos")


if __name__ == "__main__":
    main()
