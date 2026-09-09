"""Experimento 05 - a micro-area e mesmo um lugar? E o que mais da pra derivar?

Tres perguntas que ficaram em aberto quando a micro-area foi escolhida como
agrupamento publicavel:

**A. O codigo de micro-area e unico na cidade, ou so dentro da equipe?**
No e-SUS a micro-area costuma ser numerada dentro da area da equipe. Se for
o caso aqui, "micro-area 01" nao e um lugar - sao varios lugares desconexos,
um por equipe. O k medido estaria inflado por juntar territorios distintos, e
o agrupamento publicado nao seria o que se afirmou que era. A chave correta
passaria a ser o par (equipe, micro-area).

**B. A micro-area e espacialmente compacta?**
Mesmo com codigo unico, so faz sentido publicar como geografia se os
domicilios dela estiverem de fato proximos. Mede-se a dispersao dos pontos em
torno do centro robusto de cada agrupamento: territorio real da dispersao de
centenas de metros; codigo reaproveitado da quilometros.

**C. Que features geograficas dao pra derivar antes da supressao?**
Zona urbana/rural e densidade local sao insumo valioso para o gerador
sintetico e nao sao identificador. Boa parte ja existe nativa no cadastro
domiciliar - este script enumera o que ha e com que cardinalidade.

Read-only, so agregado.
"""

from __future__ import annotations

import math

from _conexao import colunas_de, conectar, consulta, existe_tabela, gravar, titulo, uma

FONTE = "tb_cds_domicilio"
LIMITE_BBOX = "nu_latitude BETWEEN -34 AND 6 AND nu_longitude BETWEEN -74 AND -28"

# Caracteristicas do domicilio no cadastro: nao sao identificador geografico,
# sao atributo - e sao exatamente o tipo de feature que o gerador sintetico
# consome. `co_tipo_localizacao` e o urbano/rural.
CARACTERISTICAS = [
    ("co_tipo_localizacao", "tb_tipo_localizacao", "urbano / rural"),
    ("co_tipo_domicilio", "tb_tipo_domicilio", "tipo de domicílio"),
    ("co_tipo_situacao_moradia", "tb_tipo_situacao_moradia", "situação de moradia"),
    ("co_tipo_abstcmento_agua", "tb_tipo_abastecimento_agua", "abastecimento de água"),
    ("co_tipo_escmento_sntar", "tb_tipo_escoamento_sanitar", "esgotamento sanitário"),
    ("co_tipo_destino_lixo", "tb_tipo_destino_lixo", "destino do lixo"),
    ("co_tipo_material_parede", "tb_tipo_material_parede", "material da parede"),
    ("co_tipo_origem_energia_eletric", "tb_tipo_origem_energia_eletric", "energia elétrica"),
    ("co_tipo_acesso_dom", "tb_tipo_acesso_domicilio", "acesso ao domicílio"),
    ("co_tipo_posse_terra", "tb_tipo_posse_terra", "posse da terra"),
    ("co_tipo_tratamento_agua", "tb_tipo_tratamento_agua", "tratamento de água"),
]


