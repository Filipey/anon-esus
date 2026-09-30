"""Experimento 01 - a micro-area e mais fina que o setor censitario?

Responde a pergunta que decide se a micro-area pode ser nivel publicavel ou
se e so o G0 da hierarquia (e portanto suprimida). A estimativa a confirmar
e de 22 a 44 micro-areas com ~240 a ~475 pessoas cada - se bater, ela e mais
fina que um setor censitario urbano tipico e nao serve como bucket.

Mede tambem quantas micro-areas cada equipe cobre, que e o fator de
generalizacao caso o eixo escolhido seja o do territorio de saude
(micro-area -> area).

Read-only, so agregado.
"""

from __future__ import annotations

from _conexao import (
    colunas_de,
    conectar,
    consulta,
    existe_tabela,
    gravar,
    titulo,
    uma,
)

# Tabelas que carregam micro-area no nivel da pessoa ou do domicilio, na
# ordem de preferencia (operacional antes de DW, e antes das de auditoria).
FONTES = [
    ("tb_cidadao", "nu_micro_area", "cidadao"),
    ("tb_cds_domicilio", "nu_micro_area", "domicilio"),
    ("tb_cds_cad_domiciliar", "nu_micro_area", "cadastro domiciliar"),
    ("tb_fat_cidadao_territorio", "nu_micro_area", "cidadao (DW)"),
    ("tb_fat_familia_territorio", "nu_micro_area", "familia (DW)"),
]

QUANTIS = """
    SELECT count(*)                                                   AS n_micro_areas,
           coalesce(sum(n), 0)                                        AS n_registros,
           min(n), max(n), round(avg(n), 1)                           AS media,
           percentile_disc(0.25) WITHIN GROUP (ORDER BY n)            AS p25,
           percentile_disc(0.50) WITHIN GROUP (ORDER BY n)            AS mediana,
           percentile_disc(0.75) WITHIN GROUP (ORDER BY n)            AS p75,
           count(*) FILTER (WHERE n < 20)                             AS abaixo_de_20,
           count(*) FILTER (WHERE n < 50)                             AS abaixo_de_50,
           count(*) FILTER (WHERE n < 100)                            AS abaixo_de_100
    FROM (
        SELECT "{col}" AS chave, count(*) AS n
        FROM public."{tab}"
        WHERE "{col}" IS NOT NULL AND btrim("{col}") <> ''
        GROUP BY 1
    ) g
"""

CAMPOS = [
    "n_micro_areas", "n_registros", "min", "max", "media",
    "p25", "mediana", "p75", "abaixo_de_20", "abaixo_de_50", "abaixo_de_100",
]


def main() -> None:
    conn = conectar()
    relatorio: dict = {"fontes": {}}

    titulo("01 - Distribuicao das micro-areas")
    print("Referencia: setor censitario urbano tem tipicamente algumas")
    print("centenas de domicilios, perto de mil pessoas.\n")

    for tabela, coluna, rotulo in FONTES:
        if not existe_tabela(conn, tabela) or coluna not in colunas_de(conn, tabela):
            print(f"  {tabela}: ausente ou sem {coluna} - pulando")
            continue

        r = uma(conn, QUANTIS.format(tab=tabela, col=coluna))
        if isinstance(r, dict):
            print(f"  {tabela}: erro/timeout -> {r['erro']}")
            relatorio["fontes"][tabela] = r
            continue

        d = dict(zip(CAMPOS, r))
        d["rotulo"] = rotulo
        relatorio["fontes"][tabela] = d

        print(f"  {tabela}  ({rotulo})")
        print(f"      micro-areas distintas: {d['n_micro_areas']}")
        print(f"      registros com micro-area: {d['n_registros']}")
        print(
            f"      por micro-area -> min={d['min']} p25={d['p25']} "
            f"mediana={d['mediana']} p75={d['p75']} max={d['max']} "
            f"media={d['media']}"
        )
        print(
            f"      micro-areas com menos de 20/50/100 registros: "
            f"{d['abaixo_de_20']} / {d['abaixo_de_50']} / {d['abaixo_de_100']}"
        )

    # Fator de generalizacao micro-area -> area, se o eixo for o da saude.
    titulo("Micro-areas por equipe (fator de generalizacao do eixo da saude)")
    cols = colunas_de(conn, "tb_cidadao")
    col_equipe = next(
        (c for c in ("co_dim_equipe", "co_equipe", "nu_ine") if c in cols), None
    )
    if col_equipe and "nu_micro_area" in cols:
        r = consulta(
            conn,
            f"""
            SELECT count(*)                                        AS n_equipes,
                   min(n_ma), max(n_ma), round(avg(n_ma), 1)       AS media,
                   percentile_disc(0.50) WITHIN GROUP (ORDER BY n_ma) AS mediana
            FROM (
                SELECT "{col_equipe}" AS equipe,
                       count(DISTINCT nu_micro_area) AS n_ma
                FROM public.tb_cidadao
                WHERE "{col_equipe}" IS NOT NULL
                  AND nu_micro_area IS NOT NULL AND btrim(nu_micro_area) <> ''
                GROUP BY 1
            ) g
            """,
        )
        if isinstance(r, dict):
            print("  erro:", r["erro"])
            relatorio["micro_areas_por_equipe"] = r
        else:
            n_eq, mn, mx, media, mediana = r[0]
            print(f"  coluna de equipe usada: {col_equipe}")
            print(f"  equipes: {n_eq}")
            print(f"  micro-areas por equipe -> min={mn} mediana={mediana} max={mx} media={media}")
            relatorio["micro_areas_por_equipe"] = {
                "coluna_equipe": col_equipe,
                "n_equipes": n_eq,
                "min": mn,
                "max": mx,
                "media": media,
                "mediana": mediana,
            }
    else:
        print("  tb_cidadao sem coluna de equipe ou de micro-area reconhecida")

    titulo("Como ler")
    print("Se a mediana de pessoas por micro-area ficar bem abaixo de ~900,")
    print("a micro-area e mais fina que um setor censitario e NAO serve como")
    print("bucket publicavel - confirma a decisao de suprimi-la e usar area.")

    gravar("01_micro_areas", relatorio)
    conn.close()


if __name__ == "__main__":
    main()
