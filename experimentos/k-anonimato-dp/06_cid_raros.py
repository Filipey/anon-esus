"""Experimento 06 - CIDs raros na base original (antes da anonimização).

Conta, para cada código CID-10 avaliado nos problemas dos atendimentos
individuais e odontológicos do DW (as mesmas tabelas de `_populacao.py`):

- ocorrências: linhas de problema/condição avaliada com o código;
- pessoas: cidadãos distintos com o código.

E o mesmo na categoria (3 caracteres), somando as subcategorias. Grava
`resultados/06_cid_raros_<ts>.json` com a contagem de cada código (para a
ECDF e a lista dos mais raros) e imprime os mais raros.

Atenção: a lista tem contagens de 1 e 2 pessoas por doença, o que é
informação da base original. Fica em `resultados/` (fora do git) e deve ser
apagada no prazo junto com a original.
"""

from __future__ import annotations

import argparse

import pandas as pd

from _conexao import conectar, gravar, titulo

TABELAS = ("tb_fat_atd_ind_problemas", "tb_fat_atend_odonto_problemas")


def contagens(conn) -> pd.DataFrame:
    partes = []
    for tabela in TABELAS:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT upper(trim(d.nu_cid)), p.co_cidadao
                FROM {tabela} f
                JOIN tb_fat_cidadao_pec p ON p.co_seq_fat_cidadao_pec = f.co_fat_cidadao_pec
                JOIN tb_dim_cid d ON d.co_seq_dim_cid = f.co_dim_cid
                WHERE d.nu_cid IS NOT NULL AND trim(d.nu_cid) NOT IN ('-', '')
            """)
            partes.append(pd.DataFrame(cur.fetchall(), columns=["codigo", "id"]))
    return pd.concat(partes, ignore_index=True)


def nomes(conn) -> dict[str, str]:
    """Nome oficial por código (subcategoria e categoria) da tabela do PEC."""
    with conn.cursor() as cur:
        cur.execute("SELECT upper(trim(nu_cid10)), no_cid10 FROM tb_cid10 WHERE nu_cid10 IS NOT NULL")
        return {c: n for c, n in cur.fetchall()}


def resumo(linhas: pd.DataFrame, chave: str, nome: dict) -> pd.DataFrame:
    g = linhas.groupby(chave).agg(ocorrencias=("id", "size"), pessoas=("id", "nunique")).reset_index()
    g = g.rename(columns={chave: "codigo"})
    g["nome"] = g["codigo"].map(nome).fillna("")
    return g.sort_values(["ocorrencias", "pessoas", "codigo"]).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    conn = conectar()
    titulo("06 - CIDs raros na base original")
    linhas = contagens(conn)
    nome = nomes(conn)
    linhas["categoria"] = linhas["codigo"].str[:3]
    por_codigo = resumo(linhas, "codigo", nome)
    por_categoria = resumo(linhas, "categoria", nome)
    por_codigo["categoria"] = por_codigo["codigo"].str[:3]
    por_codigo["nome_categoria"] = por_codigo["categoria"].map(nome).fillna("")

    for rot, t in (("código", por_codigo), ("categoria", por_categoria)):
        print(f"\n{rot}: {len(t)} distintos, {int(t['ocorrencias'].sum())} ocorrências")
        for n in (1, 2, 3, 4):
            print(f"  com {n} ocorrência(s): {(t['ocorrencias'] == n).sum():>5}   "
                  f"com {n} pessoa(s): {(t['pessoas'] == n).sum():>5}")
        print(f"  {args.top} mais raros:")
        print(t.head(args.top).to_string(index=False))

    gravar("06_cid_raros", {
        "tabelas": TABELAS,
        "por_codigo": por_codigo.to_dict(orient="records"),
        "por_categoria": por_categoria.to_dict(orient="records"),
    })


if __name__ == "__main__":
    main()
