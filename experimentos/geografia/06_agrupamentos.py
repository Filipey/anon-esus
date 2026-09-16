"""Experimento 06 - qual agrupamento geografico publicar?

O experimento 05 derrubou a escolha anterior: o codigo de micro-area e
reaproveitado entre equipes (12 codigos para 29 pares), entao "micro-area 01"
nao e um lugar. E o par (equipe, micro-area) tambem nao se mostrou compacto -
provavelmente porque o INE gravado no cadastro domiciliar e a equipe que
*fez* o cadastro, nao necessariamente a que cobre o domicilio.

Este experimento compara os candidatos lado a lado, medindo as quatro coisas
que importam ao mesmo tempo:

  k isolado     tamanho da classe de equivalencia
  compacidade   distancia mediana dos domicilios ao centro robusto do grupo
  pureza        fracao do grupo na categoria urbano/rural majoritaria
  k do par      k de (agrupamento, tercil de distancia) - o que vai publicado

Candidatos:

  equipe                 nu_ine sozinho
  par                    (nu_ine, nu_micro_area)
  micro-area             nu_micro_area sozinho - a recomendacao derrubada
  MDAV k=20              agrupamento espacial construido a partir das coordenadas
  MDAV k=20 estratificado  idem, separando urbano de rural

MDAV (Maximum Distance to Average Vector) e o algoritmo classico de
microagregacao em controle estatistico de divulgacao. Ele produz grupos de
tamanho ~k **compactos por construcao**, o que resolve de uma vez os dois
problemas: garante o k e garante que o grupo corresponde a um lugar. O custo
e que o grupo resultante nao tem significado operacional - "cluster 7" nao e
uma equipe nem uma micro-area.

Read-only, so agregado.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

from _conexao import colunas_de, conectar, consulta, existe_tabela, gravar, titulo

FONTE = "tb_cds_domicilio"
CSV_UNIDADES = Path(__file__).resolve().parent / "unidades_coordenadas.csv"

K_ALVO = 20
LIMIARES = (2, 3, 5, 8, 10, 12, 15, 20, 25, 30, 40, 50)
N_TERCIS = 3
LIMITE_SANIDADE_M = 25_000


# --------------------------------------------------------------- geometria
def projetar(lats: np.ndarray, lngs: np.ndarray) -> np.ndarray:
    """Equirretangular local: metros aproximados, suficiente num municipio."""
    lat0, lng0 = lats.mean(), lngs.mean()
    x = (lngs - lng0) * 111_320 * math.cos(math.radians(lat0))
    y = (lats - lat0) * 111_320
    return np.column_stack([x, y])


def dispersao(pts: np.ndarray) -> float | None:
    """Distancia mediana ao centro robusto (mediana por componente)."""
    if len(pts) < 2:
        return None
    centro = np.median(pts, axis=0)
    return float(np.median(np.linalg.norm(pts - centro, axis=1)))


def mdav(pts: np.ndarray, k: int) -> np.ndarray:
    """Microagregacao MDAV. Devolve o rotulo de grupo de cada ponto.

    A cada passo: pega o ponto mais distante do centroide dos restantes e
    seus k-1 vizinhos; depois o mais distante desse e seus k-1 vizinhos.
    Grupos saem com tamanho ~k e compactos por construcao.
    """
    n = len(pts)
    restantes = np.arange(n)
    rotulos = np.full(n, -1, dtype=int)
    c = 0

    while len(restantes) >= 2 * k:
        X = pts[restantes]
        centro = X.mean(axis=0)
        i = int(np.argmax(((X - centro) ** 2).sum(axis=1)))

        dr = ((X - X[i]) ** 2).sum(axis=1)
        grupo_r = restantes[np.argsort(dr)[:k]]

        j = int(np.argmax(dr))
        ds = ((X - X[j]) ** 2).sum(axis=1)
        tomados = set(grupo_r.tolist())
        grupo_s: list[int] = []
        for idx in np.argsort(ds):
            g = int(restantes[idx])
            if g not in tomados:
                grupo_s.append(g)
            if len(grupo_s) == k:
                break

        rotulos[grupo_r] = c
        rotulos[np.array(grupo_s, dtype=int)] = c + 1
        c += 2
        usados = tomados | set(grupo_s)
        restantes = np.array([x for x in restantes if int(x) not in usados], dtype=int)

    if len(restantes) >= k:
        rotulos[restantes] = c
    elif len(restantes):
        # Sobra menor que k: cada ponto vai para o grupo cujo centro esta mais
        # proximo, em vez de formar uma classe abaixo do limiar.
        centros = {
            g: pts[rotulos == g].mean(axis=0) for g in np.unique(rotulos[rotulos >= 0])
        }
        for idx in restantes:
            melhor = min(centros, key=lambda g: np.linalg.norm(pts[idx] - centros[g]))
            rotulos[idx] = melhor
    return rotulos


# ------------------------------------------------------ perda de informacao
#
# Hierarquia de generalizacao de valores (HGV) do endereco, do mais fino ao
# mais grosso. So os niveis que **aninham** entram: o codigo de micro-area
# sozinho nao aninha (e reaproveitado entre equipes, entao "micro-area 01" nao
# e subconjunto de nenhum territorio unico), e o agrupamento espacial e outra
# hierarquia. Para esses, ILoss e calculavel - so precisa dos tamanhos de
# grupo - mas Prec nao, porque Prec depende da altura na HGV.
#
#   0  endereco exato          (folha)
#   1  (equipe, micro-area)
#   2  equipe
#   3  suprimido               (raiz)
#
ALTURA_HGV = 3
ALTURA_DO_NIVEL = {
    "par (equipe, micro-área)": 1,
    "equipe (INE)": 2,
}


def perda_de_informacao(tamanhos: list[int], n: int, altura: int | None) -> dict:
    """ILoss e Prec de um agrupamento.

    ILoss(D) = (1/|D|) * soma_i (|Vg_i| - 1) / |D_A|

    Tomando a folha da hierarquia como o domicilio individual, |D_A| = |D| e
    |Vg_i| = tamanho da classe onde o registro i caiu. Somando por classe em
    vez de por registro, isso vira sum(n_c * (n_c - 1)) / |D|^2. Vale 0 quando
    nada e generalizado e tende a 1 na supressao total.

    Prec(D) = 1 - (1/(|D| * Na)) * soma h / |HGV|. Com um unico atributo QI
    generalizado uniformemente, reduz a 1 - h/|HGV|. Fica None para
    agrupamentos que nao sao no da HGV do endereco.
    """
    iloss = sum(c * (c - 1) for c in tamanhos) / (n * n)
    return {
        "iloss": round(iloss, 4),
        "prec": round(1 - altura / ALTURA_HGV, 4) if altura is not None else None,
    }


def iloss_com_supressao(tamanhos: list[int], n: int, k: int) -> float:
    """ILoss do agrupamento quando toda classe menor que k e suprimida.

    Suprimir e generalizar ate a raiz da HGV: o registro passa a ter |Vg| = |D|
    e contribui (|D| - 1) / |D|, o custo maximo que um registro pode ter. As
    classes que sobrevivem contribuem como antes.

    E isso que torna ILoss comparavel a curva de supressao: as duas viram
    funcao do mesmo k. A curva de supressao diz *quantos* registros se perde;
    esta diz *quanta informacao* se perde, contando tambem o que a
    generalizacao ja custava antes de qualquer supressao.
    """
    vivos = sum(c * (c - 1) for c in tamanhos if c >= k)
    suprimidos = sum(c for c in tamanhos if c < k)
    return round((vivos + suprimidos * (n - 1)) / (n * n), 4)


# ------------------------------------------------------------------ metricas
def avaliar(nome, chaves, pts: np.ndarray, urbano, tercis=None) -> dict:
    grupos: dict[object, list[int]] = {}
    for i, ch in enumerate(chaves):
        grupos.setdefault(ch, []).append(i)

    tamanhos = sorted(len(v) for v in grupos.values())
    disp = [d for v in grupos.values() if (d := dispersao(pts[v])) is not None]
    disp.sort()

    purezas = []
    for v in grupos.values():
        vals = [urbano[i] for i in v if urbano[i] is not None]
        if vals:
            purezas.append(max(vals.count(x) for x in set(vals)) / len(vals))
    purezas.sort()

    out = {
        "n_grupos": len(grupos),
        "tamanho_min": tamanhos[0],
        "tamanho_mediana": tamanhos[len(tamanhos) // 2],
        "tamanho_max": tamanhos[-1],
        "compacidade_mediana_m": round(disp[len(disp) // 2], 1) if disp else None,
        "compacidade_pior_m": round(disp[-1], 1) if disp else None,
        "pureza_urbano_rural_mediana": round(purezas[len(purezas) // 2], 3) if purezas else None,
    }
    n_total = sum(tamanhos)
    for t in LIMIARES:
        out[f"linhas_k_menor_{t}"] = sum(n for n in tamanhos if n < t)
        out[f"iloss_k_{t}"] = iloss_com_supressao(tamanhos, n_total, t)

    out.update(perda_de_informacao(tamanhos, n_total, ALTURA_DO_NIVEL.get(nome)))

    if tercis is not None:
        pares: dict[tuple, list[int]] = {}
        for i, ch in enumerate(chaves):
            pares.setdefault((ch, tercis[i]), []).append(i)
        tp = sorted(len(v) for v in pares.values())
        out["par_n_classes"] = len(tp)
        out["par_k_min"] = tp[0]
        out["par_k_mediana"] = tp[len(tp) // 2]
        # ILoss do que efetivamente vai publicado: as classes do par.
        out["par_iloss"] = perda_de_informacao(tp, n_total, None)["iloss"]
        for t in LIMIARES:
            out[f"par_linhas_k_menor_{t}"] = sum(n for n in tp if n < t)
            out[f"par_iloss_k_{t}"] = iloss_com_supressao(tp, n_total, t)

        # Extensao espacial do que efetivamente vai publicado.
        #
        # A compacidade medida acima e a do agrupamento ANTES do tercil. Mas a
        # celula publicada e (territorio ∩ anel de distancia ate a unidade), que
        # e menor - entao aquele numero descreve o agrupamento, nao a classe, e
        # superestima a area que o atacante precisa varrer.
        #
        # E a segunda grandeza do problema: k limita quantos candidatos, nao
        # quanta localizacao. Publicar o k sem este numero e responder metade da
        # pergunta - a mesma objecao que derrubou o MDAV, aplicada a escolha.
        disp_par = [d for v in pares.values() if (d := dispersao(pts[v])) is not None]
        if disp_par:
            disp_par.sort()
            out["par_compacidade_mediana_m"] = round(disp_par[len(disp_par) // 2], 1)
            out["par_compacidade_min_m"] = round(disp_par[0], 1)
            out["par_compacidade_pior_m"] = round(disp_par[-1], 1)
            # A lista inteira: sao poucas classes, e e nela que se ve se alguma
            # delas ficou fina demais e pede fusao de tercil.
            out["par_compacidades_m"] = [round(d, 1) for d in disp_par]
    return out


def tercis_por_grupo(chaves, distancias, n=N_TERCIS):
    """Faixa por quantil dentro de cada agrupamento."""
    por_grupo: dict[object, list[float]] = {}
    for ch, d in zip(chaves, distancias):
        por_grupo.setdefault(ch, []).append(d)
    cortes = {}
    for ch, ds in por_grupo.items():
        ds = sorted(ds)
        cortes[ch] = [ds[max(0, int(len(ds) * i / n) - 1)] for i in range(1, n)]
    saida = []
    for ch, d in zip(chaves, distancias):
        faixa = n - 1
        for i, c in enumerate(cortes[ch]):
            if d < c:
                faixa = i
                break
        saida.append(faixa)
    return saida


def carregar_unidades() -> dict[str, tuple[float, float]]:
    if not CSV_UNIDADES.exists():
        return {}
    with CSV_UNIDADES.open(encoding="utf-8") as fh:
        linhas = [l for l in fh if not l.lstrip().startswith("#")]
    un = {}
    for row in csv.DictReader(linhas):
        lat, lng = (row.get("latitude") or "").strip(), (row.get("longitude") or "").strip()
        ch = (row.get("co_unidade") or row.get("nu_cnes") or "").strip()
        if ch and lat and lng:
            try:
                un[ch] = (float(lat), float(lng))
            except ValueError:
                pass
    return un


def haversine_m(lat1, lng1, lat2, lng2):
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def main() -> None:
    conn = conectar()
    if not existe_tabela(conn, FONTE):
        raise SystemExit(f"{FONTE} ausente")
    cols = colunas_de(conn, FONTE)

    precisa = ["nu_latitude", "nu_longitude", "nu_micro_area", "nu_ine"]
    faltando = [c for c in precisa if c not in cols]
    if faltando:
        raise SystemExit(f"{FONTE}: faltam {', '.join(faltando)}")
    tem_loc = "co_tipo_localizacao" in cols
    tem_cnes = "nu_cnes" in cols

    titulo("06 - Comparação de agrupamentos geográficos")
    linhas = consulta(
        conn,
        f"""
        SELECT nu_latitude::double precision, nu_longitude::double precision,
               nu_micro_area::text, nu_ine::text,
               {"co_tipo_localizacao::text" if tem_loc else "NULL::text"},
               {"nu_cnes::text" if tem_cnes else "NULL::text"}
        FROM public."{FONTE}"
        WHERE nu_latitude IS NOT NULL AND nu_longitude IS NOT NULL
          AND nu_latitude BETWEEN -34 AND 6 AND nu_longitude BETWEEN -74 AND -28
          AND nu_micro_area IS NOT NULL AND btrim(nu_micro_area) <> ''
        """,
    )
    if isinstance(linhas, dict):
        raise SystemExit(f"consulta falhou: {linhas['erro']}")

    lats = np.array([r[0] for r in linhas])
    lngs = np.array([r[1] for r in linhas])
    micro = [r[2] for r in linhas]
    ine = [r[3] for r in linhas]
    urbano = [r[4] for r in linhas]
    cnes = [r[5] for r in linhas]
    pts = projetar(lats, lngs)
    print(f"  domicílios geolocalizados com micro-área: {len(linhas)}")

    # Tercil de distancia, se as coordenadas das unidades estiverem disponiveis.
    unidades = carregar_unidades()
    distancias = None
    if unidades and tem_cnes:
        d = []
        ok = True
        for la, ln, c in zip(lats, lngs, cnes):
            co = unidades.get(c)
            if co is None:
                ok = False
                break
            d.append(haversine_m(la, ln, co[0], co[1]))
        if ok:
            distancias = d
            print(f"  distância calculada para as {len(unidades)} unidades do CSV")
    if distancias is None:
        print("  AVISO: unidades_coordenadas.csv ausente ou incompleto —")
        print("         o k do PAR (agrupamento, tercil) não será medido.")

    candidatos: dict[str, list] = {
        "equipe (INE)": ine,
        "par (equipe, micro-área)": list(zip(ine, micro)),
        "micro-área só": micro,
    }

    print(f"\n  construindo MDAV com k={K_ALVO}...")
    candidatos[f"MDAV k={K_ALVO}"] = [f"c{g}" for g in mdav(pts, K_ALVO)]

    if tem_loc:
        rot = np.full(len(linhas), "", dtype=object)
        for zona in {u for u in urbano if u}:
            idx = np.array([i for i, u in enumerate(urbano) if u == zona])
            if len(idx) < 2 * K_ALVO:
                rot[idx] = [f"{zona}-c0"] * len(idx)
                continue
            sub = mdav(pts[idx], K_ALVO)
            for i, g in zip(idx, sub):
                rot[i] = f"{zona}-c{g}"
        semzona = [i for i, u in enumerate(urbano) if not u]
        for i in semzona:
            rot[i] = "sem-zona"
        candidatos[f"MDAV k={K_ALVO} estratificado"] = list(rot)

    rel = {
        "fonte": FONTE,
        "domicilios": len(linhas),
        "k_alvo": K_ALVO,
        "com_tercil": distancias is not None,
        "agrupamentos": {},
    }

    titulo("Resultado")
    cab = (f"  {'agrupamento':30} {'grupos':>7} {'k mín':>6} {'compac.':>9} "
           f"{'pureza':>7} {'ILoss':>7} {'Prec':>6}")
    print(cab)
    print("  " + "-" * (len(cab) - 2))
    for nome, chaves in candidatos.items():
        tercis = tercis_por_grupo(chaves, distancias) if distancias else None
        m = avaliar(nome, chaves, pts, urbano, tercis)
        rel["agrupamentos"][nome] = m
        comp = f"{m['compacidade_mediana_m']:.0f} m" if m["compacidade_mediana_m"] else "—"
        pur = f"{m['pureza_urbano_rural_mediana']:.2f}" if m["pureza_urbano_rural_mediana"] else "—"
        prec = f"{m['prec']:.3f}" if m["prec"] is not None else "—"
        print(
            f"  {nome:30} {m['n_grupos']:>7} {m['tamanho_min']:>6} "
            f"{comp:>9} {pur:>7} {m['iloss']:>7.4f} {prec:>6}"
        )

    if distancias:
        titulo("Extensão espacial da classe publicada")
        print("  O tercil corta o território em anéis: a célula publicada é menor")
        print("  que o agrupamento. É a área que o atacante precisa varrer.\n")
        cab2 = f"  {'agrupamento':30} {'agrupamento':>12} {'classe publ.':>13} {'mais fina':>11}"
        print(cab2)
        print("  " + "-" * (len(cab2) - 2))
        for nome, m in rel["agrupamentos"].items():
            if m.get("par_compacidade_mediana_m") is None:
                continue
            print(
                f"  {nome:30} {m['compacidade_mediana_m']:>10.0f} m "
                f"{m['par_compacidade_mediana_m']:>11.0f} m "
                f"{m['par_compacidade_min_m']:>9.0f} m"
            )
        esc = rel["agrupamentos"].get("equipe (INE)", {})
        if esc.get("par_compacidades_m"):
            print(f"\n  classes publicadas da escolha, da mais fina à mais larga:")
            print("   ", " · ".join(f"{d:.0f} m" for d in esc["par_compacidades_m"]))

        titulo(f"k do par (agrupamento, tercil) — o que vai publicado")
        for nome, m in rel["agrupamentos"].items():
            n = rel["domicilios"]
            pct = 100.0 * m["par_linhas_k_menor_20"] / n
            veredito = "PASSA" if m["par_k_min"] >= 20 else f"{pct:.1f}% a suprimir"
            print(
                f"  {nome:30} classes={m['par_n_classes']:>4} "
                f"k_mín={m['par_k_min']:>4}  ILoss={m['par_iloss']:.4f}  ->  {veredito}"
            )

    titulo("Como ler")
    print("  compacidade = distância mediana dos domicílios ao centro do grupo.")
    print("     território real fica na casa das centenas de metros.")
    print("  pureza = fração do grupo na categoria urbano/rural majoritária.")
    print("     1,00 = grupo homogêneo; 0,50 = metade urbano, metade rural.")
    print("  ILoss = perda de informação por generalização: 0 = nada perdido,")
    print("     1 = supressão total. Calculável para qualquer partição.")
    print("  ILoss(k) = o mesmo, já contando a supressão que o k exigido impõe —")
    print("     é a curva que a figura iloss_por_k desenha.")
    print("  Prec = 1 - h/|HGV|: só existe para nível que pertence à hierarquia")
    print("     do endereço. Micro-área sozinha e MDAV não são nós dela.")
    print("  compacidade da classe publicada = raio efetivo que o registro revela.")
    print("     k limita quantos candidatos; este número limita quanta localização.")
    print("     São grandezas distintas, e as duas precisam ser reportadas.")
    print("  O agrupamento a publicar é o que passa no k do par E é compacto E é puro,")
    print("     com o menor ILoss entre os que passam.")

    gravar("06_agrupamentos", rel)
    conn.close()


if __name__ == "__main__":
    main()