def haversine_m(lat1, lng1, lat2, lng2):
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def mediana(v):
    if not v:
        return None
    v = sorted(v)
    return v[len(v) // 2]


def dispersao(pontos):
    """Distancia mediana ao centro robusto (mediana por componente).

    Robusto a outlier: um ponto errado nao infla o resultado como o
    desvio-padrao inflaria.
    """
    if len(pontos) < 2:
        return None
    clat = mediana([p[0] for p in pontos])
    clng = mediana([p[1] for p in pontos])
    return mediana([haversine_m(la, ln, clat, clng) for la, ln in pontos])


def main() -> None:
    conn = conectar()
    rel: dict = {}

    if not existe_tabela(conn, FONTE):
        raise SystemExit(f"{FONTE} ausente")
    cols = colunas_de(conn, FONTE)
    col_eq = next((c for c in ("nu_ine", "nu_cnes") if c in cols), None)

    # ---------------------------------------------------------------- A
    titulo("A - O código de micro-área é único na cidade?")
    if "nu_micro_area" not in cols or not col_eq:
        print("  faltam nu_micro_area ou coluna de equipe - pulando")
    else:
        r = uma(
            conn,
            f"""
            SELECT count(DISTINCT nu_micro_area)                        AS so_codigo,
                   count(DISTINCT ("{col_eq}", nu_micro_area))          AS par,
                   count(DISTINCT "{col_eq}")                           AS equipes
            FROM public."{FONTE}"
            WHERE nu_micro_area IS NOT NULL AND btrim(nu_micro_area) <> ''
            """,
        )
        if isinstance(r, dict):
            print("  erro:", r["erro"])
        else:
            so, par, eq = r
            rel["unicidade"] = {
                "coluna_equipe": col_eq, "codigos_distintos": so,
                "pares_distintos": par, "equipes": eq,
                "codigo_reaproveitado": par > so,
            }
            print(f"  códigos de micro-área distintos ......... {so}")
            print(f"  pares (equipe, micro-área) distintos .... {par}")
            print(f"  equipes ................................. {eq}")
            if par > so:
                print(f"\n  >>> CÓDIGO REAPROVEITADO entre equipes.")
                print(f"  >>> 'micro-área X' não é um lugar: são até {par - so} lugares a mais")
                print(f"  >>> que o código sugere. O agrupamento correto é o PAR.")
            else:
                print("\n  >>> Código único na cidade: micro-área sozinha identifica o território.")

    # ---------------------------------------------------------------- B
    titulo("B - A micro-área é espacialmente compacta?")
    if "nu_micro_area" not in cols or "nu_latitude" not in cols:
        print("  sem micro-área ou sem coordenada - pulando")
    else:
        sel_eq = f'"{col_eq}"::text' if col_eq else "'-'"
        linhas = consulta(
            conn,
            f"""
            SELECT nu_micro_area::text, {sel_eq},
                   nu_latitude::double precision, nu_longitude::double precision
            FROM public."{FONTE}"
            WHERE nu_micro_area IS NOT NULL AND btrim(nu_micro_area) <> ''
              AND nu_latitude IS NOT NULL AND nu_longitude IS NOT NULL
              AND {LIMITE_BBOX}
            """,
        )
        if isinstance(linhas, dict):
            print("  erro:", linhas["erro"])
        else:
            por_codigo: dict[str, list] = {}
            por_par: dict[tuple, list] = {}
            for ma, eq, lat, lng in linhas:
                por_codigo.setdefault(ma, []).append((lat, lng))
                por_par.setdefault((eq, ma), []).append((lat, lng))

            rel["compacidade"] = {}
            for rotulo, grupos in (("só o código", por_codigo), ("par (equipe, micro-área)", por_par)):
                disp = [d for g in grupos.values() if (d := dispersao(g)) is not None]
                if not disp:
                    continue
                disp.sort()
                info = {
                    "grupos": len(grupos),
                    "mediana_m": round(disp[len(disp) // 2], 1),
                    "min_m": round(disp[0], 1),
                    "max_m": round(disp[-1], 1),
                }
                rel["compacidade"][rotulo] = info
                print(
                    f"  {rotulo:26} grupos={info['grupos']:>3}  "
                    f"dispersão mediana={info['mediana_m']:>9} m  "
                    f"(min {info['min_m']} / max {info['max_m']})"
                )
            print("\n  Território real tem dispersão de centenas de metros.")
            print("  Se o par for muito mais compacto que o código sozinho, confirma o item A.")

    # ---------------------------------------------------------------- C
    titulo("C - Features de domicílio já nativas (insumo do gerador)")
    rel["caracteristicas"] = {}
    for col, dim, rotulo in CARACTERISTICAS:
        if col not in cols:
            print(f"  {rotulo:24} ausente")
            continue
        r = uma(
            conn,
            f"""
            SELECT count(*), count("{col}"), count(DISTINCT "{col}")
            FROM public."{FONTE}"
            """,
        )
        if isinstance(r, dict):
            print(f"  {rotulo:24} erro")
            continue
        total, preenchidas, distintos = r
        pct = 100.0 * preenchidas / total if total else 0
        rel["caracteristicas"][col] = {
            "rotulo": rotulo, "preenchidas": preenchidas,
            "total": total, "cobertura_pct": round(pct, 1), "distintos": distintos,
        }
        print(f"  {rotulo:24} {distintos:>3} valores · {pct:5.1f}% preenchido")

        # Distribuicao do urbano/rural, que e a feature pedida explicitamente.
        if col == "co_tipo_localizacao" and existe_tabela(conn, dim):
            cols_dim = colunas_de(conn, dim)
            nome = next((c for c in cols_dim if c.startswith(("no_", "ds_"))), None)
            if nome:
                d = consulta(
                    conn,
                    f"""
                    SELECT d."{nome}"::text, count(*)
                    FROM public."{FONTE}" f
                    JOIN public."{dim}" d ON d."{col}" = f."{col}"
                    GROUP BY 1 ORDER BY 2 DESC
                    """,
                )
                if not isinstance(d, dict):
                    rel["urbano_rural"] = {k: v for k, v in d}
                    for k, v in d:
                        print(f"        {k:20} {v:>6} domicílios")

    titulo("Como ler")
    print("  A -> decide se o agrupamento publicável é micro-área ou (equipe, micro-área).")
    print("  B -> confirma que o agrupamento escolhido corresponde a um lugar.")
    print("  C -> lista o que dá pra publicar como atributo sem custo de privacidade.")

    gravar("05_geografia_derivada", rel)
    conn.close()


if __name__ == "__main__":
    main()
