"""Análise 12 - categorias do LIWC por campo.

Mesmo método do ICWSM 2026 (`liwc.load_token_parser` + % dos tokens em cada
categoria), com dicionário em português. O dicionário não vem com o
repositório (licença do LIWC): passe `--dic` ou a variável `LIWC_DIC`. O
LIWC 2007 em português do NILC/USP (Balage Filho et al., 2013) é o usual
para PT-BR. Arquivo em latin-1 é convertido para UTF-8 em memória.

Por texto: % dos tokens em cada categoria. Por campo: média entre os textos
(com >= 1 token) e % agregada (tokens da categoria / todos os tokens).

Saída: `liwc_campos.csv` (campo x categoria, média e agregada),
`liwc_textos.csv` (campo, paciente_id e as % por texto; sem o texto) e
figuras
- `12a_liwc_mapa` (6x4): mapa de calor campo x categorias selecionadas;
- `12b_liwc_<categoria>` (4x3): média por campo de cada categoria de `--figuras`.

Uso: 12_liwc.py --dic arquivo.dic [--categorias ...] [--campos ...] [--distintos]"""

import os
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd

from _corpus import (COR, GRANDE, PEQUENA, ROTULO, argumentos, carrega, estilo, figura,
                     pasta_saida, salvar, tokens)

# Categorias de interesse para texto clínico; ficam as que o dicionário tiver.
PREFERIDAS = ["negate", "posemo", "negemo", "anx", "anger", "sad", "health", "body", "bio",
              "sexual", "ingest", "death", "family", "social", "cogmech", "percept"]


def carrega_dicionario(caminho: Path):
    import liwc
    bruto = caminho.read_bytes()
    try:
        texto = bruto.decode("utf-8")
    except UnicodeDecodeError:
        texto = bruto.decode("latin-1")
    with tempfile.NamedTemporaryFile("w", suffix=".dic", encoding="utf-8", delete=False) as f:
        f.write(texto)
    try:
        return liwc.load_token_parser(f.name)
    finally:
        os.unlink(f.name)


def main() -> None:
    p = argumentos(__doc__.splitlines()[0])
    p.add_argument("--dic", type=Path, default=os.environ.get("LIWC_DIC"),
                   help="dicionário LIWC (.dic); padrão: variável LIWC_DIC")
    p.add_argument("--categorias", nargs="+", default=None,
                   help="categorias do mapa (padrão: as de PREFERIDAS que existirem)")
    p.add_argument("--figuras", nargs="+", default=["negate", "negemo", "health", "body"],
                   help="categorias com figura própria (4x3)")
    args = p.parse_args()
    if not args.dic or not Path(args.dic).exists():
        raise SystemExit("Dicionário LIWC não encontrado: passe --dic arquivo.dic ou defina LIWC_DIC.")
    estilo()
    parse, categorias = carrega_dicionario(Path(args.dic))
    df = carrega(args.entrada, args.campos, args.distintos)
    pasta = pasta_saida("12_liwc")

    linhas, agregado, n_tokens = [], {}, Counter()
    for campo, pid, texto in zip(df["campo"], df["paciente_id"], df["texto"]):
        toks = tokens(texto)
        if not toks:
            continue
        cont = Counter(c for t in toks for c in parse(t))
        agregado.setdefault(campo, Counter()).update(cont)
        n_tokens[campo] += len(toks)
        linhas.append({"campo": campo, "paciente_id": pid, "tokens": len(toks),
                       **{c: 100 * cont.get(c, 0) / len(toks) for c in categorias}})
    textos = pd.DataFrame(linhas)
    textos.round(3).to_csv(pasta / "liwc_textos.csv", sep=";", index=False, encoding="utf-8-sig")

    campos = list(dict.fromkeys(textos["campo"]))
    media = textos.groupby("campo", sort=False)[categorias].mean().loc[campos]
    agreg = pd.DataFrame({c: {cat: 100 * agregado[c][cat] / n_tokens[c] for cat in categorias}
                          for c in campos}).T.loc[campos]
    pd.concat({"media_por_texto": media, "agregada": agreg}, names=["medida", "campo"]) \
        .round(3).to_csv(pasta / "liwc_campos.csv", sep=";", encoding="utf-8-sig")

    sel = args.categorias or [c for c in PREFERIDAS if c in categorias] \
        or list(media.mean().sort_values(ascending=False).index[:10])
    sel = [c for c in sel if c in categorias]
    print(f"{len(categorias)} categorias no dicionário; mapa com: {', '.join(sel)}")

    # a. mapa de calor campo x categoria
    fig, ax = figura(GRANDE)
    m = media[sel].to_numpy()
    im = ax.imshow(m, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(sel)), sel, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(campos)), [ROTULO[c] for c in campos])
    ax.grid(False)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, f"{m[i, j]:.1f}".replace(".", ","), ha="center", va="center", fontsize=7,
                    color="white" if m[i, j] > m.max() * 0.6 else "0.15")
    fig.colorbar(im, ax=ax, label="% dos tokens (média por texto)", fraction=0.04)
    salvar(fig, pasta, "12a_liwc_mapa")

    # b. uma figura por categoria pedida
    for cat in [c for c in args.figuras if c in categorias]:
        fig, ax = figura(PEQUENA)
        ax.bar(range(len(campos)), media[cat], color=[COR[c] for c in campos], width=0.65)
        ax.set_xticks(range(len(campos)), [ROTULO[c] for c in campos], rotation=35, ha="right")
        ax.set_ylabel(f"% dos tokens ({cat})")
        ax.grid(axis="x", visible=False)
        salvar(fig, pasta, f"12b_liwc_{cat}")


if __name__ == "__main__":
    main()
