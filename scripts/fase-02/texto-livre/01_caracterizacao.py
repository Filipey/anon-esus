"""Levantamento 01 - caracterização do conteúdo das colunas de texto livre.

Consome o `00_inventario` mais recente e, para cada coluna classificada como
`texto_livre` (e `curto` com `--incluir-curto`), lê os valores distintos com
a contagem de cada um e mede em Python:

HTML
  - % de células com tag, com entidade (`&nbsp;`), com atributo `style`/
    `class`, histograma de tags e de entidades;
  - sobrecarga da marcação: tamanho bruto vs. tamanho depois de tirar o HTML.

Forma do texto (sempre depois de tirar o HTML)
  - palavras, linhas, % em CAIXA ALTA, % de dígitos, % não-ASCII;
  - indício de mojibake (`Ã©`, `Ã§`...), sinal de dupla codificação.

Repetição
  - % de células cujo texto aparece mais de uma vez (modelo/template),
    tamanho do maior grupo repetido.

Dado pessoal embutido (regex, sobre o texto sem HTML)
  - CPF, CNS, telefone, e-mail, CEP, data, idade, endereço, tratamento
    (Sr./Dra.), parentesco, número de prontuário, registro de conselho;
  - nome próprio: token capitalizado que existe no léxico de nomes de
    cidadão/profissional da própria base (proxy de risco de nome real).

Cópias
  - para cada `tb_X.col` com `ta_X.col`/`tl_X.col`, quanto do texto distinto
    da tb reaparece nas cópias — o NER tem que tratar as três igual.

Grava `resultados/01_caracterizacao_<ts>.json` só com contagens (nenhum
texto). Os exemplos saem no script 02.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import time
from collections import Counter

from _conexao import conectar, gravar, ler, titulo
from _texto import (
    GRUPOS,
    RE_ENTIDADE,
    RE_MOJIBAKE,
    RE_PALAVRA,
    RE_TAG,
    achados_pii,
    grupo,
    ler_valores,
    lexico_nomes,
    sem_html,
)


def caracterizar(valores: list[tuple[str, int]], nomes: set[str]) -> dict:
    total = sum(n for _, n in valores)
    c = Counter()
    tags = Counter()
    entidades = Counter()
    atributos = Counter()
    pii_celulas = Counter()
    pii_ocorrencias = Counter()
    palavras_hist = Counter()
    maior_repeticao = 0
    bytes_brutos = bytes_limpos = 0

    for texto, n in valores:
        maior_repeticao = max(maior_repeticao, n)
        if n > 1:
            c["celulas_repetidas"] += n
        achou_tags = RE_TAG.findall(texto)
        if achou_tags:
            c["com_html"] += n
            for _, nome, attrs in achou_tags:
                tags[nome.lower()] += n
                for a in re.findall(r"([A-Za-z-]+)\s*=", attrs):
                    atributos[a.lower()] += n
        achou_ent = RE_ENTIDADE.findall(texto)
        if achou_ent:
            c["com_entidade"] += n
            for e in achou_ent:
                entidades[e] += n

        limpo = sem_html(texto)
        bytes_brutos += len(texto) * n
        bytes_limpos += len(limpo) * n
        if not limpo:
            c["so_marcacao"] += n
            continue

        letras = [ch for ch in limpo if ch.isalpha()]
        if letras and sum(ch.isupper() for ch in letras) / len(letras) > 0.8:
            c["caixa_alta"] += n
        if any(ord(ch) > 127 for ch in limpo):
            c["nao_ascii"] += n
        if RE_MOJIBAKE.search(limpo):
            c["mojibake"] += n
        if "\n" in texto or "<br" in texto.lower() or "</p>" in texto.lower():
            c["multilinha"] += n

        n_pal = len(RE_PALAVRA.findall(limpo))
        faixa = next(f for f in (1, 2, 5, 10, 20, 50, 100, 200, 500, 10**9) if n_pal <= f)
        palavras_hist[faixa] += n
        c["palavras_total"] += n_pal * n

        for rotulo, achados in achados_pii(limpo, nomes).items():
            pii_celulas[rotulo] += n
            pii_ocorrencias[rotulo] += len(achados) * n

    pct = lambda k: round(c[k] / total, 4) if total else 0.0  # noqa: E731
    return {
        "celulas": total,
        "distintos": len(valores),
        "pct_repetidas": pct("celulas_repetidas"),
        "maior_repeticao": maior_repeticao,
        "pct_html": pct("com_html"),
        "pct_entidade_html": pct("com_entidade"),
        "pct_so_marcacao": pct("so_marcacao"),
        "sobrecarga_html": round(1 - bytes_limpos / bytes_brutos, 4) if bytes_brutos else 0.0,
        "tags": dict(tags.most_common(25)),
        "atributos_html": dict(atributos.most_common(15)),
        "entidades_html": dict(entidades.most_common(15)),
        "pct_caixa_alta": pct("caixa_alta"),
        "pct_nao_ascii": pct("nao_ascii"),
        "pct_mojibake": pct("mojibake"),
        "pct_multilinha": pct("multilinha"),
        "palavras_media": round(c["palavras_total"] / total, 1) if total else 0.0,
        "palavras_hist": {f"<={k}" if k < 10**9 else ">500": v for k, v in sorted(palavras_hist.items())},
        "pii_pct_celulas": {k: round(v / total, 4) for k, v in pii_celulas.most_common()},
        "pii_ocorrencias": dict(pii_ocorrencias.most_common()),
    }


def hashes(valores) -> set[bytes]:
    return {hashlib.md5(sem_html(t).lower().encode()).digest() for t, _ in valores}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--incluir-curto", action="store_true",
                    help="caracteriza também as colunas da classe 'curto'")
    ap.add_argument("--grupos", nargs="+", default=["clinico"], choices=GRUPOS,
                    help="grupos de coluna a caracterizar (padrão: clinico)")
    args = ap.parse_args()

    inv = ler("00_inventario")
    classes = {"texto_livre"} | ({"curto"} if args.incluir_curto else set())
    alvo = [c for c in inv["colunas"]
            if c["classe"] in classes and grupo(c["tabela"], c["coluna"]) in args.grupos]
    alvo.sort(key=lambda c: -c["preenchidas"])

    conn = conectar()
    titulo(f"01 - Caracterização de {len(alvo)} colunas "
           f"({', '.join(sorted(classes))}; grupos {', '.join(args.grupos)})")
    nomes = lexico_nomes(conn)
    print(f"  léxico de nomes da base: {len(nomes):,} tokens\n")

    resultado = []
    assinaturas: dict[tuple[str, str], set[bytes]] = {}
    inicio = time.time()
    for i, col in enumerate(alvo, 1):
        valores = ler_valores(conn, col["tabela"], col["coluna"])
        if isinstance(valores, dict):
            print(f"  {col['tabela']}.{col['coluna']}: ERRO {valores['erro']}")
            continue
        m = caracterizar(valores, nomes)
        assinaturas[(col["tabela"], col["coluna"])] = hashes(valores)
        resultado.append({"tabela": col["tabela"], "coluna": col["coluna"],
                          "familia": col["familia"],
                          "grupo": grupo(col["tabela"], col["coluna"]), **m})
        print(f"  [{i}/{len(alvo)}] {col['tabela']}.{col['coluna']}: "
              f"{m['celulas']:,} células, html={m['pct_html']:.0%}, "
              f"pal.média={m['palavras_media']}  ({time.time() - inicio:.0f}s)", flush=True)

    titulo("Cópias ta_/tl_ do mesmo texto")
    copias = []
    for (tabela, coluna), hs in assinaturas.items():
        if not tabela.startswith("tb_") or not hs:
            continue
        for prefixo in ("ta_", "tl_"):
            par = (prefixo + tabela[3:], coluna)
            if par in assinaturas:
                comum = len(hs & assinaturas[par])
                copias.append({
                    "tb": f"{tabela}.{coluna}", "copia": f"{par[0]}.{coluna}",
                    "distintos_tb": len(hs), "distintos_copia": len(assinaturas[par]),
                    "pct_tb_na_copia": round(comum / len(hs), 4),
                })
                print(f"  {tabela}.{coluna} -> {par[0]}: {comum / len(hs):.0%} do texto da tb reaparece")

    gravar("01_caracterizacao", {
        "classes": sorted(classes),
        "grupos": args.grupos,
        "lexico_nomes_tamanho": len(nomes),
        "colunas": resultado,
        "copias": copias,
    })


if __name__ == "__main__":
    main()
