"""Levantamento 03 - figuras a partir do 00_inventario e do 01_caracterizacao.

Só agregado: nomes de coluna e contagens, nenhum texto. Grava PDF e PNG em
`resultados/figuras_<ts>/`.

1. colunas textuais por classe e família (tb/ta/tl/rl);
2. volume de células das colunas de texto livre (top N), com a fração HTML;
3. distribuição do tamanho (p50/p95/máx) das colunas de texto livre (top N);
4. % de células com cada tipo de dado pessoal, por coluna (heatmap, top N);
5. histograma agregado de número de palavras;
6. tags HTML mais frequentes no agregado.
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from _conexao import RAIZ, RESULTADOS, ler
from _texto import GRUPOS, grupo

sys.path.insert(0, str(RAIZ / "scripts" / "plots"))
from _common import COLOR_PRIMARY, COLOR_RISK, COLOR_SECONDARY, set_latex_style  # noqa: E402

TOP = 30


def salvar(fig, pasta: Path, nome: str) -> None:
    fig.savefig(pasta / f"{nome}.pdf")
    fig.savefig(pasta / f"{nome}.png")
    plt.close(fig)
    print(f"  {nome}")


def rotulo(df: pd.DataFrame) -> pd.Series:
    return df["tabela"] + "." + df["coluna"]


def main() -> None:
    set_latex_style()
    inv = pd.DataFrame(ler("00_inventario")["colunas"])
    car_raw = ler("01_caracterizacao")
    car = pd.DataFrame(car_raw["colunas"])
    pasta = RESULTADOS / f"figuras_{datetime.now():%Y%m%d_%H%M%S}"
    pasta.mkdir(parents=True)
    print(f"Figuras em {pasta}")

    # 1. classe x família
    tab = inv.pivot_table(index="classe", columns="familia", values="coluna",
                          aggfunc="count", fill_value=0)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    tab.plot.barh(stacked=True, ax=ax, colormap="cividis", width=0.7)
    ax.set_xlabel("colunas")
    ax.set_ylabel("")
    ax.set_title("Colunas textuais por classe e família de tabela")
    salvar(fig, pasta, "01_classe_familia")

    livre = inv[inv["classe"] == "texto_livre"].sort_values("preenchidas", ascending=False).copy()
    livre["grupo"] = [grupo(t, c) for t, c in zip(livre["tabela"], livre["coluna"])]

    # 1b. texto livre por grupo: colunas, células e células com HTML
    por_grupo = livre.groupby("grupo").agg(
        colunas=("coluna", "count"), celulas=("preenchidas", "sum"), html=("n_html", "sum")
    ).reindex([g for g in GRUPOS if g in set(livre["grupo"])])
    fig, axes = plt.subplots(1, 2, figsize=(9, 3))
    axes[0].barh(por_grupo.index, por_grupo["colunas"], color=COLOR_PRIMARY)
    axes[0].set_xlabel("colunas")
    axes[1].barh(por_grupo.index, por_grupo["celulas"], color=COLOR_PRIMARY, label="preenchidas")
    axes[1].barh(por_grupo.index, por_grupo["html"], color=COLOR_SECONDARY, label="com HTML")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("células (escala log)")
    axes[1].legend(loc="lower right", fontsize=7)
    axes[1].set_yticklabels([])
    fig.suptitle("Colunas classificadas como texto livre, por grupo")
    salvar(fig, pasta, "01b_grupos")

    livre = livre[livre["grupo"].isin(set(car.get("grupo", pd.Series(["clinico"]))))]
    top = livre.head(TOP).iloc[::-1]

    # 2. volume + fração HTML
    fig, ax = plt.subplots(figsize=(7, 0.25 * len(top) + 1))
    y = rotulo(top)
    ax.barh(y, top["preenchidas"], color=COLOR_PRIMARY, label="preenchidas")
    ax.barh(y, top["n_html"], color=COLOR_SECONDARY, label="com HTML")
    ax.set_xscale("log")
    ax.set_xlabel("células (escala log)")
    ax.legend(loc="lower right")
    ax.set_title(f"Colunas de texto livre com mais células (top {len(top)})")
    ax.tick_params(axis="y", labelsize=6)
    salvar(fig, pasta, "02_volume_html")

    # 3. tamanhos
    fig, ax = plt.subplots(figsize=(7, 0.25 * len(top) + 1))
    ax.hlines(y, top["tam_p50"], top["tam_max"], color="0.75", lw=1)
    ax.scatter(top["tam_p50"], y, color=COLOR_PRIMARY, s=12, label="p50", zorder=3)
    ax.scatter(top["tam_p95"], y, color=COLOR_SECONDARY, s=12, label="p95", zorder=3)
    ax.scatter(top["tam_max"], y, color=COLOR_RISK, s=12, label="máx", zorder=3)
    ax.set_xscale("log")
    ax.set_xlabel("caracteres (escala log)")
    ax.legend(loc="lower right")
    ax.set_title("Tamanho do texto por coluna")
    ax.tick_params(axis="y", labelsize=6)
    salvar(fig, pasta, "03_tamanhos")

    # 4. heatmap de dado pessoal
    pii = pd.DataFrame(car["pii_pct_celulas"].tolist()).fillna(0)
    pii.index = rotulo(car)
    pii = pii.loc[car.sort_values("celulas", ascending=False).head(TOP).pipe(rotulo)]
    if not pii.empty:
        fig, ax = plt.subplots(figsize=(8, 0.25 * len(pii) + 1.5))
        sns.heatmap(pii * 100, ax=ax, cmap="Reds", annot=True, fmt=".0f",
                    annot_kws={"size": 5}, cbar_kws={"label": "% das células"})
        ax.set_title("Células com possível dado pessoal (regex/léxico)")
        ax.tick_params(axis="y", labelsize=6)
        ax.tick_params(axis="x", labelsize=7, rotation=45)
        salvar(fig, pasta, "04_dado_pessoal")

    # 5. palavras (agregado)
    hist = Counter()
    for h in car["palavras_hist"]:
        hist.update(h)
    ordem = [k for k in ("<=1", "<=2", "<=5", "<=10", "<=20", "<=50", "<=100",
                         "<=200", "<=500", ">500") if k in hist]
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.bar(ordem, [hist[k] for k in ordem], color=COLOR_PRIMARY)
    ax.set_xlabel("palavras por célula (sem HTML)")
    ax.set_ylabel("células")
    ax.set_title("Tamanho do texto livre em palavras, todas as colunas")
    salvar(fig, pasta, "05_palavras")

    # 6. tags HTML
    tags = Counter()
    for t in car["tags"]:
        tags.update(t)
    if tags:
        comuns = tags.most_common(20)[::-1]
        fig, ax = plt.subplots(figsize=(6, 0.25 * len(comuns) + 1))
        ax.barh([k for k, _ in comuns], [v for _, v in comuns], color=COLOR_SECONDARY)
        ax.set_xlabel("ocorrências em células")
        ax.set_title("Tags HTML mais frequentes")
        salvar(fig, pasta, "06_tags_html")


if __name__ == "__main__":
    main()
