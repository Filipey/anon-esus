"""Experimento 02 - tamanho de classe de equivalencia por nivel da hierarquia.

Elimina os niveis geograficos inviaveis antes de qualquer escolha. Para cada
nivel candidato mede o k duas vezes:

- **k isolado**: registros que compartilham o mesmo valor geografico. E o
  que a fase 1 precisa satisfazer.
- **k conjunto**: registros que compartilham geografia + sexo + mes/ano de
  nascimento. E o que a fase 2 vai encontrar quando acrescentar os
  demograficos ao conjunto de quase-identificadores.

Medir os dois de uma vez e o que evita retrabalho: um nivel que da k=20
sobre geografia isolada pode dar k=1 sobre o conjunto, e ai a granularidade
escolhida na fase 1 teria que ser refeita.

Niveis nativos da base. Setor censitario nao entra porque nao existe aqui -
exigiria a malha do IBGE e ponto-em-poligono sobre as coordenadas de
domicilio.

Read-only, so agregado.
"""

from __future__ import annotations

from _conexao import colunas_de, conectar, existe_tabela, gravar, titulo, uma

TABELA = "tb_cidadao"

# (rotulo, expressao SQL do bucket, colunas exigidas)
NIVEIS = [
    ("micro-area", '"nu_micro_area"', ["nu_micro_area"]),
    ("area / equipe", '"{equipe}"', []),          # coluna resolvida em runtime
    ("bairro (normalizado)", 'upper(btrim("no_bairro_filtro"))', ["no_bairro_filtro"]),
    ("bairro (texto livre)", 'upper(btrim("no_bairro"))', ["no_bairro"]),
    ("municipio", '"co_localidade_endereco"', ["co_localidade_endereco"]),
]

LIMIARES = (2, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100)

BASE = """
    WITH g AS (
        SELECT {bucket} AS bucket{extra}, count(*) AS n
        FROM public."{tab}"
        WHERE {filtro}
        GROUP BY 1{extra_group}
    )
    SELECT count(*)                                            AS n_classes,
           coalesce(sum(n), 0)                                 AS n_registros,
           min(n), max(n),
           percentile_disc(0.25) WITHIN GROUP (ORDER BY n)     AS p25,
           percentile_disc(0.50) WITHIN GROUP (ORDER BY n)     AS mediana,
           {filtros_classe},
           {filtros_linha}
    FROM g
"""

CAMPOS = ["n_classes", "n_registros", "min", "max", "p25", "mediana"]
CAMPOS += [f"classes_k_menor_{t}" for t in LIMIARES]
CAMPOS += [f"linhas_k_menor_{t}" for t in LIMIARES]


def _monta(bucket: str, filtro: str, com_demograficos: bool, sexo: str, nasc: str) -> str:
    extra = ""
    extra_group = ""
    if com_demograficos:
        extra = f', "{sexo}" AS sexo, date_trunc(\'month\', "{nasc}") AS mes_nasc'
        extra_group = ", 2, 3"
        filtro = f'{filtro} AND "{sexo}" IS NOT NULL AND "{nasc}" IS NOT NULL'
    return BASE.format(
        tab=TABELA,
        bucket=bucket,
        extra=extra,
        extra_group=extra_group,
        filtro=filtro,
        filtros_classe=", ".join(
            f"count(*) FILTER (WHERE n < {t}) AS classes_k_menor_{t}" for t in LIMIARES
        ),
        filtros_linha=", ".join(
            f"coalesce(sum(n) FILTER (WHERE n < {t}), 0) AS linhas_k_menor_{t}"
            for t in LIMIARES
        ),
    )


def _mostra(rotulo: str, d: dict) -> None:
    print(f"      classes={d['n_classes']}  registros={d['n_registros']}")
    print(
        f"      k -> min={d['min']} p25={d['p25']} "
        f"mediana={d['mediana']} max={d['max']}"
    )
    classes = " / ".join(str(d[f"classes_k_menor_{t}"]) for t in LIMIARES)
    linhas = " / ".join(str(d[f"linhas_k_menor_{t}"]) for t in LIMIARES)
    print(f"      classes com k < {'/'.join(map(str, LIMIARES))}: {classes}")
    print(f"      linhas  em  k < {'/'.join(map(str, LIMIARES))}: {linhas}")


