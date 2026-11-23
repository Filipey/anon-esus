"""Levantamento 00 - inventário de todas as colunas textuais da base.

Varre toda coluna `text`/`varchar`/`char`/`json` do schema `public` (inclusive
as cópias `ta_*`/`tl_*`, que guardam o mesmo texto clínico das `tb_*`) e
mede, sem ler conteúdo para fora do banco:

- preenchimento (nulo, vazio/branco, preenchido) e cardinalidade;
- tamanho em caracteres (média, p50, p95, p99, máximo);
- proporção com >= 3 palavras, com marcação HTML, com entidade HTML
  (`&nbsp;`), com quebra de linha, com cara de JSON, só com dígitos/pontuação;

e classifica cada coluna em `texto_livre`, `curto` (nome, rótulo, frase
curta) ou `codigo` (enum, identificador, código), pelos limiares abaixo.
Colunas `bytea` entram numa lista à parte, com a assinatura dos primeiros
bytes (PDF, PNG, RTF, HTML...), porque documento binário também pode
carregar texto clínico.

Uma consulta por tabela (todas as colunas textuais juntas), read-only.
Grava `resultados/00_inventario_<ts>.json`, consumido pelos próximos
scripts.
"""

from __future__ import annotations

import time

from _conexao import conectar, consulta, familia, gravar, ident, titulo

TIPOS_TEXTO = ("text", "character varying", "character", "json", "jsonb")

# Limiares de classificação (sobre as linhas preenchidas).
LIVRE_MIN_PCT_3_PALAVRAS = 0.20
LIVRE_MIN_TAM_MEDIO = 15
CODIGO_MAX_TAM_MEDIO = 8
CODIGO_MAX_PCT_3_PALAVRAS = 0.05

# Regex POSIX avaliadas no Postgres. O banco é SQL_ASCII, então só padrões
# ASCII são confiáveis aqui (classe [À-ú] não funciona em SQL_ASCII).
RE_3_PALAVRAS = r"\S+\s+\S+\s+\S"
RE_TAG_HTML = r"<\s*/?\s*[A-Za-z][A-Za-z0-9]*(\s[^>]*)?/?>"
RE_ENTIDADE_HTML = r"&([A-Za-z]+|#[0-9]+|#x[0-9A-Fa-f]+);"
RE_QUEBRA = r"[\n\r]"
RE_JSON = r"^\s*[\{\[]"
RE_SO_NUMERICO = r"^[0-9\s.,:;/()+-]+$"

ASSINATURAS_BYTEA = {
    "25504446": "pdf",
    "89504e47": "png",
    "ffd8ffe0": "jpeg",
    "ffd8ffe1": "jpeg",
    "ffd8ffdb": "jpeg",
    "7b5c7274": "rtf",
    "3c21444f": "html",
    "3c68746d": "html",
    "3c3f786d": "xml",
    "504b0304": "zip/docx",
    "1f8b0800": "gzip",
}


def colunas_por_tabela(conn) -> dict[str, list[tuple[str, str, int | None]]]:
    linhas = consulta(
        conn,
        """
        SELECT c.table_name, c.column_name, c.data_type, c.character_maximum_length
        FROM information_schema.columns c
        JOIN information_schema.tables t USING (table_schema, table_name)
        WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE'
          AND c.data_type = ANY(%s)
        ORDER BY c.table_name, c.ordinal_position
        """,
        (list(TIPOS_TEXTO),),
    )
    out: dict[str, list] = {}
    for tabela, coluna, tipo, tam in linhas:
        out.setdefault(tabela, []).append((coluna, tipo, tam))
    return out


def medir_tabela(conn, tabela: str, colunas: list[tuple[str, str, int | None]]) -> dict:
    partes = ["count(*)"]
    for coluna, _, _ in colunas:
        v = f"nullif(btrim({ident(coluna)}::text), '')"
        partes += [
            f"count({ident(coluna)})",
            f"count({v})",
            f"count(DISTINCT {v})",
            f"avg(length({v}))",
            f"percentile_disc(0.5) WITHIN GROUP (ORDER BY length({v}))",
            f"percentile_disc(0.95) WITHIN GROUP (ORDER BY length({v}))",
            f"percentile_disc(0.99) WITHIN GROUP (ORDER BY length({v}))",
            f"max(length({v}))",
            f"count(*) FILTER (WHERE {v} ~ '{RE_3_PALAVRAS}')",
            f"count(*) FILTER (WHERE {v} ~ '{RE_TAG_HTML}')",
            f"count(*) FILTER (WHERE {v} ~ '{RE_ENTIDADE_HTML}')",
            f"count(*) FILTER (WHERE {v} ~ '{RE_QUEBRA}')",
            f"count(*) FILTER (WHERE {v} ~ '{RE_JSON}')",
            f"count(*) FILTER (WHERE {v} ~ '{RE_SO_NUMERICO}')",
        ]
    r = consulta(conn, f"SELECT {', '.join(partes)} FROM public.{ident(tabela)}")
    if isinstance(r, dict):
        return {"erro": r["erro"]}
    valores = list(r[0])
    n_linhas = valores.pop(0)
    out = {"linhas": n_linhas, "colunas": {}}
    for coluna, tipo, tam in colunas:
        (nao_nulas, preench, distintos, tam_medio, p50, p95, p99, tam_max,
         n3, html, ent, quebra, js, num) = valores[:14]
        del valores[:14]
        out["colunas"][coluna] = {
            "tipo": tipo,
            "tam_declarado": tam,
            "nao_nulas": nao_nulas,
            "preenchidas": preench,
            "vazias_ou_branco": nao_nulas - preench,
            "distintos": distintos,
            "tam_medio": round(float(tam_medio), 1) if tam_medio is not None else None,
            "tam_p50": p50,
            "tam_p95": p95,
            "tam_p99": p99,
            "tam_max": tam_max,
            "n_3_palavras": n3,
            "n_html": html,
            "n_entidade_html": ent,
            "n_quebra_linha": quebra,
            "n_json": js,
            "n_so_numerico": num,
        }
    return out


