"""Experimento 00b - qual e, de fato, o elo "cidadao/domicilio -> unidade"?

O 00 revelou que so 3 unidades distintas aparecem em `tb_cds_domicilio.nu_cnes`,
contra 12 na tabela mestra. Esse campo e o CNES da unidade cuja equipe fez o
cadastro domiciliar - procedencia da coleta - e nao necessariamente a unidade
de vinculo do cidadao, que e o que a faixa de distancia precisa.

Este script compara os caminhos candidatos e diz qual tem cobertura real,
para o 03 apontar para o certo. Tambem mostra quantas unidades de fato
fazem territorio, que e o numero de geocodificacoes manuais necessarias -
possivelmente bem menor que 12.

Read-only, so agregado.
"""

from __future__ import annotations

from _conexao import colunas_de, conectar, existe_tabela, gravar, titulo, uma

# (rotulo, tabela, coluna) - candidatos a carregar o vinculo territorial.
CANDIDATOS = [
    ("domicilio CDS -> CNES da coleta", "tb_cds_domicilio", "nu_cnes"),
    ("domicilio CDS -> INE da equipe", "tb_cds_domicilio", "nu_ine"),
    ("cadastro domiciliar -> INE", "tb_cds_cad_domiciliar", "nu_ine"),
    ("vinculacao de equipe do cidadao", "tb_cidadao_vinculacao_equipe", "nu_ine"),
    ("territorio do cidadao (DW)", "tb_fat_cidadao_territorio", "co_dim_unidade_saude"),
    ("territorio do cidadao (DW) - equipe", "tb_fat_cidadao_territorio", "co_dim_equipe"),
    ("territorio da familia (DW)", "tb_fat_familia_territorio", "co_dim_unidade_saude"),
    ("territorio da familia (DW) - equipe", "tb_fat_familia_territorio", "co_dim_equipe"),
    ("domicilio DW -> unidade", "tb_fat_cad_domiciliar", "co_dim_unidade_saude"),
]


def main() -> None:
    conn = conectar()
    relatorio: dict = {"candidatos": {}}

    titulo("00b - Caminhos candidatos para 'unidade de vinculo'")
    print("  Interessa o que tem MAIS cobertura de linhas e um numero de")
    print("  unidades distintas coerente com quem faz territorio.\n")

    for rotulo, tabela, coluna in CANDIDATOS:
        if not existe_tabela(conn, tabela) or coluna not in colunas_de(conn, tabela):
            print(f"  {rotulo:38} ausente")
            continue

        r = uma(
            conn,
            f"""
            SELECT count(*)                                              AS linhas,
                   count("{coluna}")                                     AS preenchidas,
                   count(DISTINCT "{coluna}")                            AS distintos
            FROM public."{tabela}"
            """,
        )
        if isinstance(r, dict):
            print(f"  {rotulo:38} erro -> {r['erro']}")
            relatorio["candidatos"][f"{tabela}.{coluna}"] = r
            continue

        linhas, preenchidas, distintos = r
        pct = (100.0 * preenchidas / linhas) if linhas else 0.0
        print(
            f"  {rotulo:38} {distintos:>4} distinto(s)   "
            f"{preenchidas}/{linhas} preenchidas ({pct:.0f}%)"
        )
        relatorio["candidatos"][f"{tabela}.{coluna}"] = {
            "rotulo": rotulo,
            "linhas": linhas,
            "preenchidas": preenchidas,
            "distintos": distintos,
            "cobertura_pct": round(pct, 1),
        }

    # Quantas unidades tem equipe - ou seja, fazem territorio de fato.
    titulo("Quantas unidades fazem territorio")
    if existe_tabela(conn, "tb_equipe"):
        cols = colunas_de(conn, "tb_equipe")
        col_un = next(
            (c for c in ("co_unidade_saude", "nu_cnes", "co_dim_unidade_saude") if c in cols),
            None,
        )
        if col_un:
            r = uma(
                conn,
                f"""
                SELECT count(DISTINCT "{col_un}") AS unidades_com_equipe,
                       count(*)                   AS equipes
                FROM public.tb_equipe
                WHERE "{col_un}" IS NOT NULL
                """,
            )
            if not isinstance(r, dict):
                print(f"  unidades com pelo menos uma equipe: {r[0]}  (equipes: {r[1]})")
                print(f"  coluna de unidade em tb_equipe: {col_un}")
                relatorio["unidades_com_equipe"] = {
                    "coluna": col_un,
                    "unidades": r[0],
                    "equipes": r[1],
                }
        else:
            print("  tb_equipe sem coluna de unidade reconhecida")
    total = uma(conn, "SELECT count(*) FROM public.tb_unidade_saude")
    if not isinstance(total, dict) and total:
        print(f"  unidades na tabela mestra: {total[0]}")
        relatorio["unidades_total"] = total[0]

    titulo("Como ler")
    print("  O elo certo e o que cobre a maior parte das linhas e cujo numero")
    print("  de unidades distintas bate com 'unidades com equipe'. Sao essas")
    print("  que precisam de coordenada - as demais nao fazem adscricao e nao")
    print("  entram na faixa de distancia.")

    gravar("00b_vinculo_unidade", relatorio)
    conn.close()


if __name__ == "__main__":
    main()