def main() -> None:
    conn = conectar()
    if not existe_tabela(conn, TABELA):
        raise SystemExit(f"tabela {TABELA} ausente")

    cols = colunas_de(conn, TABELA)
    col_equipe = next(
        (c for c in ("co_dim_equipe", "co_equipe", "nu_ine") if c in cols), None
    )
    col_sexo = next((c for c in ("co_sexo", "no_sexo", "tp_sexo") if c in cols), None)
    col_nasc = next((c for c in ("dt_nascimento",) if c in cols), None)

    relatorio: dict = {
        "tabela": TABELA,
        "coluna_equipe": col_equipe,
        "coluna_sexo": col_sexo,
        "coluna_nascimento": col_nasc,
        "niveis": {},
    }

    titulo("02 - k por nivel da hierarquia geografica")
    print(f"  equipe={col_equipe}  sexo={col_sexo}  nascimento={col_nasc}")
    if not (col_sexo and col_nasc):
        print("  AVISO: sem sexo ou data de nascimento, o k conjunto nao sera medido.")

    for rotulo, bucket_tpl, exigidas in NIVEIS:
        if rotulo.startswith("area"):
            if not col_equipe:
                print(f"\n  {rotulo}: sem coluna de equipe - pulando")
                continue
            bucket = bucket_tpl.format(equipe=col_equipe)
            filtro = f'"{col_equipe}" IS NOT NULL'
        else:
            faltando = [c for c in exigidas if c not in cols]
            if faltando:
                print(f"\n  {rotulo}: sem {', '.join(faltando)} - pulando")
                continue
            col = exigidas[0]
            filtro = f'"{col}" IS NOT NULL'
            if col.startswith(("no_", "nu_", "ds_")):
                filtro += f" AND btrim(\"{col}\"::text) <> ''"
            bucket = bucket_tpl

        print(f"\n  {rotulo}")
        entrada: dict = {}

        r = uma(conn, _monta(bucket, filtro, False, "", ""))
        if isinstance(r, dict):
            print(f"      [isolado] erro/timeout -> {r['erro']}")
            entrada["isolado"] = r
        else:
            d = dict(zip(CAMPOS, r))
            entrada["isolado"] = d
            print("      [k isolado]")
            _mostra(rotulo, d)

        if col_sexo and col_nasc:
            r = uma(conn, _monta(bucket, filtro, True, col_sexo, col_nasc))
            if isinstance(r, dict):
                print(f"      [conjunto] erro/timeout -> {r['erro']}")
                entrada["conjunto_fase2"] = r
            else:
                d = dict(zip(CAMPOS, r))
                entrada["conjunto_fase2"] = d
                print("      [k conjunto: + sexo + mes/ano de nascimento]")
                _mostra(rotulo, d)

        relatorio["niveis"][rotulo] = entrada

    # Area/equipe e unidade nao existem como coluna em tb_cidadao - vivem na
    # tabela de territorio do DW. Sem esta passagem o eixo favorecido era
    # simplesmente pulado em silencio, que foi o que aconteceu na primeira
    # rodada.
    TERRITORIO = "tb_fat_cidadao_territorio"
    if existe_tabela(conn, TERRITORIO):
        titulo(f"Niveis do territorio de saude ({TERRITORIO})")
        cols_t = colunas_de(conn, TERRITORIO)
        for rotulo, col in (
            ("micro-area (territorio)", "nu_micro_area"),
            ("area / equipe", "co_dim_equipe"),
            ("unidade", "co_dim_unidade_saude"),
        ):
            if col not in cols_t:
                print(f"\n  {rotulo}: sem {col} - pulando")
                continue

            filtro = f'"{col}" IS NOT NULL'
            if col.startswith(("no_", "nu_", "ds_")):
                filtro += f" AND btrim(\"{col}\"::text) <> ''"

            sql = BASE.format(
                tab=TERRITORIO,
                bucket=f'"{col}"',
                extra="",
                extra_group="",
                filtro=filtro,
                filtros_classe=", ".join(
                    f"count(*) FILTER (WHERE n < {t}) AS classes_k_menor_{t}" for t in LIMIARES
                ),
                filtros_linha=", ".join(
                    f"coalesce(sum(n) FILTER (WHERE n < {t}), 0) AS linhas_k_menor_{t}"
                    for t in LIMIARES
                ),
            )
            r = uma(conn, sql)
            print(f"\n  {rotulo}")
            if isinstance(r, dict):
                print(f"      erro/timeout -> {r['erro']}")
                relatorio["niveis"][rotulo] = {"isolado": r}
                continue
            d = dict(zip(CAMPOS, r))
            relatorio["niveis"][rotulo] = {"isolado": d}
            print("      [k isolado]")
            _mostra(rotulo, d)

    titulo("Como ler")
    print("Escolher o nivel mais fino cujo k isolado satisfaca o minimo (20) e")
    print("cujo k conjunto nao colapse para 1 - senao a fase 2 obriga a refazer")
    print("a granularidade. 'linhas em k < t' pesa quantas pessoas ficam")
    print("expostas, nao so quantas classes: uma classe rara com 3 pessoas")
    print("importa mais que dez classes raras com 1 registro cada.")

    gravar("02_k_por_nivel", relatorio)
    conn.close()


if __name__ == "__main__":
    main()
