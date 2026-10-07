"""Migration 15 - k-anonimato do núcleo de quase-identificadores.

Depois das migrations 01-14, a base ainda permitia reidentificar quase todo
mundo pelo que um vizinho ou agente sabe: com sexo + mês/ano de nascimento +
equipe + raça/cor, 81% das pessoas eram únicas
(`experimentos/k-anonimato-dp/00_quase_identificadores.py`). Esta migration
aplica o k-anonimato decidido em 07/10/2026 (`experimentos/k-anonimato-dp/`,
`README.md`):

- **QI do atacante**: sexo, data de nascimento, equipe, tercil de distância,
  raça/cor, escolaridade (5 níveis) e estado civil;
- **k = 5**, núcleo adaptativo com corte por ciclo de vida, m = 1
  (`k_anonimato.nucleo_adaptativo`): estado civil, escolaridade, raça/cor e
  tercil são suprimidos, nessa ordem, em grupo com < k pessoas; a data de
  nascimento é microagregada em blocos de >= k pessoas (mediana do bloco);
  equipe vinculada só é suprimida quando o sexo x equipe tem < k pessoas;
- **fora do k**: município de nascimento, município de residência e ocupação
  — valor com < k pessoas vira nulo.

População: todo `tb_cidadao` (inclusive inativos e falecidos, que também
estão na base) mais as pessoas que só existem no cadastro individual CDS
(versão atual sem cidadão correspondente por CPF/CNS). O tercil vem de
`tb_cds_domicilio.ds_ponto_referencia`, onde a migration 06 o gravou.

Propagação para todas as cópias: `ta_/tb_/tl_cidadao` pelo código do
cidadão; cadastro individual CDS pela cadeia de versões
(`co_unico_ficha_origem`), CPF ou CNS; DW e demais tabelas com data de
nascimento (lista da migration 04) pelo CPF. Linha com data de nascimento que
não se liga a ninguém recebe uma data microagregada (blocos de k) dentro da
própria tabela — nenhuma data original sobra. Atributo suprimido vira nulo
no operacional e o código "não informado" no DW.

Proteção: depois de calcular, a migration confere o k sobre os QI
publicados e **aborta** se alguma classe ficar abaixo de K.

Atômica: tudo numa transação.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

import k_anonimato as ka

log = get_logger("15_anon_k_anonimato")

K = 5
M = 1.0
POR_CICLO = True
# Data fixa para calcular o ciclo de vida: com a data do dia, rodar de novo
# em outro dia mudaria o resultado.
REFERENCIA = date(2026, 10, 7)

SEXO_CDS = {0: "MASCULINO", 1: "FEMININO"}
RACA_SEM_INFORMACAO = 6
DW_NAO_INFORMADO = {"sexo": 4, "raca": 6, "escolaridade": 16, "estado_civil": 99, "cbo": 1, "municipio": 1}
RE_TERCIL = re.compile(r"tercil (\d)")


def _m04():
    path = Path(__file__).resolve().parent / "04_anon_datas_cidadao.py"
    spec = importlib.util.spec_from_file_location("_m04_para_15", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_m04_para_15"] = mod
    spec.loader.exec_module(mod)
    return mod


def _colunas(conn: Connection, tabela: str) -> set[str]:
    return set(conn.execute(
        text("SELECT column_name FROM information_schema.columns "
             "WHERE table_schema = 'public' AND table_name = :t"), {"t": tabela}
    ).scalars())


def _df(conn: Connection, sql: str, colunas: list[str]) -> pd.DataFrame:
    return pd.DataFrame(conn.execute(text(sql)).all(), columns=colunas)


# ------------------------------------------------------------ população
def carregar_populacao(conn: Connection) -> pd.DataFrame:
    pec = _df(
        conn,
        """
        SELECT co_seq_cidadao, no_sexo, dt_nascimento, co_raca_cor, co_escolaridade,
               co_estado_civil, nu_cpf, nu_cns, co_localidade, co_localidade_endereco, co_cbo
        FROM public.tb_cidadao
        """,
        ["co_cidadao", "sexo", "dt_nasc", "raca_cor", "escolaridade", "estado_civil",
         "cpf", "cns", "mun_nasc", "mun_resid", "ocupacao"],
    )
    pec["id"] = "c:" + pec["co_cidadao"].astype(str)
    pec["ficha_origem"] = None

    if {"co_cidadao", "nu_ine"} <= _colunas(conn, "tb_cidadao_vinculacao_equipe"):
        eq = _df(conn, "SELECT co_cidadao, max(nu_ine) FROM public.tb_cidadao_vinculacao_equipe GROUP BY 1",
                 ["co_cidadao", "equipe"])
        pec = pec.merge(eq, on="co_cidadao", how="left")
    else:
        pec["equipe"] = None

    pec = pec.merge(_domicilios(conn), on="co_cidadao", how="left")

    cds = pd.DataFrame()
    if {"co_unico_ficha_origem", "st_versao_atual"} <= _colunas(conn, "tb_cds_cad_individual"):
        cds = _df(
            conn,
            """
            SELECT ci.co_unico_ficha_origem, ci.co_sexo, ci.dt_nascimento, ci.co_raca_cor,
                   ci.co_estado_civil, ci.nu_cpf_cidadao, ci.nu_cns_cidadao, ci.co_municipio, ci.co_cbo
            FROM public.tb_cds_cad_individual ci
            WHERE ci.st_versao_atual = 1
              AND NOT EXISTS (SELECT 1 FROM public.tb_cidadao c
                              WHERE (ci.nu_cpf_cidadao IS NOT NULL AND c.nu_cpf = ci.nu_cpf_cidadao)
                                 OR (ci.nu_cns_cidadao IS NOT NULL AND c.nu_cns = ci.nu_cns_cidadao))
            """,
            ["ficha_origem", "sexo", "dt_nasc", "raca_cor", "estado_civil", "cpf", "cns",
             "mun_nasc", "ocupacao"],
        )
        cds = cds.drop_duplicates("ficha_origem")
        cds["sexo"] = cds["sexo"].map(SEXO_CDS)
        cds["id"] = "f:" + cds["ficha_origem"].astype(str)
        for col in ("co_cidadao", "escolaridade", "mun_resid", "equipe", "domicilio", "tercil"):
            cds[col] = None

    pop = pd.concat([pec, cds], ignore_index=True)
    pop = pop[pop["dt_nasc"].notna()].copy()
    pop["dt_nasc"] = pd.to_datetime(pop["dt_nasc"])
    idade = (pd.Timestamp(REFERENCIA) - pop["dt_nasc"]).dt.days // 365.25
    pop["ciclo"] = pd.cut(idade, bins=[-10**4, 1, 9, 19, 59, 10**4], labels=ka.CICLOS).astype(str)
    for col in ("raca_cor", "escolaridade", "estado_civil", "equipe", "tercil", "domicilio"):
        pop[col] = pop[col].astype(object).where(pop[col].notna(), None)
    return pop.reset_index(drop=True)


def _domicilios(conn: Connection) -> pd.DataFrame:
    tabelas = ("tb_fat_cidadao_pec", "tb_fat_cidadao_territorio", "tb_fat_familia_territorio",
               "tb_fat_cad_domiciliar", "tb_cds_cad_domiciliar", "tb_cds_domicilio")
    if not all(_colunas(conn, t) for t in tabelas):
        return pd.DataFrame(columns=["co_cidadao", "domicilio", "tercil"])
    dom = _df(
        conn,
        """
        SELECT DISTINCT ON (p.co_cidadao) p.co_cidadao, d.co_seq_cds_domicilio, d.ds_ponto_referencia
        FROM public.tb_fat_cidadao_pec p
        JOIN public.tb_fat_cidadao_territorio ct ON ct.co_fat_cidadao_pec = p.co_seq_fat_cidadao_pec
        JOIN public.tb_fat_familia_territorio ft
          ON ft.co_seq_fat_familia_territorio = ct.co_fat_familia_territorio
        JOIN public.tb_fat_cad_domiciliar fd ON fd.co_seq_fat_cad_domiciliar = ft.co_fat_cad_domiciliar
        JOIN public.tb_cds_cad_domiciliar cd ON cd.co_unico_ficha::text = fd.nu_uuid_ficha::text
        JOIN public.tb_cds_domicilio d ON d.co_unico_domicilio = cd.co_unico_domicilio
        ORDER BY p.co_cidadao, ft.co_seq_fat_familia_territorio DESC
        """,
        ["co_cidadao", "domicilio", "ref"],
    )
    dom["tercil"] = dom["ref"].map(
        lambda r: int(m.group(1)) if isinstance(r, str) and (m := RE_TERCIL.search(r)) else None)
    return dom[["co_cidadao", "domicilio", "tercil"]]


# ------------------------------------------------------------ cálculo
def calcular(pop: pd.DataFrame) -> pd.DataFrame:
    r = ka.nucleo_adaptativo(pop, K, M, POR_CICLO)
    for col in ("mun_nasc", "mun_resid", "ocupacao"):
        novo = ka.raros_para_outro(r[col], r["id"], K)
        r[f"{col}_rara"] = r[col].notna() & novo.isna()
    publicados = ["sexo_pub", "equipe_pub", *[f"{c}_pub" for c, _ in ka.SUPRIMIVEIS], "dt_nasc_pub"]
    tam = ka.classes(r, publicados)
    if len(r) and tam.min() < K:
        raise RuntimeError(
            f"k-anonimato não alcançado: {int((tam < K).sum())} pessoa(s) em classe < {K}. "
            "Nada foi gravado."
        )
    return r


# ------------------------------------------------------------ gravação
def _publicacao(r: pd.DataFrame) -> pd.DataFrame:
    def pub(col):
        return r[f"{col}_pub"].where(r[f"{col}_pub"] != ka.NULO)

    return pd.DataFrame({
        "id": r["id"],
        "dt_nasc": r["dt_nasc_pub"].dt.date,
        "raca": pd.to_numeric(pub("raca_cor"), errors="coerce"),
        "escolaridade": pub("escolaridade_nivel").map(ka.CODIGO_DO_NIVEL),
        "estado_civil": pd.to_numeric(pub("estado_civil"), errors="coerce"),
        "equipe_suprimida": r["equipe_suprimida"],
        "sexo_suprimido": r["sexo_suprimido"],
        "mun_nasc_rara": r["mun_nasc_rara"],
        "mun_resid_rara": r["mun_resid_rara"],
        "ocupacao_rara": r["ocupacao_rara"],
    })


def _carregar_temp(conn: Connection, pop: pd.DataFrame, pub: pd.DataFrame) -> None:
    conn.execute(text(
        "CREATE TEMP TABLE _pub (id text PRIMARY KEY, dt_nasc date, raca int, escolaridade int, "
        "estado_civil int, equipe_suprimida bool, sexo_suprimido bool, mun_nasc_rara bool, "
        "mun_resid_rara bool, ocupacao_rara bool) ON COMMIT DROP"
    ))
    linhas = pub.astype(object).where(pub.notna(), None).to_dict(orient="records")
    conn.execute(text(
        "INSERT INTO _pub VALUES (:id, :dt_nasc, :raca, :escolaridade, :estado_civil, "
        ":equipe_suprimida, :sexo_suprimido, :mun_nasc_rara, :mun_resid_rara, :ocupacao_rara)"), linhas)

    # chaves de ligação -> pessoa (CPF e CNS podem repetir entre populações: o PEC vence)
    conn.execute(text("CREATE TEMP TABLE _chave (tipo text, valor text, id text) ON COMMIT DROP"))
    chaves = []
    for tipo, col in (("cidadao", "co_cidadao"), ("ficha", "ficha_origem"), ("cpf", "cpf"), ("cns", "cns")):
        sub = pop[pop[col].notna()][[col, "id"]].drop_duplicates(col)
        chaves += [{"tipo": tipo, "valor": str(v), "id": i} for v, i in zip(sub[col], sub["id"])]
    if chaves:
        conn.execute(text("INSERT INTO _chave VALUES (:tipo, :valor, :id)"), chaves)
    conn.execute(text("CREATE INDEX ON _chave (tipo, valor)"))


def _fallback_nascimento(conn: Connection, tabela: str, coluna: str, condicao_sem_pessoa: str) -> int:
    """Microagrega em blocos de K, dentro da tabela, as datas de nascimento das
    linhas que não se ligam a ninguém da população."""
    linhas = conn.execute(text(
        f'SELECT ctid::text, "{coluna}"::date FROM public."{tabela}" t '
        f'WHERE t."{coluna}" IS NOT NULL AND {condicao_sem_pessoa} ORDER BY 2'
    )).all()
    if not linhas:
        return 0
    ctids = [c for c, _ in linhas]
    datas = [d for _, d in linhas]
    novas: list[date] = []
    for bloco in np.array_split(np.arange(len(datas)), max(1, len(datas) // K)):
        rep = datas[bloco[len(bloco) // 2]]
        novas += [rep] * len(bloco)
    conn.execute(text("CREATE TEMP TABLE _fb (ctid_txt text, dt date) ON COMMIT DROP"))
    conn.execute(text("INSERT INTO _fb VALUES (:c, :d)"),
                 [{"c": c, "d": d} for c, d in zip(ctids, novas)])
    n = conn.execute(text(
        f'UPDATE public."{tabela}" t SET "{coluna}" = f.dt FROM _fb f WHERE t.ctid = f.ctid_txt::tid'
    )).rowcount
    conn.execute(text("DROP TABLE _fb"))
    return n


def _nascimento_por_chave(conn: Connection, tabela: str, coluna: str, chaves: list[tuple[str, str]]) -> int:
    """Data publicada para as linhas ligadas a uma pessoa por alguma chave;
    as demais (com data) vão para o fallback. O fallback roda antes, enquanto
    o ctid das linhas sem pessoa ainda é estável."""
    cols = _colunas(conn, tabela)
    chaves = [(tipo, col) for tipo, col in chaves if col in cols]
    if coluna not in cols:
        return 0
    if chaves:
        casa = " OR ".join(
            f"EXISTS (SELECT 1 FROM _chave k WHERE k.tipo = '{tipo}' AND k.valor = t.\"{col}\"::text)"
            for tipo, col in chaves)
        sem_pessoa = f"NOT ({casa})"
    else:
        sem_pessoa = "TRUE"
    total = _fallback_nascimento(conn, tabela, coluna, sem_pessoa)
    for tipo, col in chaves:
        total += conn.execute(text(
            f'UPDATE public."{tabela}" t SET "{coluna}" = p.dt_nasc '
            f"FROM _chave k JOIN _pub p ON p.id = k.id "
            f"WHERE k.tipo = :tipo AND k.valor = t.\"{col}\"::text AND t.\"{coluna}\" IS NOT NULL"
        ), {"tipo": tipo}).rowcount
    return total


ATRIBUTOS_CIDADAO = {
    # coluna -> expressão com o publicado (p.*) e o valor atual (t.*)
    "no_sexo": 'CASE WHEN p.sexo_suprimido THEN NULL ELSE t."no_sexo" END',
    "co_raca_cor": f"coalesce(p.raca, {RACA_SEM_INFORMACAO})",
    "co_escolaridade": "p.escolaridade",
    "co_estado_civil": "p.estado_civil",
    "co_localidade": 'CASE WHEN p.mun_nasc_rara THEN NULL ELSE t."co_localidade" END',
    "co_localidade_endereco": 'CASE WHEN p.mun_resid_rara THEN NULL ELSE t."co_localidade_endereco" END',
    "co_cbo": 'CASE WHEN p.ocupacao_rara THEN NULL ELSE t."co_cbo" END',
}
ATRIBUTOS_CDS = {
    "co_sexo": 'CASE WHEN p.sexo_suprimido THEN NULL ELSE t."co_sexo" END',
    "co_raca_cor": f"coalesce(p.raca, {RACA_SEM_INFORMACAO})",
    "co_estado_civil": "p.estado_civil",
    "co_municipio": 'CASE WHEN p.mun_nasc_rara THEN NULL ELSE t."co_municipio" END',
    "co_cbo": 'CASE WHEN p.ocupacao_rara THEN NULL ELSE t."co_cbo" END',
}
ATRIBUTOS_DW = {
    "co_dim_sexo": f"CASE WHEN p.sexo_suprimido THEN {DW_NAO_INFORMADO['sexo']} ELSE t.\"co_dim_sexo\" END",
    "co_dim_raca_cor": f"coalesce(p.raca, {DW_NAO_INFORMADO['raca']})",
    "co_dim_tipo_escolaridade": f"coalesce(p.escolaridade, {DW_NAO_INFORMADO['escolaridade']})",
    "co_dim_estado_civil": f"coalesce(p.estado_civil, {DW_NAO_INFORMADO['estado_civil']})",
    "co_dim_municipio_cidadao": f"CASE WHEN p.mun_nasc_rara THEN {DW_NAO_INFORMADO['municipio']} "
                                'ELSE t."co_dim_municipio_cidadao" END',
    "co_dim_cbo_cidadao": f"CASE WHEN p.ocupacao_rara THEN {DW_NAO_INFORMADO['cbo']} "
                          'ELSE t."co_dim_cbo_cidadao" END',
}


def _atributos(conn: Connection, tabela: str, mapa: dict[str, str], tipo: str, col_chave: str) -> int:
    cols = _colunas(conn, tabela)
    sets = [f'"{c}" = {expr}' for c, expr in mapa.items() if c in cols]
    if not sets or col_chave not in cols:
        return 0
    return conn.execute(text(
        f'UPDATE public."{tabela}" t SET {", ".join(sets)} '
        f"FROM _chave k JOIN _pub p ON p.id = k.id "
        f"WHERE k.tipo = :tipo AND k.valor = t.\"{col_chave}\"::text"
    ), {"tipo": tipo}).rowcount


def gravar(conn: Connection, pop: pd.DataFrame, r: pd.DataFrame) -> dict[str, int]:
    _carregar_temp(conn, pop, _publicacao(r))
    n: dict[str, int] = {}

    # 1. datas de nascimento
    for t in ("tb_cidadao", "ta_cidadao", "tl_cidadao"):
        n[f"{t}.dt_nascimento"] = _nascimento_por_chave(
            conn, t, "dt_nascimento", [("cidadao", "co_seq_cidadao"), ("cpf", "nu_cpf"), ("cns", "nu_cns")])
    for t in ("tb_cds_cad_individual", "tl_cds_cad_individual"):
        n[f"{t}.dt_nascimento"] = _nascimento_por_chave(
            conn, t, "dt_nascimento",
            [("ficha", "co_unico_ficha_origem"), ("cpf", "nu_cpf_cidadao"), ("cns", "nu_cns_cidadao")])
    feitas = {(t, "dt_nascimento") for t in ("tb_cidadao", "ta_cidadao", "tl_cidadao",
                                              "tb_cds_cad_individual", "tl_cds_cad_individual")}
    for alvo in _m04().DATE_TABLES:
        if (alvo.table, alvo.birth_column) in feitas:
            continue
        chaves = [("cpf", alvo.cpf_column)]
        if alvo.birth_column == "dt_nascimento":
            cols = _colunas(conn, alvo.table)
            chaves += [("cns", c) for c in ("nu_cns_cidadao", "nu_cns") if c in cols][:1]
        n[f"{alvo.table}.{alvo.birth_column}"] = _nascimento_por_chave(
            conn, alvo.table, alvo.birth_column, chaves)
        feitas.add((alvo.table, alvo.birth_column))

    # 2. atributos do núcleo e QI raros
    for t in ("tb_cidadao", "ta_cidadao", "tl_cidadao"):
        n[f"{t}.atributos"] = _atributos(conn, t, ATRIBUTOS_CIDADAO, "cidadao", "co_seq_cidadao")
    for t in ("tb_cds_cad_individual", "tl_cds_cad_individual"):
        n[f"{t}.atributos"] = sum(
            _atributos(conn, t, ATRIBUTOS_CDS, tipo, col)
            for tipo, col in (("ficha", "co_unico_ficha_origem"), ("cpf", "nu_cpf_cidadao"),
                              ("cns", "nu_cns_cidadao")))
    n["tb_fat_cad_individual.atributos"] = sum(
        _atributos(conn, "tb_fat_cad_individual", ATRIBUTOS_DW, tipo, col)
        for tipo, col in (("cpf", "nu_cpf_cidadao"), ("cns", "nu_cns")))
    if "no_raca_cor" in _colunas(conn, "tb_acomp_cidadaos_vinculados"):
        n["tb_acomp_cidadaos_vinculados.no_raca_cor"] = conn.execute(text(
            "UPDATE public.tb_acomp_cidadaos_vinculados t SET no_raca_cor = NULL "
            "FROM _chave k JOIN _pub p ON p.id = k.id "
            "WHERE k.tipo = 'cidadao' AND k.valor = t.co_cidadao::text AND p.raca IS NULL"
        )).rowcount

    # 3. tercil suprimido: o domicílio inteiro perde a faixa
    doms = sorted({int(d) for d in r.loc[r["tercil_suprimido"] & r["domicilio"].notna(), "domicilio"]})
    if doms and "ds_ponto_referencia" in _colunas(conn, "tb_cds_domicilio"):
        n["tb_cds_domicilio.tercil"] = conn.execute(text(
            "UPDATE public.tb_cds_domicilio SET ds_ponto_referencia = NULL "
            "WHERE co_seq_cds_domicilio = ANY(:d)"), {"d": doms}).rowcount

    # 4. equipe vinculada suprimida
    eq = sorted({int(c) for c in r.loc[r["equipe_suprimida"] & r["co_cidadao"].notna(), "co_cidadao"]})
    # (pessoas só do CDS não têm vínculo em tb_cidadao_vinculacao_equipe)
    if eq and "nu_ine" in _colunas(conn, "tb_cidadao_vinculacao_equipe"):
        n["tb_cidadao_vinculacao_equipe.nu_ine"] = conn.execute(text(
            "UPDATE public.tb_cidadao_vinculacao_equipe SET nu_ine = NULL "
            "WHERE co_cidadao = ANY(:c)"), {"c": eq}).rowcount
    return n


def run(engine: Engine) -> None:
    """Executa a migration de forma atômica."""
    log.info("iniciando k-anonimato do núcleo (k=%d, m=%s, ciclo=%s)...", K, M, POR_CICLO)
    with engine.begin() as conn:
        if "dt_nascimento" not in _colunas(conn, "tb_cidadao"):
            log.info("tb_cidadao ausente — nada a fazer.")
            return
        pop = carregar_populacao(conn)
        if pop.empty:
            log.info("nenhum cidadão com data de nascimento — nada a fazer.")
            return
        r = calcular(pop)
        tem = lambda c: max(1, int(r[c].notna().sum()))  # noqa: E731
        log.info(
            "população %d; suprimido: estado civil %.1f%%, escolaridade %.1f%%, raça/cor %.1f%%, "
            "tercil %.1f%%, equipe %d pessoa(s); deslocamento mediano do nascimento %d dia(s)",
            len(r),
            100 * r["estado_civil_suprimido"].sum() / tem("estado_civil"),
            100 * r["escolaridade_nivel_suprimido"].sum() / tem("escolaridade_nivel"),
            100 * r["raca_cor_suprimido"].sum() / tem("raca_cor"),
            100 * r["tercil_suprimido"].sum() / tem("tercil"),
            int(r["equipe_suprimida"].sum()),
            int(r["desloc_dias"].abs().median()),
        )
        for chave, qtd in gravar(conn, pop, r).items():
            log.info("%s: %d linha(s)", chave, qtd)
        log.info("concluído.")
