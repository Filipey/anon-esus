"""Análise 14 - toxicidade (Detoxify multilíngue) por campo.

Modelo `Detoxify("multilingual")` (XLM-RoBERTa; cobre português), 7 rótulos:
toxicity, severe_toxicity, obscene, identity_attack, insult, threat,
sexual_explicit, cada um em [0, 1]. Pontua cada texto distinto uma vez só
(o mesmo texto repetido recebe a mesma nota), em lotes ordenados por
tamanho, na GPU se houver. O modelo (~1 GB) é baixado no primeiro uso para
`~/.cache/torch/hub`.

Cuidado ao ler: o modelo foi treinado em comentário de internet.
- Caixa alta é "grito" para ele: "PARASITOSE INTESTINAL" sai com toxicidade
  0,99 e "parasitose intestinal" com 0,01. Por isso o texto vai para
  minúscula antes de pontuar (`--manter-caixa` desliga); o que é tóxico de
  verdade continua alto ("xingou a equipe de idiota": 0,98 nos dois).
- Termo anatômico de exame ("prurido anal", "pênis", "vagina") sai com
  toxicidade e `sexual_explicit` altos mesmo em minúscula.
`detoxify_mais_altos.csv` traz os textos de maior nota por campo para essa
conferência — tem texto (pseudo-anonimizado).

Saída: `detoxify_textos.csv` (campo, paciente_id e as 7 notas; sem o texto),
`detoxify_campos.csv` (média, p95 e % >= `--limiar` por campo e rótulo),
`detoxify_mais_altos.csv` e figuras
- `14a_acima_limiar` (6x4): % dos textos com nota >= limiar, campo x rótulo;
- `14b_toxicidade_cauda` (6x4): % dos textos com toxicidade >= x, por campo.

Uso: 14_detoxify.py [--limiar 0.5] [--lote 128] [--manter-caixa] [--campos ...] [--distintos]"""

import numpy as np
import pandas as pd
import torch
from detoxify import Detoxify

from _corpus import (COR, GRANDE, ROTULO, argumentos, carrega, estilo, figura, log_decimal,
                     pasta_saida, salvar)

ROTULOS = ["toxicity", "severe_toxicity", "obscene", "identity_attack", "insult", "threat",
           "sexual_explicit"]


def pontua(textos: list[str], lote: int) -> pd.DataFrame:
    disp = "cuda" if torch.cuda.is_available() else "cpu"
    modelo = Detoxify("multilingual", device=disp)
    ordem = np.argsort([len(t) for t in textos])          # menos padding por lote
    notas = {r: np.zeros(len(textos)) for r in ROTULOS}
    for k in range(0, len(ordem), lote):
        idx = ordem[k:k + lote]
        with torch.inference_mode():
            r = modelo.predict([textos[i] for i in idx])
        for rot in ROTULOS:
            notas[rot][idx] = r[rot]
        if (k // lote) % 200 == 0:
            print(f"  {k + len(idx)}/{len(textos)} ({disp})")
    return pd.DataFrame(notas)


def main() -> None:
    p = argumentos(__doc__.splitlines()[0])
    p.add_argument("--limiar", type=float, default=0.5)
    p.add_argument("--lote", type=int, default=128)
    p.add_argument("--mais-altos", type=int, default=30, help="textos por campo no CSV de conferência")
    p.add_argument("--manter-caixa", action="store_true",
                   help="pontua o texto como está (sem passar para minúscula)")
    args = p.parse_args()
    estilo()
    df = carrega(args.entrada, args.campos, args.distintos)
    pasta = pasta_saida("14_detoxify")

    df["pontuado"] = df["texto"] if args.manter_caixa else df["texto"].str.lower()
    distintos = df["pontuado"].drop_duplicates().tolist()
    print(f"{len(df)} textos, {len(distintos)} distintos")
    notas = pontua(distintos, args.lote)
    notas.index = distintos
    df = df.join(notas, on="pontuado")
    df[["campo", "paciente_id", *ROTULOS]].round(5) \
        .to_csv(pasta / "detoxify_textos.csv", sep=";", index=False, encoding="utf-8-sig")

    campos = list(dict.fromkeys(df["campo"]))
    g = df.groupby("campo", sort=False)[ROTULOS]
    acima = g.agg(lambda s: 100 * (s >= args.limiar).mean()).loc[campos]
    pd.concat({"media": g.mean(), "p95": g.quantile(0.95), f"pct_acima_{args.limiar}": acima},
              names=["medida", "campo"]).round(5) \
        .to_csv(pasta / "detoxify_campos.csv", sep=";", encoding="utf-8-sig")
    df.sort_values("toxicity", ascending=False).groupby("campo", sort=False) \
        .head(args.mais_altos)[["campo", "texto", *ROTULOS]].round(3) \
        .to_csv(pasta / "detoxify_mais_altos.csv", sep=";", index=False, encoding="utf-8-sig")
    print(acima.round(2).to_string())

    # a. % acima do limiar, campo x rótulo
    fig, ax = figura(GRANDE)
    m = acima.to_numpy()
    im = ax.imshow(m, aspect="auto", cmap="Reds")
    ax.set_xticks(range(len(ROTULOS)), [r.replace("_", " ") for r in ROTULOS], rotation=35,
                  ha="right", fontsize=9)
    ax.set_yticks(range(len(campos)), [ROTULO[c] for c in campos])
    ax.grid(False)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, f"{m[i, j]:.2f}".replace(".", ","), ha="center", va="center", fontsize=7,
                    color="white" if m[i, j] > max(m.max(), 1e-9) * 0.6 else "0.15")
    fig.colorbar(im, ax=ax, label=f"% dos textos com nota $\\geq$ {args.limiar:g}".replace(".", ","),
                 fraction=0.04)
    salvar(fig, pasta, "14a_acima_limiar")

    # b. cauda da toxicidade: % dos textos com nota >= x
    fig, ax = figura(GRANDE)
    x = np.linspace(0, 1, 201)
    for campo in campos:
        s = np.sort(df.loc[df["campo"] == campo, "toxicity"].to_numpy())
        pct = 100 * (1 - np.searchsorted(s, x, side="left") / len(s))
        pct[pct == 0] = np.nan                         # log: a curva acaba onde zera
        ax.plot(x, pct, color=COR[campo], lw=1.6, label=ROTULO[campo])
    ax.set_yscale("log")
    log_decimal(ax)
    ax.set_xlabel("toxicidade (Detoxify)")
    ax.set_ylabel("% dos textos com nota $\\geq$ x (escala log)")
    ax.set_xlim(0, 1)
    ax.legend(loc="upper right")
    salvar(fig, pasta, "14b_toxicidade_cauda")


if __name__ == "__main__":
    main()
