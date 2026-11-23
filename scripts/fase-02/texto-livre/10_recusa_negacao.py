"""Análise 10 - combinações mais frequentes com os lemas recusar, rejeitar e negar.

Lema por lista explícita de flexões, não pelo lematizador do spaCy: o
`pt_core_news_md` toma "Nega" no início da frase ("Nega febre.") como nome
próprio e não lematiza. As formas saem de radical + desinência (todos os
tempos, particípio, gerúndio, com "neg-" -> "negu-" antes de "e") mais o
substantivo (recusa, rejeição, negação). O casamento é sem acento e em
minúscula; "recusa-se" vira "recusa se" na tokenização. "Negativo/negativa"
fica de fora ("negativo para malignidade" não é negar).

Para cada ocorrência, dentro da frase/bloco (`_corpus.segmentos`), com as
stopwords mantidas (o "se" de "recusa-se" importa):
- `direita_2`: forma + palavra seguinte ("recusou a");
- `direita_3`: forma + 2 seguintes ("recusou a vacina");
- `esquerda_2`: palavra anterior + forma ("paciente recusa");
- `conteudo`: forma + próxima palavra que não é stopword ("recusou vacina").

Saída: `formas.csv` (# ocorrências e # textos por forma e por campo),
`combinacoes_<lema>.csv` e figuras
- `10a_formas` (6x4): formas mais frequentes, cor por lema;
- `10b_<lema>_combinacoes` (6x4): top `--top` de `direita_3` por lema;
- `10c_<lema>_conteudo` (6x4): top `--top` de `conteudo` por lema;
- `10d_por_campo` (4x3): % dos textos de cada campo com cada lema.

Uso: 10_recusa_negacao.py [--top 15] [--campos ...] [--distintos]"""

from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from _corpus import (GRANDE, PEQUENA, ROTULO, argumentos, barras_horizontais, carrega, estilo,
                     figura, log_decimal, milhar, pasta_saida, salvar, segmentos, sem_acento,
                     stopwords)

DESINENCIAS = [
    "ar", "o", "a", "as", "amos", "ais", "am", "ei", "aste", "ou", "astes", "aram", "ava", "avas",
    "avamos", "aveis", "avam", "ara", "aras", "aramos", "areis", "arei", "aras", "ara", "aremos",
    "areis", "arao", "aria", "arias", "ariamos", "arieis", "ariam", "e", "es", "emos", "eis", "em",
    "asse", "asses", "assemos", "asseis", "assem", "armos", "ardes", "arem", "ando", "ado", "ada",
    "ados", "adas",
]


def formas(radical: str, gu: bool = False) -> set[str]:
    """radical + desinência; com `gu`, "g" vira "gu" antes de "e" (negue, neguei)."""
    return {radical + ("u" if gu and d.startswith("e") else "") + d for d in DESINENCIAS}


LEMAS = {
    "recusar": formas("recus"),
    "rejeitar": formas("rejeit") | {"rejeicao", "rejeicoes"},
    "negar": formas("neg", gu=True) | {"negacao", "negacoes"},
}
COR_LEMA = {"recusar": "#9E2A2B", "rejeitar": "#F18F01", "negar": "#2E4057"}
LEMA_DA_FORMA = {f: lema for lema, fs in LEMAS.items() for f in fs}


