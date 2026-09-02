"""Experimento 03 - largura da faixa de distancia e k do par (bucket, faixa).

BLOQUEADO ate `unidades_coordenadas.csv` estar preenchido: as unidades de
saude nao tem nenhuma coluna de coordenada na base, entao a distancia
cidadao<->unidade nao existe como dado e precisa ser criada. Sao 12
unidades - consulta manual ao cadastro publico do CNES, feita uma vez, e
antes da `02_anon_unidade_saude.py` rodar, que substitui o CNES.

O que mede, uma vez destravado:

1. distribuicao das distancias domicilio -> unidade de vinculo;
2. varredura de larguras de banda (100, 250, 500, 1000 m), reportando para
   cada uma o k do **par** (bucket geografico, faixa) - nao de cada um
   isoladamente. O anel em torno da unidade cruzado com o poligono do bucket
   pode ter intersecao pequena, e e esse par que vai ao publico.

Se o par violar o k minimo, as saidas sao alargar a banda (degrada a
distribuicao de distancia) ou subir um nivel de bucket (degrada a resolucao
espacial). A troca e explicita.

Read-only, so agregado.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

from _conexao import colunas_de, conectar, consulta, existe_tabela, gravar, titulo

CSV_UNIDADES = Path(__file__).resolve().parent / "unidades_coordenadas.csv"

LARGURAS_M = (100, 250, 500, 1000)
LIMIARES = (2, 5, 10, 20, 50)

# Domicilios geolocalizados, na ordem de preferencia.
FONTES_DOMICILIO = ["tb_cds_domicilio", "tb_cds_cad_domiciliar", "tb_fat_cad_domiciliar"]


def carregar_unidades() -> dict[str, tuple[float, float]]:
    """Le o CSV preenchido a mao. Linhas sem coordenada sao ignoradas."""
    if not CSV_UNIDADES.exists():
        return {}
    with CSV_UNIDADES.open(encoding="utf-8") as fh:
        # As linhas de comentario precisam sair antes do DictReader, senao a
        # primeira delas vira o cabecalho e todo campo sai como None.
        linhas = [linha for linha in fh if not linha.lstrip().startswith("#")]

    unidades: dict[str, tuple[float, float]] = {}
    for row in csv.DictReader(linhas):
        lat = (row.get("latitude") or "").strip()
        lng = (row.get("longitude") or "").strip()
        chave = (row.get("co_unidade") or row.get("nu_cnes") or "").strip()
        if not chave or not lat or not lng:
            continue
        try:
            unidades[chave] = (float(lat), float(lng))
        except ValueError:
            continue
    return unidades


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def quantis(valores: list[float]) -> dict:
    if not valores:
        return {}
    v = sorted(valores)
    def q(p: float) -> float:
        return round(v[min(len(v) - 1, int(p * len(v)))], 1)
    return {
        "n": len(v),
        "min": round(v[0], 1),
        "p25": q(0.25),
        "mediana": q(0.50),
        "p75": q(0.75),
        "p95": q(0.95),
        "max": round(v[-1], 1),
    }


def main() -> None:
    unidades = carregar_unidades()
    if not unidades:
        titulo("03 - BLOQUEADO")
        print(f"  {CSV_UNIDADES.name} vazio ou ausente.")
        print("  Preencha as 12 linhas com as coordenadas das unidades a partir")
        print("  do cadastro publico do CNES e rode de novo. Sem isso a distancia")
        print("  cidadao<->unidade nao existe como dado - nao ha o que medir.")
        return

    conn = conectar()
    titulo("03 - Faixa de distancia e k do par (bucket, faixa)")
    print(f"  unidades com coordenada: {len(unidades)}")

    fonte = next((t for t in FONTES_DOMICILIO if existe_tabela(conn, t)), None)
    if fonte is None:
        raise SystemExit("nenhuma tabela de domicilio encontrada")

    cols = colunas_de(conn, fonte)
    col_unidade = next(
        (c for c in ("nu_cnes", "co_unidade_saude", "co_dim_unidade_saude") if c in cols),
        None,
    )
    faltando = [c for c in ("nu_latitude", "nu_longitude") if c not in cols]
    if faltando or not col_unidade:
        raise SystemExit(
            f"{fonte}: falta {', '.join(faltando) or 'coluna de unidade'} - "
            "ajuste FONTES_DOMICILIO ou o mapeamento de unidade"
        )

    col_bucket = next(
        (c for c in ("no_bairro_filtro", "no_bairro", "nu_micro_area") if c in cols), None
    )
    print(f"  fonte={fonte}  unidade={col_unidade}  bucket={col_bucket}")

    linhas = consulta(
        conn,
        f"""
        SELECT "{col_unidade}"::text AS unidade,
               {f'upper(btrim("{col_bucket}"::text))' if col_bucket else "'-'"} AS bucket,
               nu_latitude::double precision  AS lat,
               nu_longitude::double precision AS lng
        FROM public."{fonte}"
        WHERE nu_latitude IS NOT NULL AND nu_longitude IS NOT NULL
          AND "{col_unidade}" IS NOT NULL
          AND nu_latitude BETWEEN -34 AND 6
          AND nu_longitude BETWEEN -74 AND -28
        """,
    )
    if isinstance(linhas, dict):
        raise SystemExit(f"consulta falhou: {linhas['erro']}")

    distancias: list[float] = []
    pares: list[tuple[str, float]] = []
    sem_unidade = 0
    for unidade, bucket, lat, lng in linhas:
        coord = unidades.get(unidade)
        if coord is None:
            sem_unidade += 1
            continue
        d = haversine_m(lat, lng, coord[0], coord[1])
        distancias.append(d)
        pares.append((bucket, d))

    print(f"  domicilios geolocalizados usados: {len(distancias)}")
    if sem_unidade:
        print(f"  ignorados por unidade sem coordenada no CSV: {sem_unidade}")
    if not distancias:
        raise SystemExit("nenhum domicilio casou com uma unidade do CSV")

    relatorio: dict = {
        "fonte": fonte,
        "coluna_unidade": col_unidade,
        "coluna_bucket": col_bucket,
        "unidades_no_csv": len(unidades),
        "domicilios_usados": len(distancias),
        "ignorados_sem_unidade": sem_unidade,
        "distancia_m": quantis(distancias),
        "larguras": {},
    }

    titulo("Distancia domicilio -> unidade de vinculo (metros)")
    for k, v in relatorio["distancia_m"].items():
        print(f"  {k}: {v}")

    titulo("k do par (bucket, faixa) por largura de banda")
    for largura in LARGURAS_M:
        classes: dict[tuple[str, int], int] = {}
        for bucket, d in pares:
            chave = (bucket, int(d // largura))
            classes[chave] = classes.get(chave, 0) + 1
        tamanhos = sorted(classes.values())
        entrada = {
            "n_classes": len(tamanhos),
            "k_min": tamanhos[0],
            "k_mediana": tamanhos[len(tamanhos) // 2],
            "k_max": tamanhos[-1],
        }
        for t in LIMIARES:
            entrada[f"classes_k_menor_{t}"] = sum(1 for n in tamanhos if n < t)
            entrada[f"linhas_k_menor_{t}"] = sum(n for n in tamanhos if n < t)
        relatorio["larguras"][f"{largura}m"] = entrada

        print(f"\n  banda de {largura} m")
        print(
            f"      classes={entrada['n_classes']}  k -> min={entrada['k_min']} "
            f"mediana={entrada['k_mediana']} max={entrada['k_max']}"
        )
        print(
            "      classes com k < "
            + "/".join(map(str, LIMIARES))
            + ": "
            + " / ".join(str(entrada[f"classes_k_menor_{t}"]) for t in LIMIARES)
        )
        print(
            "      linhas  em  k < "
            + "/".join(map(str, LIMIARES))
            + ": "
            + " / ".join(str(entrada[f"linhas_k_menor_{t}"]) for t in LIMIARES)
        )

    titulo("Como ler")
    print("A menor largura cujo k minimo do par satisfaca o minimo (20) e a")
    print("escolha. Se nenhuma satisfizer, subir um nivel de bucket antes de")
    print("alargar mais a banda - alargar degrada a distribuicao de distancia,")
    print("que e justamente a utilidade que se quer preservar.")

    gravar("03_faixa_de_distancia", relatorio)
    conn.close()


if __name__ == "__main__":
    main()
