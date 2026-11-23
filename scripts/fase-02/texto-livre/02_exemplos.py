"""Levantamento 02 - exemplos reais de cada coluna de texto livre.

**Grava texto clínico real.** A saída fica em `resultados/`, que está no
`.gitignore`; não copie trechos daqui para documento versionado nem para
figura.

Para cada coluna `texto_livre` do `00_inventario` mais recente, sorteia
(semente fixa) até `--amostra` valores distintos e escolhe:

- `aleatorio`   : alguns valores quaisquer;
- `html`        : com marcação, mostrados bruto e sem HTML lado a lado;
- `pii`         : onde algum padrão de dado pessoal casou, com os trechos;
- `longo`       : o mais longo da amostra (truncado);
- `modelo`      : os textos mais repetidos da coluna inteira (template).

Grava `resultados/02_exemplos_<ts>.md`, uma seção por coluna, na ordem de
volume de células preenchidas.
"""

from __future__ import annotations

import argparse
import random

from _conexao import conectar, consulta, gravar, ident, ler, titulo
from _texto import GRUPOS, RE_TAG, achados_pii, grupo, ler_valores, lexico_nomes, sem_html

TRUNCAR = 1200


def cortar(texto: str, n: int = TRUNCAR) -> str:
    return texto if len(texto) <= n else texto[:n] + f" […+{len(texto) - n} caracteres]"


def bloco(texto: str) -> str:
    return "```text\n" + cortar(texto).replace("```", "'''") + "\n```"


def modelos(conn, tabela: str, coluna: str, n: int) -> list[tuple[str, int]]:
    v = f"nullif(btrim({ident(coluna)}::text), '')"
    r = consulta(
        conn,
        f"""
        SELECT v, count(*) FROM (SELECT {v} AS v FROM public.{ident(tabela)}) s
        WHERE v IS NOT NULL GROUP BY v HAVING count(*) > 1
        ORDER BY 2 DESC LIMIT {int(n)}
        """,
    )
    return [] if isinstance(r, dict) else r


def secao(conn, col: dict, nomes: set[str], amostra: int, por_estrato: int) -> list[str]:
    tab, cn = col["tabela"], col["coluna"]
    out = [
        f"## `{tab}.{cn}`",
        "",
        f"{col['preenchidas']:,} células preenchidas, {col['distintos']:,} distintas, "
        f"tamanho médio {col['tam_medio']}, p95 {col['tam_p95']}, máx {col['tam_max']}; "
        f"{col['n_html']:,} com HTML.",
        "",
    ]
    valores = ler_valores(conn, tab, cn, limite=amostra)
    if isinstance(valores, dict):
        return out + [f"Erro: {valores['erro']}", ""]
    rnd = random.Random(42)
    textos = [t for t, _ in valores]

    out += ["### Aleatórios", ""]
    for t in rnd.sample(textos, min(por_estrato, len(textos))):
        out += [bloco(t), ""]

    com_html = [t for t in textos if RE_TAG.search(t)]
    if com_html:
        out += [f"### Com HTML ({len(com_html)} de {len(textos)} na amostra)", ""]
        for t in rnd.sample(com_html, min(por_estrato, len(com_html))):
            out += ["Bruto:", bloco(t), "Sem HTML:", bloco(sem_html(t)), ""]

    com_pii = []
    for t in textos:
        a = achados_pii(sem_html(t), nomes)
        if a:
            com_pii.append((t, a))
    if com_pii:
        out += [f"### Com possível dado pessoal ({len(com_pii)} de {len(textos)} na amostra)", ""]
        for t, a in rnd.sample(com_pii, min(por_estrato, len(com_pii))):
            resumo = "; ".join(f"{k}: {', '.join(v[:5])}" for k, v in a.items())
            out += [f"Achados — {resumo}", bloco(sem_html(t)), ""]

    if textos:
        out += ["### Mais longo da amostra", "", bloco(max(textos, key=len)), ""]

    reps = modelos(conn, tab, cn, por_estrato)
    if reps:
        out += ["### Mais repetidos (modelo)", ""]
        for t, n in reps:
            out += [f"{n:,} células:", bloco(t), ""]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--amostra", type=int, default=2000,
                    help="valores distintos sorteados por coluna (padrão 2000)")
    ap.add_argument("--por-estrato", type=int, default=3,
                    help="exemplos mostrados por estrato (padrão 3)")
    ap.add_argument("--colunas", nargs="*",
                    help="só estas colunas, no formato tabela.coluna")
    ap.add_argument("--grupos", nargs="+", default=["clinico"], choices=GRUPOS,
                    help="grupos de coluna a amostrar (padrão: clinico)")
    args = ap.parse_args()

    inv = ler("00_inventario")
    alvo = [c for c in inv["colunas"]
            if c["classe"] == "texto_livre" and grupo(c["tabela"], c["coluna"]) in args.grupos]
    if args.colunas:
        alvo = [c for c in alvo if f"{c['tabela']}.{c['coluna']}" in set(args.colunas)]
    alvo.sort(key=lambda c: -c["preenchidas"])

    conn = conectar()
    titulo(f"02 - Exemplos de {len(alvo)} colunas de texto livre")
    nomes = lexico_nomes(conn)

    linhas = [
        "# Exemplos de texto livre — CONTÉM DADO REAL, NÃO VERSIONAR",
        "",
        f"Amostra de até {args.amostra} valores distintos por coluna (semente fixa), "
        f"{args.por_estrato} exemplos por estrato. Achados de dado pessoal são por regex "
        "e léxico de nomes da base: indicam onde olhar, não confirmam.",
        "",
    ]
    for i, col in enumerate(alvo, 1):
        print(f"  [{i}/{len(alvo)}] {col['tabela']}.{col['coluna']}", flush=True)
        linhas += secao(conn, col, nomes, args.amostra, args.por_estrato)

    gravar("02_exemplos", "\n".join(linhas), sufixo="md")
    print("ATENÇÃO: o arquivo contém texto clínico real.")


if __name__ == "__main__":
    main()
