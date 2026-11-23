"""Corpus, tokenização e estilo de figura compartilhados pelas análises 07-14.

As análises leem o texto já pseudo-anonimizado e sem HTML (etapas 04-06), não
o banco: é o mesmo texto entregue aos parceiros, e tabela de n-grama ou de
contexto pode ir para artigo sem expor nome real. Saída em
`resultados/<análise>_<timestamp>/` (no `.gitignore`).

Campos (texto digitado pelo profissional):

| campo          | arquivo                                   | coluna          |
|----------------|-------------------------------------------|-----------------|
| subjetivo      | 06_soap_sem_html.csv                      | subjetivo       |
| objetivo       | 06_soap_sem_html.csv                      | objetivo        |
| avaliacao      | 06_soap_sem_html.csv                      | avaliacao       |
| plano          | 06_soap_sem_html.csv                      | plano           |
| recomendacao   | 07_receitas_com_contexto_sem_html.csv     | recomendacao    |
| atestado       | 05_atestados_sem_html.csv                 | texto_atestado  |

Ficam de fora a posologia (montada pelo sistema a partir dos campos da
receita) e a dose (curta, quase estruturada)."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

AQUI = Path(__file__).resolve().parent
RESULTADOS = AQUI / "resultados"
csv.field_size_limit(10**9)

CAMPOS = {
    "subjetivo": ("06_soap_sem_html.csv", "subjetivo"),
    "objetivo": ("06_soap_sem_html.csv", "objetivo"),
    "avaliacao": ("06_soap_sem_html.csv", "avaliacao"),
    "plano": ("06_soap_sem_html.csv", "plano"),
    "recomendacao": ("07_receitas_com_contexto_sem_html.csv", "recomendacao"),
    "atestado": ("05_atestados_sem_html.csv", "texto_atestado"),
}
ROTULO = {"subjetivo": "Subjetivo", "objetivo": "Objetivo", "avaliacao": "Avaliação",
          "plano": "Plano", "recomendacao": "Recomendação", "atestado": "Atestado",
          "todos": "Todos"}
# Uma cor fixa por campo em todas as figuras (paleta de `experimentos/k-anonimato-dp`,
# validada para daltonismo, mais um sexto tom).
COR = dict(zip(CAMPOS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6f5aa8"]))
COR_UNICA = "#2E4057"          # série única (`scripts/plots/_common.py`)

GRANDE = (6, 4)                # tamanhos de figura permitidos (polegadas)
PEQUENA = (4, 3)

# Token: sequência de letras (com acento). Hífen e número separam, então
# "recusa-se" vira "recusa se" e "1/2 comprimido" vira "comprimido".
TOKEN = re.compile(r"[a-zà-öø-ÿ]+")
# Negação não é stopword aqui: em texto clínico ela carrega o sentido
# ("sem febre", "não aderiu", "nega dor").
NEGACAO = {"não", "nao", "nem", "nunca", "sem", "nada", "nenhum", "nenhuma", "jamais"}


def stopwords() -> set[str]:
    from spacy.lang.pt.stop_words import STOP_WORDS
    return {w for w in STOP_WORDS if w not in NEGACAO}


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def tokens(texto: str) -> list[str]:
    return TOKEN.findall(texto.lower())


# Fim de frase ou de bloco (o " | " vem da limpeza do HTML): n-grama e contexto
# não atravessam, senão "nega. | Febre" viraria o bigrama "nega febre".
FIM_DE_FRASE = re.compile(r"[.;:!?|\n]+")


def segmentos(texto: str) -> list[list[str]]:
    """Tokens de cada frase/bloco do texto, para montar n-grama."""
    return [t for t in (tokens(s) for s in FIM_DE_FRASE.split(texto)) if t]


def argumentos(descricao: str) -> argparse.ArgumentParser:
    """Opções comuns; cada análise acrescenta as suas e chama `parse_args()`."""
    p = argparse.ArgumentParser(description=descricao)
    p.add_argument("--entrada", type=Path, default=RESULTADOS,
                   help="pasta com os CSVs sem HTML (padrão: resultados/)")
    p.add_argument("--campos", nargs="+", choices=list(CAMPOS), default=list(CAMPOS))
    p.add_argument("--distintos", action="store_true",
                   help="usa só textos distintos de cada campo (tira modelo repetido)")
    return p


def carrega(entrada: Path, campos: list[str], distintos: bool = False) -> pd.DataFrame:
    """Uma linha por texto não vazio: campo, paciente_id, texto."""
    partes, lidos = [], {}
    for campo in campos:
        arquivo, coluna = CAMPOS[campo]
        if arquivo not in lidos:
            lidos[arquivo] = pd.read_csv(entrada / arquivo, sep=";", dtype=str,
                                         keep_default_na=False, encoding="utf-8-sig")
        df = lidos[arquivo]
        t = df[coluna].str.strip()
        sub = pd.DataFrame({"campo": campo, "paciente_id": df["paciente_id"], "texto": t})[t != ""]
        if distintos:
            sub = sub.drop_duplicates("texto")
        partes.append(sub)
    return pd.concat(partes, ignore_index=True)


def pasta_saida(nome: str) -> Path:
    pasta = RESULTADOS / f"{nome}_{datetime.now():%Y%m%d_%H%M%S}"
    pasta.mkdir(parents=True)
    print(f"Saída em {pasta}")
    return pasta


def estilo() -> None:
    """Visual LaTeX (serifa Computer Modern) sem exigir LaTeX instalado.

    Usa CMU Serif (Computer Modern Unicode, com acento) se estiver instalada,
    senão DejaVu Serif: a `cmr10` do matplotlib não tem "ç", "ã", "é"."""
    disponiveis = {f.name for f in font_manager.fontManager.ttflist}
    serif = [f for f in ("CMU Serif", "Latin Modern Roman") if f in disponiveis] + ["DejaVu Serif"]
    # vírgula decimal nos eixos e nas barras de cor, se o sistema tiver pt_BR
    import locale
    for nome in ("pt_BR.UTF-8", "pt_BR.utf8"):
        try:
            locale.setlocale(locale.LC_NUMERIC, nome)
            plt.rcParams["axes.formatter.use_locale"] = True
            break
        except locale.Error:
            pass
    plt.rcParams.update({
        "font.family": "serif", "font.serif": serif, "mathtext.fontset": "cm",
        "font.size": 11, "axes.labelsize": 12, "xtick.labelsize": 10, "ytick.labelsize": 10,
        "legend.fontsize": 9, "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "0.3",
        "axes.linewidth": 0.8, "axes.grid": True, "grid.color": "0.88", "grid.linewidth": 0.6,
        "axes.axisbelow": True, "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
        "pdf.fonttype": 42,
    })


def figura(tamanho=GRANDE):
    assert tamanho in (GRANDE, PEQUENA), "figura fora dos tamanhos 6x4 / 4x3"
    return plt.subplots(figsize=tamanho)


def salvar(fig, pasta: Path, nome: str) -> None:
    fig.savefig(pasta / f"{nome}.pdf")
    fig.savefig(pasta / f"{nome}.png")
    plt.close(fig)
    print(f"  {nome}")


def milhar(ax, eixo: str = "x") -> None:
    """Separador de milhar com ponto, como no texto em português. Em eixo log,
    também troca "10^2" por "100" (só nas potências de 10)."""
    from matplotlib.ticker import FuncFormatter, NullFormatter
    f = FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".") if v >= 1 else f"{v:g}")
    a = ax.xaxis if eixo == "x" else ax.yaxis
    a.set_major_formatter(f)
    if a.get_scale() == "log":
        a.set_minor_formatter(NullFormatter())


def log_decimal(ax, eixo: str = "y") -> None:
    """Eixo log com valor por extenso e vírgula decimal ("0,01", "0,1", "1", "10")."""
    from matplotlib.ticker import FuncFormatter, NullFormatter
    a = ax.xaxis if eixo == "x" else ax.yaxis
    a.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    a.set_minor_formatter(NullFormatter())


def barras_horizontais(pasta: Path, nome: str, rotulos: list[str], valores: list[float],
                       xlabel: str, tamanho=GRANDE, cor: str = COR_UNICA) -> None:
    """Top-k em barras horizontais, maior em cima, com o valor na ponta."""
    fig, ax = figura(tamanho)
    y = range(len(rotulos))[::-1]
    ax.barh(list(y), valores, color=cor, height=0.7)
    ax.set_yticks(list(y), rotulos, fontsize=9 if tamanho == GRANDE else 8)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    milhar(ax)
    ax.margins(x=0.12)
    for yi, v in zip(y, valores):
        ax.text(v, yi, f" {v:,.0f}".replace(",", "."), va="center", fontsize=8, color="0.25")
    salvar(fig, pasta, nome)
