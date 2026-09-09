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
LIMIARES = (2, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100)

# Acima disto, num municipio, e erro de coordenada ou vinculo cruzado - nao
# distancia real ate a propria unidade de vinculo.
LIMITE_SANIDADE_M = 25_000

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

    # Varre TODOS os buckets disponiveis, nao so um. O exp. 02 mostrou que
    # micro-area e area/equipe passam k=20 isoladas com folgas muito
    # diferentes (mediana 523 contra 2312), entao o par pode falhar numa e
    # passar na outra - e e essa comparacao que decide o desenho.
    CANDIDATOS_BUCKET = ["nu_micro_area", "nu_ine", "no_bairro_filtro"]
    buckets = [c for c in CANDIDATOS_BUCKET if c in cols]
    if not buckets:
        raise SystemExit(f"{fonte} nao tem nenhuma coluna de bucket reconhecida")

    sel_buckets = ", ".join(
        f'upper(btrim("{c}"::text)) AS b_{i}' for i, c in enumerate(buckets)
    )
    print(f"  fonte={fonte}  unidade={col_unidade}")
    print(f"  buckets a varrer: {', '.join(buckets)}")

    linhas = consulta(
        conn,
        f"""
        SELECT "{col_unidade}"::text AS unidade,
               {sel_buckets},
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
    pares_por_bucket: dict[str, list[tuple[str, float]]] = {c: [] for c in buckets}
    por_unidade: dict[str, list[float]] = {}
    sem_unidade = 0
    for linha in linhas:
        unidade = linha[0]
        vals = linha[1 : 1 + len(buckets)]
        lat, lng = linha[-2], linha[-1]
        coord = unidades.get(unidade)
        if coord is None:
            sem_unidade += 1
            continue
        d = haversine_m(lat, lng, coord[0], coord[1])
        distancias.append(d)
        for nome, v in zip(buckets, vals):
            pares_por_bucket[nome].append((v if v is not None else "-", d))
        por_unidade.setdefault(unidade, []).append(d)

    print(f"  domicilios geolocalizados usados: {len(distancias)}")
    if sem_unidade:
        print(f"  ignorados por unidade sem coordenada no CSV: {sem_unidade}")
    if not distancias:
        raise SystemExit("nenhum domicilio casou com uma unidade do CSV")

    relatorio: dict = {
        "fonte": fonte,
        "coluna_unidade": col_unidade,
        "buckets_varridos": buckets,
        "unidades_no_csv": len(unidades),
        "domicilios_usados": len(distancias),
        "ignorados_sem_unidade": sem_unidade,
        "distancia_m": quantis(distancias),
        "larguras": {},
    }

    titulo("Distancia domicilio -> unidade de vinculo (metros)")
    for k, v in relatorio["distancia_m"].items():
        print(f"  {k}: {v}")

    # Quebra por unidade. Uma UBS geocodificada no lugar errado desloca TODOS
    # os seus domicilios de uma vez, e boa parte deles cai abaixo do limite de
    # sanidade - passa pelo filtro de outlier e continua contaminando o k do
    # par. O sintoma e uma unidade com perfil de distancia destoante das
    # outras.
    titulo("Distancia por unidade (uma UBS deslocada aparece aqui)")
    relatorio["por_unidade"] = {}
    for unidade in sorted(por_unidade):
        ds = por_unidade[unidade]
        q = quantis(ds)
        lat_u, lng_u = unidades[unidade]
        fora_bbox = not (-34 <= lat_u <= 6 and -74 <= lng_u <= -28)
        q["fora_do_bbox_brasil"] = fora_bbox
        relatorio["por_unidade"][unidade] = q
        alerta = "  <-- COORDENADA FORA DO BRASIL" if fora_bbox else ""
        print(
            f"  {unidade}: n={q['n']:>5}  mediana={q['mediana']:>9}  "
            f"p95={q['p95']:>10}  max={q['max']:>11}{alerta}"
        )
    print("\n  Se uma unidade tem mediana muito acima das outras, a coordenada")
    print("  dela e a suspeita - nao os domicilios.")

    # Cauda implausivel: num municipio, domicilio a dezenas de km da propria
    # unidade de vinculo e coordenada errada ou vinculo cruzado, nao
    # realidade. Esses pontos viram classe de tamanho 1 nas faixas altas e
    # contaminam o k do par - por isso sao contados e reportados.
    fora = [d for d in distancias if d > LIMITE_SANIDADE_M]
    relatorio["fora_do_limite"] = {
        "limite_m": LIMITE_SANIDADE_M,
        "n": len(fora),
        "pct": round(100.0 * len(fora) / len(distancias), 2),
    }
    print(
        f"\n  acima de {LIMITE_SANIDADE_M / 1000:.0f} km: {len(fora)} "
        f"({relatorio['fora_do_limite']['pct']}%) - provavel erro de coordenada"
    )
    if fora:
        print("  a varredura abaixo roda com e sem esses pontos, para separar")
        print("  o efeito da largura da banda do efeito do dado sujo.")

    def varre(conjunto: list[tuple[str, float]], largura: int) -> dict:
        classes: dict[tuple[str, int], int] = {}
        for bucket, d in conjunto:
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
        return entrada

    def imprime(entrada: dict) -> None:
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

    # ---------------------------------------------------------------------
    # Esquemas de faixa com numero LIMITADO de bandas.
    #
    # Largura fixa e a discretizacao errada para uma distribuicao que varre
    # duas ordens de grandeza (p25=212m, p95=14km): perto da unidade junta
    # centenas numa classe so, longe deixa cada domicilio sozinho na sua
    # banda. Limitar o numero de faixas resolve os dois lados.
    # ---------------------------------------------------------------------
    def por_cortes_fixos(cortes: list[float]):
        def atribui(_bucket: str, d: float) -> int:
            for i, c in enumerate(cortes):
                if d < c:
                    return i
            return len(cortes)
        return atribui

    def por_quantil(conjunto: list[tuple[str, float]], n: int):
        agrupado: dict[str, list[float]] = {}
        for b, d in conjunto:
            agrupado.setdefault(b, []).append(d)
        cortes: dict[str, list[float]] = {}
        for b, ds in agrupado.items():
            ds.sort()
            cortes[b] = [ds[max(0, int(len(ds) * i / n) - 1)] for i in range(1, n)]

        def atribui(bucket: str, d: float) -> int:
            for i, c in enumerate(cortes.get(bucket, [])):
                if d < c:
                    return i
            return n - 1
        return atribui

    def varre_esquema(conjunto: list[tuple[str, float]], atribui) -> dict:
        classes: dict[tuple[str, int], int] = {}
        for bucket, d in conjunto:
            chave = (bucket, atribui(bucket, d))
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
        return entrada

    ESQUEMAS = [
        ("6 faixas fixas (250/500/1k/2.5k/5k)", lambda c: por_cortes_fixos([250, 500, 1000, 2500, 5000])),
        ("4 faixas fixas (500/1.5k/5k)", lambda c: por_cortes_fixos([500, 1500, 5000])),
        ("quartis por bucket", lambda c: por_quantil(c, 4)),
        ("tercis por bucket", lambda c: por_quantil(c, 3)),
    ]

    titulo("k do par por ESQUEMA de faixa (numero limitado de bandas)")
    relatorio["esquemas"] = {}
    for nome_bucket in buckets:
        limpos = [(b, d) for b, d in pares_por_bucket[nome_bucket] if d <= LIMITE_SANIDADE_M]
        n_l = len(limpos)
        relatorio["esquemas"][nome_bucket] = {}
        print(f"\n  bucket = {nome_bucket}  (n={n_l}, sem outliers)")
        for rotulo, construtor in ESQUEMAS:
            e = varre_esquema(limpos, construtor(limpos))
            pct = 100.0 * e["linhas_k_menor_20"] / n_l if n_l else 0.0
            e["pct_supressao_k20"] = round(pct, 1)
            relatorio["esquemas"][nome_bucket][rotulo] = e
            veredito = "PASSA" if e["k_min"] >= 20 else f"{pct:.1f}% a suprimir"
            print(
                f"      {rotulo:36} classes={e['n_classes']:>4}  "
                f"k_min={e['k_min']:>3}  k_med={e['k_mediana']:>4}  -> {veredito}"
            )

    relatorio["larguras"] = {}
    for nome_bucket in buckets:
        pares = pares_por_bucket[nome_bucket]
        pares_limpos = [(b, d) for b, d in pares if d <= LIMITE_SANIDADE_M]
        n_limpos = len(pares_limpos)

        titulo(f"k do par ({nome_bucket}, faixa) por largura de banda")
        relatorio["larguras"][nome_bucket] = {}
        for largura in LARGURAS_M:
            entrada = {"todos": varre(pares, largura)}
            print(f"\n  banda de {largura} m — todos os pontos")
            imprime(entrada["todos"])

            if n_limpos < len(pares):
                lim = varre(pares_limpos, largura)
                entrada["sem_outliers"] = lim
                pct = 100.0 * lim["linhas_k_menor_20"] / n_limpos if n_limpos else 0.0
                print(f"  banda de {largura} m — sem os acima de {LIMITE_SANIDADE_M / 1000:.0f} km")
                imprime(lim)
                print(f"      -> {pct:.1f}% das linhas precisariam de supressao")

            relatorio["larguras"][nome_bucket][f"{largura}m"] = entrada

    titulo("Como ler")
    print("A menor largura cujo k minimo do par satisfaca o minimo (20) e a")
    print("escolha. Se nenhuma satisfizer, subir um nivel de bucket antes de")
    print("alargar mais a banda - alargar degrada a distribuicao de distancia,")
    print("que e justamente a utilidade que se quer preservar.")

    gravar("03_faixa_de_distancia", relatorio)
    conn.close()


if __name__ == "__main__":
    main()
