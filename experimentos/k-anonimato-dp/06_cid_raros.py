"""Experimento 06 - CIDs raros na base original (antes da anonimização).

Conta, para cada código CID-10 avaliado nos problemas dos atendimentos
individuais e odontológicos do DW (as mesmas tabelas de `_populacao.py`):

- ocorrências: linhas de problema/condição avaliada com o código;
- pessoas: cidadãos distintos com o código.

E o mesmo na categoria (3 caracteres), somando as subcategorias. Grava
`resultados/06_cid_raros_<ts>.json` com a contagem de cada código (para a
ECDF e a lista dos mais raros) e imprime os mais raros.

Também lista as categorias fragmentadas: a mesma doença registrada com dois
ou mais códigos, todos com menos de K pessoas (ex.: A161, A167 e A168 em
A16). Grava `resultados/06_cid_fragmentadas_<ts>.csv`, com a soma na
categoria e se ela alcança K (sobe para a categoria) ou não (suprimida).

Atenção: a lista tem contagens de 1 e 2 pessoas por doença, o que é
informação da base original. Fica em `resultados/` (fora do git) e deve ser
apagada no prazo junto com a original.
"""

from __future__ import annotations

import argparse

import pandas as pd

from _conexao import conectar, gravar, titulo

TABELAS = ("tb_fat_atd_ind_problemas", "tb_fat_atend_odonto_problemas")
K = 5


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


def fragmentadas(linhas: pd.DataFrame, por_codigo: pd.DataFrame, nome: dict) -> pd.DataFrame:
    """Categorias com 2+ códigos distintos, todos com menos de K pessoas."""
    g = por_codigo.groupby("categoria").agg(codigos=("codigo", "size"), max_pessoas=("pessoas", "max"))
    sel = g[(g["codigos"] >= 2) & (g["max_pessoas"] < K)].index
    cat = linhas[linhas["categoria"].isin(sel)].groupby("categoria").agg(
        ocorrencias=("id", "size"), pessoas=("id", "nunique"))
    detalhe = (por_codigo[por_codigo["categoria"].isin(sel)].sort_values("codigo")
               .assign(txt=lambda d: d["codigo"] + " " + d["nome"] + " (" + d["ocorrencias"].astype(str)
                       + "/" + d["pessoas"].astype(str) + ")")
               .groupby("categoria")["txt"].agg(" | ".join))
    out = g.loc[sel, ["codigos"]].join(cat).join(detalhe.rename("codigos_ocorrencias_pessoas"))
    out["soma_pessoas_codigos"] = por_codigo[por_codigo["categoria"].isin(sel)].groupby("categoria")["pessoas"].sum()
    out["destino_k5"] = (out["pessoas"] >= K).map({True: "sobe para a categoria", False: "suprimida"})
    out.insert(0, "nome", out.index.map(nome).fillna(""))
    return out.reset_index().sort_values(["codigos", "pessoas"], ascending=False)


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

    frag = fragmentadas(linhas, por_codigo, nome)
    print(f"\ncategorias fragmentadas (2+ códigos, todos com menos de {K} pessoas): {len(frag)}")
    print(f"  sobem para a categoria: {(frag['pessoas'] >= K).sum()}   suprimidas: {(frag['pessoas'] < K).sum()}")
    print(f"  mesma pessoa com 2+ códigos da categoria: {(frag['soma_pessoas_codigos'] > frag['pessoas']).sum()}")
    gravar("06_cid_fragmentadas", frag.to_csv(index=False), sufixo="csv")

    gravar("06_cid_raros", {
        "tabelas": TABELAS,
        "por_codigo": por_codigo.to_dict(orient="records"),
        "por_categoria": por_categoria.to_dict(orient="records"),
    })


if __name__ == "__main__":
    main()