def main() -> None:
    p = argumentos(__doc__.splitlines()[0])
    p.add_argument("--top", type=int, default=15, help="combinações por figura")
    args = p.parse_args()
    estilo()
    pare = stopwords()
    df = carrega(args.entrada, args.campos, args.distintos)
    pasta = pasta_saida("10_recusa_negacao")

    ocorr = Counter()                                 # (lema, forma) -> #
    textos_forma = Counter()
    por_campo = defaultdict(Counter)                  # campo -> (lema, forma) -> #
    textos_lema_campo = defaultdict(Counter)          # campo -> lema -> # textos
    comb = {lema: defaultdict(Counter) for lema in LEMAS}   # lema -> tipo -> combinação -> #
    grafia = defaultdict(Counter)                     # forma sem acento -> grafias vistas

    for campo, texto in zip(df["campo"], df["texto"]):
        vistos_forma, vistos_lema = set(), set()
        for seg in segmentos(texto):
            norm = [sem_acento(t) for t in seg]
            for i, n in enumerate(norm):
                lema = LEMA_DA_FORMA.get(n)
                if not lema:
                    continue
                grafia[n][seg[i]] += 1
                ocorr[(lema, n)] += 1
                por_campo[campo][(lema, n)] += 1
                vistos_forma.add((lema, n))
                vistos_lema.add(lema)
                c = comb[lema]
                if i + 1 < len(seg):
                    c["direita_2"][f"{seg[i]} {seg[i + 1]}"] += 1
                if i + 2 < len(seg):
                    c["direita_3"][f"{seg[i]} {seg[i + 1]} {seg[i + 2]}"] += 1
                if i > 0:
                    c["esquerda_2"][f"{seg[i - 1]} {seg[i]}"] += 1
                prox = next((t for t in seg[i + 1:] if t not in pare and len(t) > 1), None)
                if prox:
                    c["conteudo"][f"{seg[i]} {prox}"] += 1
        textos_forma.update(vistos_forma)
        textos_lema_campo[campo].update(vistos_lema)

    campos = list(dict.fromkeys(df["campo"]))
    escrita = {n: g.most_common(1)[0][0] for n, g in grafia.items()}   # grafia mais comum
    linhas = [{"lema": lema, "forma": escrita[n], "ocorrencias": v, "textos": textos_forma[(lema, n)],
               **{f"ocorr_{c}": por_campo[c][(lema, n)] for c in campos}}
              for (lema, n), v in ocorr.most_common()]
    tab = pd.DataFrame(linhas)
    tab.to_csv(pasta / "formas.csv", sep=";", index=False, encoding="utf-8-sig")
    print(tab.groupby("lema")[["ocorrencias", "textos"]].sum().to_string())

    for lema in LEMAS:
        partes = [pd.DataFrame({"tipo": tipo, "combinacao": list(cont), "ocorrencias": list(cont.values())})
                  .sort_values("ocorrencias", ascending=False).head(200)
                  for tipo, cont in comb[lema].items()]
        if partes:
            pd.concat(partes).to_csv(pasta / f"combinacoes_{lema}.csv", sep=";", index=False,
                                     encoding="utf-8-sig")

    # a. formas mais frequentes, cor por lema
    top = tab.head(20)
    if not top.empty:
        fig, ax = figura(GRANDE)
        y = np.arange(len(top))[::-1]
        ax.barh(y, top["ocorrencias"], color=[COR_LEMA[l] for l in top["lema"]], height=0.7)
        ax.set_yticks(y, top["forma"], fontsize=9)
        ax.set_xscale("log")
        milhar(ax)
        ax.set_xlabel("# ocorrências (escala log)")
        ax.grid(axis="y", visible=False)
        from matplotlib.patches import Patch
        ax.legend([Patch(facecolor=COR_LEMA[l]) for l in LEMAS], list(LEMAS), loc="lower right")
        salvar(fig, pasta, "10a_formas")

    # b/c. combinações por lema
    for lema in LEMAS:
        for tipo, nome in (("direita_3", "combinacoes"), ("conteudo", "conteudo")):
            mais = comb[lema][tipo].most_common(args.top)
            if mais:
                barras_horizontais(pasta, f"10{'b' if tipo == 'direita_3' else 'c'}_{lema}_{nome}",
                                   [k for k, _ in mais], [v for _, v in mais], "# ocorrências",
                                   GRANDE, COR_LEMA[lema])

    # d. % dos textos de cada campo com o lema
    fig, ax = figura(PEQUENA)
    x = np.arange(len(campos))
    total = df["campo"].value_counts()
    for k, lema in enumerate(LEMAS):
        pct = [100 * textos_lema_campo[c][lema] / total[c] for c in campos]
        ax.bar(x + (k - 1) * 0.27, pct, 0.27, color=COR_LEMA[lema], label=lema)
    ax.set_xticks(x, [ROTULO[c] for c in campos], rotation=35, ha="right")
    # log: "negar" chega a ~9% dos textos e "recusar"/"rejeitar" ficam em ~0,1%
    ax.set_yscale("log")
    log_decimal(ax)
    ax.set_ylabel("% dos textos (escala log)")
    ax.grid(axis="x", visible=False)
    ax.legend()
    salvar(fig, pasta, "10d_por_campo")


if __name__ == "__main__":
    main()
