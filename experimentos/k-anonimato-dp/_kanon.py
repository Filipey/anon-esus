"""Algoritmos de k-anonimato da metodologia final.

Funções puras sobre DataFrames, para a varredura de k medir em memória e as
migrations reaproveitarem depois. Nenhuma toca o banco.

Núcleo de quase-identificadores (QI): sexo, data de nascimento, equipe,
tercil de distância, raça/cor.

1. `nucleo`: generaliza até todo grupo (sexo, equipe, tercil, raça/cor)
   publicado ter >= k pessoas — primeiro suprime a raça/cor de quem está em
   grupo pequeno, depois o tercil (que é do domicílio: suprime para a família
   inteira). Equipe não entra na hierarquia: ela aparece em cada atendimento,
   suprimi-la no vínculo não esconderia nada — e sexo x equipe já tem
   centenas de pessoas. Depois, dentro de cada grupo, microagrega a data de
   nascimento: ordena e corta em blocos consecutivos de >= k pessoas; todos
   do bloco recebem a mesma data (a menor do bloco, para ninguém "nascer"
   depois do próprio atendimento, ou a mediana).
2. `raros_para_outro`: valor de QI fora do núcleo com < k pessoas vira nulo.
3. `antropometria`: por variável, corta extremos (erros de digitação) e
   microagrega por valor — blocos consecutivos de valores com >= k pessoas
   distintas, cada valor vira a média do bloco. A regra depende só do valor,
   então o mesmo peso vira o mesmo número em qualquer tabela.
4. `diagnosticos`: código CID/CIAP com < k pessoas (no contexto escolhido)
   sobe na hierarquia até alcançar k ou chegar ao capítulo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

NULO = "∅"  # categoria publicada para valor ausente ou suprimido


# ------------------------------------------------------------ núcleo
def _rotulo(serie: pd.Series) -> pd.Series:
    return serie.astype(object).where(serie.notna(), NULO).astype(str)


def nucleo(pes: pd.DataFrame, k: int, representante: str = "min") -> pd.DataFrame:
    """Devolve, por pessoa, os QI publicados e o nível de generalização.

    Colunas de entrada: id, sexo, dt_nasc, equipe, tercil, raca_cor, domicilio.
    """
    df = pes[["id", "sexo", "dt_nasc", "equipe", "tercil", "raca_cor", "domicilio"]].copy()
    df["raca_pub"] = _rotulo(df["raca_cor"])
    df["tercil_pub"] = _rotulo(df["tercil"])
    df["equipe_pub"] = _rotulo(df["equipe"])
    df["sexo_pub"] = _rotulo(df["sexo"])
    chave = ["sexo_pub", "equipe_pub", "tercil_pub", "raca_pub"]

    df["raca_suprimida"] = False
    df["tercil_suprimido"] = False
    for _ in range(50):
        tam = df.groupby(chave)["id"].transform("size")
        pequeno = tam < k
        if not pequeno.any():
            break
        # 1º passo: suprime raça/cor de quem ainda a tem publicada
        alvo = pequeno & (df["raca_pub"] != NULO)
        if alvo.any():
            df.loc[alvo, "raca_pub"] = NULO
            df.loc[alvo, "raca_suprimida"] = True
            continue
        # 2º passo: suprime o tercil do domicílio inteiro
        alvo = pequeno & (df["tercil_pub"] != NULO)
        if alvo.any():
            doms = set(df.loc[alvo & df["domicilio"].notna(), "domicilio"])
            fam = df["domicilio"].isin(doms) | alvo
            df.loc[fam & (df["tercil_pub"] != NULO), "tercil_suprimido"] = True
            df.loc[fam, "tercil_pub"] = NULO
            continue
        break  # sobra só sexo x equipe < k: tratado na microagregação (bloco único)

    df["dt_nasc_pub"] = pd.NaT
    df["bloco"] = -1
    proximo = 0
    for _, g in df.sort_values("dt_nasc").groupby(chave, sort=False):
        idx = g.index.to_numpy()
        n = len(idx)
        nblocos = max(1, n // k)
        cortes = np.array_split(idx, nblocos)  # blocos consecutivos de >= k (ou o grupo todo)
        for b in cortes:
            datas = df.loc[b, "dt_nasc"]
            rep = datas.min() if representante == "min" else datas.sort_values().iloc[len(b) // 2]
            df.loc[b, "dt_nasc_pub"] = rep
            df.loc[b, "bloco"] = proximo
            proximo += 1
    df["desloc_dias"] = (df["dt_nasc"] - df["dt_nasc_pub"]).dt.days
    return df


def nucleo_data_primeiro(pes: pd.DataFrame, k: int, representante: str = "mediana",
                         fator_bloco: float = 1.0) -> pd.DataFrame:
    """Variante que prioriza a precisão da data de nascimento.

    1. Dentro de sexo x equipe (grupos de centenas), corta a data em blocos
       consecutivos de >= k*fator_bloco pessoas e publica um representante
       por bloco. Com grupos grandes há bebês suficientes para os blocos deles
       serem estreitos.
    2. Dentro de cada bloco, subgrupo (tercil, raça/cor) com < k pessoas tem a
       raça suprimida; se ainda < k, o tercil (do domicílio inteiro).
    3. O subgrupo (sem tercil, sem raça) do bloco, se ficar com 0 < n < k,
       absorve subgrupos inteiros do mesmo bloco, do menor para o maior, até
       chegar a k. Como o bloco tem >= k pessoas, sempre termina: o k vale
       para todos, exceto um grupo sexo x equipe inteiro menor que k.
    Supressão de tercil afeta a família em outros blocos; repete até estabilizar.
    """
    df = pes[["id", "sexo", "dt_nasc", "equipe", "tercil", "raca_cor", "domicilio"]].copy()
    df["sexo_pub"] = _rotulo(df["sexo"])
    df["equipe_pub"] = _rotulo(df["equipe"])
    df["raca_pub"] = _rotulo(df["raca_cor"])
    df["tercil_pub"] = _rotulo(df["tercil"])

    tamanho = max(k, int(round(k * fator_bloco)))
    df["bloco"] = -1
    df["dt_nasc_pub"] = pd.NaT
    proximo = 0
    for _, g in df.sort_values("dt_nasc").groupby(["sexo_pub", "equipe_pub"], sort=False):
        idx = g.index.to_numpy()
        for b in np.array_split(idx, max(1, len(idx) // tamanho)):
            datas = df.loc[b, "dt_nasc"].sort_values()
            rep = datas.iloc[0] if representante == "min" else datas.iloc[len(b) // 2]
            df.loc[b, "dt_nasc_pub"] = rep
            df.loc[b, "bloco"] = proximo
            proximo += 1

    sub = ["bloco", "tercil_pub", "raca_pub"]
    for _ in range(200):
        mudou = False
        tam = df.groupby(sub)["id"].transform("size")
        alvo = (tam < k) & (df["raca_pub"] != NULO)
        if alvo.any():
            df.loc[alvo, "raca_pub"] = NULO
            mudou = True
            tam = df.groupby(sub)["id"].transform("size")
        alvo = (tam < k) & (df["tercil_pub"] != NULO)
        if alvo.any():
            doms = set(df.loc[alvo & df["domicilio"].notna(), "domicilio"])
            fam = alvo | df["domicilio"].isin(doms)
            df.loc[fam, "tercil_pub"] = NULO
            mudou = True
            tam = df.groupby(sub)["id"].transform("size")
        # subgrupo totalmente suprimido pequeno: absorve subgrupos do mesmo bloco
        vazio = (df["tercil_pub"] == NULO) & (df["raca_pub"] == NULO)
        tam_vazio = df[vazio].groupby("bloco").size()
        for bloco, n in tam_vazio[tam_vazio < k].items():
            no_bloco = df[(df["bloco"] == bloco) & ~vazio]
            if no_bloco.empty:
                continue
            ordem = no_bloco.groupby(["tercil_pub", "raca_pub"]).size().sort_values()
            for (t, r), m in ordem.items():
                sel = (df["bloco"] == bloco) & (df["tercil_pub"] == t) & (df["raca_pub"] == r)
                doms = set(df.loc[sel & df["domicilio"].notna(), "domicilio"])
                df.loc[sel, "raca_pub"] = NULO
                df.loc[sel | df["domicilio"].isin(doms), "tercil_pub"] = NULO
                n += m
                mudou = True
                if n >= k:
                    break
        if not mudou:
            break

    df["raca_suprimida"] = (df["raca_pub"] == NULO) & df["raca_cor"].notna()
    df["tercil_suprimido"] = (df["tercil_pub"] == NULO) & df["tercil"].notna()
    df["desloc_dias"] = (df["dt_nasc"] - df["dt_nasc_pub"]).dt.days
    return df


CICLOS = ["0-1", "2-9", "10-19", "20-59", "60+"]


def nucleo_adaptativo(pes: pd.DataFrame, k: int, m: float = 3.0, por_ciclo: bool = True,
                      representante: str = "mediana") -> pd.DataFrame:
    """Meio-termo ajustável entre precisão da data e retenção de raça/tercil.

    1. Base: sexo x equipe (x ciclo de vida, se `por_ciclo`) — bebês só
       concorrem com bebês, então os blocos de data deles ficam estreitos.
       Base com < k pessoas é fundida ao ciclo vizinho.
    2. Raça/cor e tercil só ficam publicados num grupo (base, tercil, raça) com
       >= m*k pessoas: abaixo disso, suprime a raça; depois o tercil (do
       domicílio inteiro). m = 1 ~ "categorias primeiro"; m grande ~ "data
       primeiro".
    3. Grupo residual (base, sem tercil, sem raça) com 0 < n < k absorve
       grupos inteiros da mesma base, do menor para o maior, até chegar a k.
    4. Data microagregada dentro de cada grupo final em blocos de >= k.
    Garante k para todos, exceto uma base inteira menor que k.
    """
    df = pes[["id", "sexo", "dt_nasc", "equipe", "tercil", "raca_cor", "domicilio", "ciclo"]].copy()
    df["sexo_pub"] = _rotulo(df["sexo"])
    df["equipe_pub"] = _rotulo(df["equipe"])
    df["raca_pub"] = _rotulo(df["raca_cor"])
    df["tercil_pub"] = _rotulo(df["tercil"])
    df["base_ciclo"] = df["ciclo"].astype(str) if por_ciclo else "*"
    base = ["sexo_pub", "equipe_pub", "base_ciclo"]

    # 0. equipe com < k pessoas no sexo (ex.: INE com um cidadão vinculado):
    #    a equipe vinculada não é publicada para essas pessoas.
    tam_eq = df.groupby(["sexo_pub", "equipe_pub"])["id"].transform("size")
    df["equipe_suprimida"] = (tam_eq < k) & (df["equipe_pub"] != NULO)
    df.loc[df["equipe_suprimida"], "equipe_pub"] = NULO

    # 1. dentro de sexo x equipe, junta ciclos consecutivos até cada balde ter >= k
    if por_ciclo:
        for _, g in df.groupby(["sexo_pub", "equipe_pub"]):
            cont = g["ciclo"].astype(str).value_counts()
            baldes: list[list[str]] = []
            atual: list[str] = []
            n = 0
            for c in CICLOS:
                if c not in cont:
                    continue
                atual.append(c)
                n += cont[c]
                if n >= k:
                    baldes.append(atual)
                    atual, n = [], 0
            if atual:
                if baldes:
                    baldes[-1].extend(atual)
                else:
                    baldes.append(atual)
            for b in baldes:
                sel = g.index[g["ciclo"].astype(str).isin(b)]
                df.loc[sel, "base_ciclo"] = "|".join(b)

    grupo = base + ["tercil_pub", "raca_pub"]
    limite = m * k
    for _ in range(100):
        mudou = False
        tam = df.groupby(grupo)["id"].transform("size")
        alvo = (tam < limite) & (df["raca_pub"] != NULO)
        if alvo.any():
            df.loc[alvo, "raca_pub"] = NULO
            mudou = True
            tam = df.groupby(grupo)["id"].transform("size")
        alvo = (tam < limite) & (df["tercil_pub"] != NULO)
        if alvo.any():
            doms = set(df.loc[alvo & df["domicilio"].notna(), "domicilio"])
            df.loc[alvo | df["domicilio"].isin(doms), "tercil_pub"] = NULO
            mudou = True
        # 3. residual pequeno absorve grupos da mesma base
        vazio = (df["tercil_pub"] == NULO) & (df["raca_pub"] == NULO)
        tam_vazio = df[vazio].groupby(base).size()
        for chave, n in tam_vazio[tam_vazio < k].items():
            na_base = (df[base] == pd.Series(chave, index=base)).all(axis=1)
            outros = df[na_base & ~vazio]
            for (t, r), qtd in outros.groupby(["tercil_pub", "raca_pub"]).size().sort_values().items():
                sel = na_base & (df["tercil_pub"] == t) & (df["raca_pub"] == r)
                doms = set(df.loc[sel & df["domicilio"].notna(), "domicilio"])
                df.loc[sel, "raca_pub"] = NULO
                df.loc[sel | df["domicilio"].isin(doms), "tercil_pub"] = NULO
                n += qtd
                mudou = True
                if n >= k:
                    break
        if not mudou:
            break

    df["dt_nasc_pub"] = pd.NaT
    df["bloco"] = -1
    proximo = 0
    for _, g in df.sort_values("dt_nasc").groupby(grupo, sort=False):
        idx = g.index.to_numpy()
        for b in np.array_split(idx, max(1, len(idx) // k)):
            datas = df.loc[b, "dt_nasc"].sort_values()
            df.loc[b, "dt_nasc_pub"] = datas.iloc[0] if representante == "min" else datas.iloc[len(b) // 2]
            df.loc[b, "bloco"] = proximo
            proximo += 1

    df["raca_suprimida"] = (df["raca_pub"] == NULO) & df["raca_cor"].notna()
    df["tercil_suprimido"] = (df["tercil_pub"] == NULO) & df["tercil"].notna()
    df["desloc_dias"] = (df["dt_nasc"] - df["dt_nasc_pub"]).dt.days
    return df


def classes(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """Tamanho da classe de equivalência de cada linha sobre `cols`."""
    chave = df[cols].astype(str)
    return chave.groupby(cols, dropna=False)[cols[0]].transform("size")


# ------------------------------------------------------------ QI fora do núcleo
def raros_para_outro(serie: pd.Series, ids: pd.Series, k: int) -> pd.Series:
    """Valor com < k pessoas vira nulo ("outro")."""
    pessoas = ids.groupby(serie).nunique()
    raros = set(pessoas[pessoas < k].index)
    return serie.where(~serie.isin(raros))


# ------------------------------------------------------------ antropometria
def antropometria(valores: pd.Series, ids: pd.Series, k: int,
                  corte: tuple[float, float] = (0.001, 0.999), casas: int = 1):
    """Mapa valor original -> valor publicado, para uma variável.

    Corta abaixo/acima dos quantis `corte` (erros de digitação viram o próprio
    limite) e microagrega por valor em blocos com >= k pessoas distintas.
    Devolve (serie_publicada, mapa {valor: publicado}).
    """
    ok = valores.notna()
    v = valores[ok].round(casas)
    lo, hi = v.quantile(corte[0]), v.quantile(corte[1])
    v = v.clip(lo, hi)
    tab = pd.DataFrame({"v": v, "id": ids[ok]})
    por_valor = tab.groupby("v").agg(pessoas=("id", "nunique"), n=("id", "size")).sort_index()

    mapa: dict[float, float] = {}
    bloco_vals: list[float] = []
    bloco_ids: set = set()
    grupos: list[list[float]] = []
    ids_por_valor = tab.groupby("v")["id"].apply(set)
    for val in por_valor.index:
        bloco_vals.append(val)
        bloco_ids |= ids_por_valor[val]
        if len(bloco_ids) >= k:
            grupos.append(bloco_vals)
            bloco_vals, bloco_ids = [], set()
    if bloco_vals:  # sobra < k pessoas: junta ao bloco anterior
        if grupos:
            grupos[-1].extend(bloco_vals)
        else:
            grupos.append(bloco_vals)
    for g in grupos:
        pesos = por_valor.loc[g, "n"]
        media = round(float(np.average(g, weights=pesos)), casas)
        for val in g:
            mapa[val] = media

    original = valores.round(casas)
    publicado = original.clip(lo, hi).map(mapa)
    return publicado.where(ok), {"limites": (float(lo), float(hi)), "mapa": mapa}


# ------------------------------------------------------------ diagnósticos
_CAPITULOS_CID = [
    ("A00", "B99", "I"), ("C00", "D48", "II"), ("D50", "D89", "III"), ("E00", "E90", "IV"),
    ("F00", "F99", "V"), ("G00", "G99", "VI"), ("H00", "H59", "VII"), ("H60", "H95", "VIII"),
    ("I00", "I99", "IX"), ("J00", "J99", "X"), ("K00", "K93", "XI"), ("L00", "L99", "XII"),
    ("M00", "M99", "XIII"), ("N00", "N99", "XIV"), ("O00", "O99", "XV"), ("P00", "P96", "XVI"),
    ("Q00", "Q99", "XVII"), ("R00", "R99", "XVIII"), ("S00", "T98", "XIX"), ("V01", "Y98", "XX"),
    ("Z00", "Z99", "XXI"), ("U00", "U99", "XXII"),
]


def capitulo_cid(codigo: str) -> str:
    cat = codigo[:3]
    for ini, fim, cap in _CAPITULOS_CID:
        if ini <= cat <= fim:
            return f"CID-{cap}"
    return "CID-?"


def hierarquia(sistema: str, codigo: str) -> list[str]:
    """Do mais específico ao mais geral."""
    if sistema == "CID":
        niveis = [codigo] if len(codigo) > 3 else []
        return niveis + [codigo[:3], capitulo_cid(codigo)]
    # CIAP-2: letra = capítulo; 01-29 sintomas, 30-69 procedimentos, 70-99 diagnósticos.
    # Códigos de 6 caracteres (ex.: ABP001) são extensões do e-SUS: sobem para o prefixo.
    if len(codigo) == 6:
        return [codigo, codigo[:3], f"CIAP-{codigo[0]}"]
    try:
        num = int(codigo[1:])
        comp = "sintoma" if num < 30 else ("procedimento" if num < 70 else "diagnostico")
    except ValueError:
        comp = "?"
    return [codigo, f"CIAP-{codigo[0]}-{comp}", f"CIAP-{codigo[0]}"]


def diagnosticos(diag: pd.DataFrame, contexto: pd.DataFrame | None, k: int) -> pd.DataFrame:
    """Generaliza cada código até ter >= k pessoas.

    `contexto`: None -> k sobre a população inteira; ou DataFrame (id, ctx)
    -> k em cada contexto onde o código publicado aparece (ex.: sexo x ciclo
    de vida), modelando um atacante que sabe o diagnóstico e o contexto.
    Recodificação global, decidida por código: o mesmo código vira o mesmo
    publicado em toda a base. A cada rodada, os códigos cujo valor publicado
    tem < k pessoas sobem um nível, até o capítulo.
    """
    d = diag.reset_index(drop=True).copy()
    if contexto is not None:
        d = d.merge(contexto, on="id", how="left")
        d["ctx"] = d["ctx"].fillna(NULO)
    cod = d[["sistema", "codigo"]].drop_duplicates().reset_index(drop=True)
    cod["hier"] = [hierarquia(s, c) for s, c in zip(cod["sistema"], cod["codigo"])]
    cod["nivel"] = 0
    chave = ["sistema", "codigo"]
    for _ in range(5):
        cod["publicado"] = [h[n] for h, n in zip(cod["hier"], cod["nivel"])]
        d = d.drop(columns=["publicado", "nivel"], errors="ignore").merge(
            cod[[*chave, "publicado", "nivel"]], on=chave, how="left")
        if contexto is None:
            pessoas = d.groupby(["sistema", "publicado"])["id"].nunique()
        else:
            pessoas = d.groupby(["sistema", "publicado", "ctx"])["id"].nunique().groupby(
                level=[0, 1]).min()
        n_pub = cod.set_index(["sistema", "publicado"]).index.map(pessoas)
        subir = (np.asarray(n_pub) < k) & (cod["nivel"] < cod["hier"].str.len() - 1)
        if not subir.any():
            break
        cod.loc[subir, "nivel"] += 1
    return d.drop(columns=[c for c in ("ctx",) if c in d.columns])


# ------------------------------------------------------------ l-diversidade
SENSIVEIS_CID = {
    "HIV/aids": ("B20", "B24"), "tuberculose": ("A15", "A19"), "hanseníase": ("A30", "A30"),
    "IST": ("A50", "A64"), "transtorno mental": ("F20", "F99"), "uso de substância": ("F10", "F19"),
    "gestação/aborto": ("O00", "O99"), "violência": ("X85", "Y09"),
}
SENSIVEIS_CIAP = {"HIV/aids": ("B90",), "gestação/aborto": ("W",), "transtorno mental": ("P",)}


def sensiveis_por_pessoa(diag: pd.DataFrame) -> pd.DataFrame:
    """(id, categoria sensível) a partir dos códigos originais."""
    out = []
    cid = diag[diag["sistema"] == "CID"]
    for rot, (ini, fim) in SENSIVEIS_CID.items():
        cat = cid["codigo"].str[:3]
        out.append(cid.loc[(cat >= ini) & (cat <= fim), ["id"]].assign(sensivel=rot))
    ciap = diag[diag["sistema"] == "CIAP"]
    for rot, prefixos in SENSIVEIS_CIAP.items():
        out.append(ciap.loc[ciap["codigo"].str.startswith(prefixos), ["id"]].assign(sensivel=rot))
    return pd.concat(out, ignore_index=True).drop_duplicates()
