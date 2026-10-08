"""Algoritmos de k-anonimato da metodologia final.

Funções puras sobre DataFrames, usadas pela varredura de k
(`experimentos/k-anonimato-dp/`) e pelas migrations 08 e 15. Nenhuma toca o
banco.

Núcleo de quase-identificadores (QI): sexo, data de nascimento, equipe,
tercil de distância, raça/cor.

1. `nucleo_adaptativo`: QI = sexo, nascimento, equipe + atributos
   suprimíveis (estado civil, escolaridade em 5 níveis, raça/cor, tercil).
   Corte por ciclo de vida, supressão em ordem de prioridade nos grupos com
   < m*k pessoas (tercil é do domicílio: suprime para a família), grupo
   residual absorvendo subgrupos até k, e microagregação da data de
   nascimento em blocos de >= k dentro de cada grupo final. Equipe não é
   generalizada (aparece em cada atendimento), só suprimida quando o
   sexo x equipe inteiro tem < k pessoas. As duas primeiras versões
   (estratos primeiro; data primeiro) eram os extremos da fronteira e foram
   substituídas por esta, que tem os dois como casos limite (m = 1 sem
   ciclo; m grande).
2. `raros_para_outro`: valor de QI fora do núcleo com < k pessoas vira nulo.
3. `antropometria`: por variável, corta extremos (erros de digitação) e
   microagrega por valor — blocos consecutivos de valores com >= k pessoas
   distintas, cada valor vira a mediana do bloco. A regra depende só do valor,
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


CICLOS = ["0-1", "2-9", "10-19", "20-59", "60+"]

# Escolaridade (tb_escolaridade) em 5 níveis; o publicado é um código
# representativo de cada nível, porque o PEC exige um código válido.
NIVEL_ESCOLARIDADE = {
    15: "nenhuma", 14: "nenhuma",
    1: "infantil", 2: "infantil", 3: "infantil",
    4: "fundamental", 5: "fundamental", 6: "fundamental", 7: "fundamental", 8: "fundamental", 9: "fundamental",
    10: "medio", 11: "medio", 12: "medio",
    13: "superior",
}
CODIGO_DO_NIVEL = {"nenhuma": 15, "infantil": 1, "fundamental": 5, "medio": 10, "superior": 13}

# Atributos generalizáveis, na ordem em que são suprimidos (o de menor valor
# para a população sintética primeiro). "domicilio": suprimir afeta a família.
SUPRIMIVEIS = [
    ("estado_civil", "pessoa"),
    ("escolaridade_nivel", "pessoa"),
    ("raca_cor", "pessoa"),
    ("tercil", "domicilio"),
]


def _absorver(df: pd.DataFrame, alvo: pd.Series, doadores: pd.Series, faltam: int,
              colunas: list[str], marca: str) -> None:
    """Suprime `colunas` de `faltam` pessoas de `doadores` (as de menor id,
    para ser determinístico), juntando-as ao grupo `alvo`."""
    escolhidos = df[doadores].sort_values("id").index[:faltam]
    for col in colunas:
        df.loc[escolhidos, col] = NULO
    df.loc[escolhidos, marca] = True


def _base_sexo_equipe(df: pd.DataFrame, k: int) -> None:
    """Garante >= k pessoas em cada sexo x equipe publicado.

    - equipe com < k pessoas no sexo: a equipe vinculada não é publicada;
    - o grupo "sexo sem equipe" com 0 < n < k absorve pessoas do maior time do
      mesmo sexo (que perdem a equipe);
    - o grupo "sem sexo" com 0 < n < k absorve pessoas do maior sexo (que
      perdem o sexo e a equipe); pessoas sem sexo também não publicam equipe.
    Absorver tira informação de poucas pessoas, mas não inventa nenhuma.
    """
    tam = df.groupby(["sexo_pub", "equipe_pub"])["id"].transform("size")
    pequena = (tam < k) & (df["equipe_pub"] != NULO)
    df.loc[pequena, "equipe_suprimida"] = True
    df.loc[pequena, "equipe_pub"] = NULO

    sem_sexo = df["sexo_pub"] == NULO
    df.loc[sem_sexo & (df["equipe_pub"] != NULO), "equipe_suprimida"] = True
    df.loc[sem_sexo, "equipe_pub"] = NULO
    n = int(sem_sexo.sum())
    if 0 < n < k:
        maior = df.loc[~sem_sexo, "sexo_pub"].value_counts().idxmax()
        _absorver(df, sem_sexo, df["sexo_pub"] == maior, k - n, ["sexo_pub", "equipe_pub"], "sexo_suprimido")

    for sexo in df.loc[df["sexo_pub"] != NULO, "sexo_pub"].unique():
        do_sexo = df["sexo_pub"] == sexo
        vazio = do_sexo & (df["equipe_pub"] == NULO)
        n = int(vazio.sum())
        if 0 < n < k:
            times = df.loc[do_sexo & ~vazio, "equipe_pub"].value_counts()
            if not times.empty:
                maior = do_sexo & (df["equipe_pub"] == times.index[0])
                _absorver(df, vazio, maior, k - n, ["equipe_pub"], "equipe_suprimida")


def nucleo_adaptativo(pes: pd.DataFrame, k: int, m: float = 1.0, por_ciclo: bool = True,
                      representante: str = "mediana",
                      suprimiveis: list[tuple[str, str]] | None = None) -> pd.DataFrame:
    """Meio-termo ajustável entre precisão da data e retenção dos atributos.

    QI = sexo, data de nascimento, equipe + `suprimiveis` (padrão: estado
    civil, escolaridade em 5 níveis, raça/cor, tercil de distância).

    0. Sexo x equipe com >= k pessoas (`_base_sexo_equipe`): equipe pequena
       não é publicada; grupos "sem equipe" e "sem sexo" pequenos absorvem
       pessoas do maior grupo vizinho.
    1. Base: sexo x equipe (x ciclo de vida, se `por_ciclo`); ciclos vizinhos
       se juntam até cada base ter >= k pessoas.
    2. Grupo (base, atributos publicados) com < m*k pessoas: suprime o
       primeiro atributo ainda publicado na ordem de `suprimiveis` (tercil é do
       domicílio: suprime para a família inteira). Repete até estabilizar.
    3. Grupo residual (base, tudo suprimido) com 0 < n < k absorve grupos
       inteiros da mesma base, do menor para o maior, até chegar a k.
    4. Data microagregada dentro de cada grupo final em blocos de >= k.
    Garante k para todos sobre os QI publicados.
    """
    sup = suprimiveis if suprimiveis is not None else SUPRIMIVEIS
    df = pes.copy()
    if "escolaridade_nivel" not in df and "escolaridade" in df:
        df["escolaridade_nivel"] = df["escolaridade"].map(NIVEL_ESCOLARIDADE)
    df["sexo_pub"] = _rotulo(df["sexo"])
    df["equipe_pub"] = _rotulo(df["equipe"])
    pubs = []
    for col, _ in sup:
        df[f"{col}_pub"] = _rotulo(df[col])
        pubs.append(f"{col}_pub")

    df["equipe_suprimida"] = False
    df["sexo_suprimido"] = False
    _base_sexo_equipe(df, k)

    df["base_ciclo"] = "*"
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
                df.loc[g.index[g["ciclo"].astype(str).isin(b)], "base_ciclo"] = "|".join(b)
    base = ["sexo_pub", "equipe_pub", "base_ciclo"]
    grupo = base + pubs

    def suprimir(sel: pd.Series, col: str, nivel: str) -> None:
        pub = f"{col}_pub"
        if nivel == "domicilio":
            doms = set(df.loc[sel & df["domicilio"].notna(), "domicilio"])
            sel = sel | df["domicilio"].isin(doms)
        df.loc[sel, pub] = NULO

    limite = m * k
    for _ in range(200):
        mudou = False
        for col, nivel in sup:
            tam = df.groupby(grupo)["id"].transform("size")
            alvo = (tam < limite) & (df[f"{col}_pub"] != NULO)
            # só suprime este atributo de quem já não tem um anterior a suprimir
            for anterior, _n in sup[: [c for c, _ in sup].index(col)]:
                alvo &= df[f"{anterior}_pub"] == NULO
            if alvo.any():
                suprimir(alvo, col, nivel)
                mudou = True
        vazio = (df[pubs] == NULO).all(axis=1)
        tam_vazio = df[vazio].groupby(base).size()
        for chave, n in tam_vazio[tam_vazio < k].items():
            na_base = (df[base] == pd.Series(chave, index=base)).all(axis=1)
            outros = df[na_base & ~vazio]
            for vals, qtd in outros.groupby(pubs).size().sort_values().items():
                vals = vals if isinstance(vals, tuple) else (vals,)
                sel = na_base & (df[pubs] == pd.Series(vals, index=pubs)).all(axis=1)
                for col, nivel in sup:
                    suprimir(sel, col, nivel)
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

    for col, _ in sup:
        df[f"{col}_suprimido"] = (df[f"{col}_pub"] == NULO) & df[col].notna()
    df["raca_suprimida"] = df.get("raca_cor_suprimido", False)
    df["tercil_suprimido"] = df.get("tercil_suprimido", False)
    df["desloc_dias"] = (df["dt_nasc"] - df["dt_nasc_pub"]).dt.days
    df["raca_pub"] = df.get("raca_cor_pub", NULO)
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
def faixas_antropometria(valores: pd.Series, ids: pd.Series, k: int,
                         corte: tuple[float, float] = (0.001, 0.999),
                         casas: int = 1) -> list[tuple[float, float, float]]:
    """Faixas (início, fim, publicado) que cobrem a reta inteira, para uma variável.

    Corta abaixo/acima dos quantis `corte` (erros de digitação ficam na faixa
    da ponta) e agrupa os valores ordenados em blocos com >= k pessoas
    distintas; cada bloco vira uma faixa [início, início do próximo) cujo
    publicado é a mediana dos valores do bloco. A primeira faixa começa em -inf
    e a última termina em +inf, então qualquer valor — inclusive um que só
    aparece no DW — cai em alguma faixa.
    """
    ok = valores.notna()
    v = valores[ok].round(casas)
    lo, hi = v.quantile(corte[0]), v.quantile(corte[1])
    tab = pd.DataFrame({"v": v.clip(lo, hi), "id": ids[ok]})
    por_valor = tab.groupby("v").agg(n=("id", "size")).sort_index()
    ids_por_valor = tab.groupby("v")["id"].apply(set)

    grupos: list[list[float]] = []
    bloco_vals: list[float] = []
    bloco_ids: set = set()
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

    faixas = []
    for i, g in enumerate(grupos):
        inicio = -np.inf if i == 0 else g[0]
        fim = grupos[i + 1][0] if i + 1 < len(grupos) else np.inf
        # mediana ponderada: um erro de digitação que escape do corte não
        # puxa o publicado do bloco (a média puxaria)
        acum = por_valor.loc[g, "n"].cumsum()
        mediana = float(acum.index[np.searchsorted(acum.to_numpy(), acum.iloc[-1] / 2)])
        faixas.append((float(inicio), float(fim), round(mediana, casas)))
    return faixas


def aplicar_faixas(valores: pd.Series, faixas: list[tuple[float, float, float]]) -> pd.Series:
    inicios = np.array([f[0] for f in faixas])
    publicados = np.array([f[2] for f in faixas])
    pos = np.searchsorted(inicios, valores.to_numpy(dtype=float), side="right") - 1
    out = pd.Series(publicados[np.clip(pos, 0, len(faixas) - 1)], index=valores.index)
    return out.where(valores.notna())


def antropometria(valores: pd.Series, ids: pd.Series, k: int,
                  corte: tuple[float, float] = (0.001, 0.999), casas: int = 1):
    """Série publicada e as faixas, para uma variável (usa `faixas_antropometria`)."""
    faixas = faixas_antropometria(valores, ids, k, corte, casas)
    return aplicar_faixas(valores.round(casas), faixas), {"faixas": faixas,
                                                          "mapa": {f[0]: f[2] for f in faixas}}


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
    for _ in range(20):
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
        # Um nível por vez, do mais específico para o mais geral: primeiro as
        # subcategorias raras sobem para a categoria; só na rodada seguinte a
        # categoria é avaliada, já com elas somadas. Subir tudo junto mandava
        # para o capítulo um código de categoria raro (ex.: "S02" usado por 1
        # pessoa) na mesma rodada em que as subcategorias S02x chegavam a ele,
        # e a categoria acabava suprimida mesmo com 76 pessoas.
        especificidade = cod["hier"].str.len() - 1 - cod["nivel"]
        subir &= (especificidade == especificidade[subir].max()).to_numpy()
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
