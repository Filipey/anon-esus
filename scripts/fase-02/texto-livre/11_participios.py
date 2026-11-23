"""Análise 11 - palavras terminadas em -ado, -ada, -ados, -adas.

Pedido com o exemplo "menopausada": particípio e adjetivo que descrevem o
estado do paciente (orientada, hidratado, encaminhada...). Conta toda palavra
de 5 letras ou mais com essa terminação (abaixo disso é "nada", "cada",
"lado", "dado"). Palavra agrupada sem acento; a grafia exibida é a mais comum.

Nem toda terminação é particípio: `SUBSTANTIVOS` lista os casos frequentes
que são substantivo (pomada, fígado, cunhada, entrada...). O CSV traz todas,
com a coluna `substantivo`; as figuras mostram só particípio/adjetivo.

Saída: `terminacoes.csv` e figuras
- `11a_mais_frequentes` (6x4): top `--top` palavras;
- `11b_terminacoes` (4x3): # ocorrências por terminação;
- `11c_por_campo` (4x3): # ocorrências por 1.000 palavras, por campo.

Uso: 11_participios.py [--top 20] [--campos ...] [--distintos]"""

import re
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from _corpus import (COR, COR_UNICA, GRANDE, PEQUENA, ROTULO, argumentos, barras_horizontais,
                     carrega, estilo, figura, milhar, pasta_saida, salvar, sem_acento, tokens)

TERMINACAO = re.compile(r"(ado|ada|ados|adas)$")
SUBSTANTIVOS = {
    "pomada", "pomadas", "figado", "cunhado", "cunhada", "cunhados", "namorado", "namorada",
    "entrada", "entradas", "jornada", "camada", "camadas", "salada", "saladas", "mercado",
    "advogado", "advogada", "soldado", "telhado", "teclado", "senado", "machado", "pecado",
    "chegada", "parada", "estrada", "estradas", "morada", "temporada", "madrugada", "risada",
    "colherada", "colheradas", "caminhada", "caminhadas", "golada", "goladas", "dourado", "dourada", "fachada", "sacada",
    "calcada", "enxada", "cebolada", "feijoada", "limonada", "marmelada", "empregado",
    "empregada", "delegado", "delegada", "agrado", "prado", "gado", "bocado", "bocados",
    "quadrado", "quadrados", "legado", "condado", "reinado", "mandado", "recado", "recados",
    "cuidado", "cuidados", "resultado", "resultados", "estado", "estados", "passado",
    "atestado", "atestados", "mestrado", "doutorado", "comunicado", "certificado",
}
# "cuidado", "resultado", "estado", "atestado"... são particípios de origem,
# mas no texto clínico funcionam como substantivo ("resultado do exame").


def main() -> None:
    p = argumentos(__doc__.splitlines()[0])
    p.add_argument("--top", type=int, default=20, help="palavras na figura")
    args = p.parse_args()
    estilo()
    df = carrega(args.entrada, args.campos, args.distintos)
    pasta = pasta_saida("11_participios")

    ocorr, textos = Counter(), Counter()
    por_campo = defaultdict(Counter)
    palavras_campo = Counter()
    grafia = defaultdict(Counter)
    for campo, texto in zip(df["campo"], df["texto"]):
        toks = tokens(texto)
        palavras_campo[campo] += len(toks)
        vistos = set()
        for t in toks:
            n = sem_acento(t)
            if len(n) >= 5 and TERMINACAO.search(n):
                grafia[n][t] += 1
                ocorr[n] += 1
                por_campo[campo][n] += 1
                vistos.add(n)
        textos.update(vistos)

    campos = list(dict.fromkeys(df["campo"]))
    tab = pd.DataFrame([{
        "palavra": grafia[n].most_common(1)[0][0], "chave": n,
        "terminacao": TERMINACAO.search(n).group(1), "substantivo": n in SUBSTANTIVOS,
        "ocorrencias": v, "textos": textos[n],
        **{f"ocorr_{c}": por_campo[c][n] for c in campos}} for n, v in ocorr.most_common()])
    tab.to_csv(pasta / "terminacoes.csv", sep=";", index=False, encoding="utf-8-sig")
    part = tab[~tab["substantivo"]]
    print(f"{len(tab)} palavras distintas ({len(part)} particípio/adjetivo); "
          f"{part['ocorrencias'].sum()} ocorrências de particípio/adjetivo")

    # a. mais frequentes
    top = part.head(args.top)
    barras_horizontais(pasta, "11a_mais_frequentes", list(top["palavra"]), list(top["ocorrencias"]),
                       "# ocorrências", GRANDE, COR_UNICA)

    # b. por terminação
    fig, ax = figura(PEQUENA)
    ordem = ["ado", "ada", "ados", "adas"]
    soma = part.groupby("terminacao")["ocorrencias"].sum().reindex(ordem, fill_value=0)
    distintas = part.groupby("terminacao").size().reindex(ordem, fill_value=0)
    barras = ax.bar([f"-{t}" for t in ordem], soma, color=COR_UNICA, width=0.6)
    for b, d in zip(barras, distintas):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{d} palavras",
                ha="center", va="bottom", fontsize=8, color="0.25")
    ax.set_ylabel("# ocorrências")
    milhar(ax, "y")
    ax.margins(y=0.12)
    ax.grid(axis="x", visible=False)
    salvar(fig, pasta, "11b_terminacoes")

    # c. taxa por campo
    fig, ax = figura(PEQUENA)
    taxa = [1000 * part[f"ocorr_{c}"].sum() / max(palavras_campo[c], 1) for c in campos]
    ax.bar(range(len(campos)), taxa, color=[COR[c] for c in campos], width=0.65)
    ax.set_xticks(range(len(campos)), [ROTULO[c] for c in campos], rotation=35, ha="right")
    ax.set_ylabel("# por 1.000 palavras")
    ax.grid(axis="x", visible=False)
    salvar(fig, pasta, "11c_por_campo")


if __name__ == "__main__":
    main()