def classificar(m: dict) -> str:
    p = m["preenchidas"]
    if not p:
        return "vazia"
    pct3 = m["n_3_palavras"] / p
    if m["n_html"] / p >= 0.05:
        return "texto_livre"
    if pct3 >= LIVRE_MIN_PCT_3_PALAVRAS and (m["tam_medio"] or 0) >= LIVRE_MIN_TAM_MEDIO:
        return "texto_livre"
    if (m["tam_medio"] or 0) <= CODIGO_MAX_TAM_MEDIO or pct3 <= CODIGO_MAX_PCT_3_PALAVRAS:
        return "codigo"
    return "curto"


def medir_bytea(conn) -> list[dict]:
    colunas = consulta(
        conn,
        """
        SELECT table_name, column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND data_type = 'bytea'
        ORDER BY 1, 2
        """,
    )
    out = []
    for tabela, coluna in colunas:
        c = ident(coluna)
        r = consulta(
            conn,
            f"""
            SELECT count(*), count({c}), avg(octet_length({c}))::bigint, max(octet_length({c}))
            FROM public.{ident(tabela)}
            """,
        )
        assin = consulta(
            conn,
            f"""
            SELECT encode(substring({c} FROM 1 FOR 4), 'hex') AS a, count(*)
            FROM public.{ident(tabela)} WHERE {c} IS NOT NULL
            GROUP BY 1 ORDER BY 2 DESC LIMIT 8
            """,
        )
        item = {"tabela": tabela, "coluna": coluna, "familia": familia(tabela)}
        if isinstance(r, dict):
            item["erro"] = r["erro"]
        else:
            linhas, preench, medio, maximo = r[0]
            item |= {"linhas": linhas, "preenchidas": preench, "bytes_medio": medio, "bytes_max": maximo}
        if not isinstance(assin, dict):
            item["assinaturas"] = {
                f"{a} ({ASSINATURAS_BYTEA.get(a, '?')})": n for a, n in assin
            }
        out.append(item)
    return out


def main() -> None:
    conn = conectar()
    titulo("00 - Inventário de colunas textuais")
    por_tabela = colunas_por_tabela(conn)
    total_col = sum(len(v) for v in por_tabela.values())
    print(f"  {len(por_tabela)} tabelas, {total_col} colunas textuais\n")

    colunas_out = []
    erros = {}
    inicio = time.time()
    for i, (tabela, colunas) in enumerate(sorted(por_tabela.items()), 1):
        r = medir_tabela(conn, tabela, colunas)
        if "erro" in r:
            erros[tabela] = r["erro"]
            print(f"  [{i}/{len(por_tabela)}] {tabela}: ERRO {r['erro']}")
            continue
        for coluna, m in r["colunas"].items():
            colunas_out.append(
                {
                    "tabela": tabela,
                    "coluna": coluna,
                    "familia": familia(tabela),
                    "linhas_tabela": r["linhas"],
                    **m,
                    "classe": classificar(m),
                }
            )
        if i % 50 == 0:
            print(f"  [{i}/{len(por_tabela)}] {time.time() - inicio:.0f}s", flush=True)

    titulo("Resumo por classe x família")
    resumo: dict[str, dict[str, int]] = {}
    for c in colunas_out:
        resumo.setdefault(c["classe"], {}).setdefault(c["familia"], 0)
        resumo[c["classe"]][c["familia"]] += 1
    for classe, fams in sorted(resumo.items()):
        print(f"  {classe:12} total={sum(fams.values()):5}  {fams}")

    livres = [c for c in colunas_out if c["classe"] == "texto_livre"]
    print(f"\n  Texto livre: {len(livres)} colunas em "
          f"{len({c['tabela'] for c in livres})} tabelas, "
          f"{sum(c['preenchidas'] for c in livres):,} células preenchidas, "
          f"{sum(c['n_html'] for c in livres):,} com HTML")

    titulo("bytea")
    binarios = medir_bytea(conn)
    for b in binarios:
        print(f"  {b['tabela']}.{b['coluna']}: {b.get('preenchidas')} preenchidas, "
              f"{b.get('assinaturas', b.get('erro'))}")

    gravar(
        "00_inventario",
        {
            "limiares": {
                "livre_min_pct_3_palavras": LIVRE_MIN_PCT_3_PALAVRAS,
                "livre_min_tam_medio": LIVRE_MIN_TAM_MEDIO,
                "codigo_max_tam_medio": CODIGO_MAX_TAM_MEDIO,
                "codigo_max_pct_3_palavras": CODIGO_MAX_PCT_3_PALAVRAS,
            },
            "resumo": resumo,
            "colunas": colunas_out,
            "bytea": binarios,
            "erros": erros,
        },
    )


if __name__ == "__main__":
    main()
