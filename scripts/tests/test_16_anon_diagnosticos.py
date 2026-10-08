"""Testes da migration 16 (generalização de diagnósticos raros)."""

from __future__ import annotations

from _helpers import load_migration
from sqlalchemy import text

m = load_migration("16_anon_diagnosticos.py")

CID = {"A00": 10, "A000": 11, "A001": 12, "B20": 20, "J45": 30}
CIAP = {"T90": 1, "K86": 2}
# pessoa -> (cid, ciap); K = 5
CASOS = (
    [(p, "J45", "T90") for p in range(1, 7)]       # 6 pessoas: mantém
    + [(p, "A000", None) for p in range(7, 9)]     # 2 pessoas
    + [(p, "A001", None) for p in range(9, 12)]    # 3 pessoas: A00 junta 5 -> categoria
    + [(12, "B20", "K86"), (13, None, "K86")]      # raros: suprimidos
)


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE TABLE public.tb_cid10 (co_cid10 bigint PRIMARY KEY, nu_cid10 text, no_cid10 text)"))
        c.execute(text("CREATE TABLE public.tb_ciap (co_seq_ciap bigint PRIMARY KEY, co_ciap text)"))
        c.execute(text("CREATE TABLE public.tb_problema (co_seq serial PRIMARY KEY, co_cid10 bigint, co_ciap bigint)"))
        c.execute(text("CREATE TABLE public.ta_problema (co_seq serial PRIMARY KEY, co_cid10 bigint, co_ciap bigint)"))
        c.execute(text("CREATE TABLE public.tb_dim_cid (co_seq_dim_cid bigint PRIMARY KEY, nu_cid text, "
                       "no_cid text, st_ativo int, st_registro_valido int)"))
        c.execute(text("CREATE TABLE public.tb_dim_ciap (co_seq_dim_ciap bigint PRIMARY KEY, nu_ciap text)"))
        c.execute(text("CREATE TABLE public.tb_fat_cidadao_pec (co_seq_fat_cidadao_pec bigint PRIMARY KEY, co_cidadao bigint)"))
        c.execute(text("CREATE TABLE public.tb_fat_atd_ind_problemas (co_seq serial PRIMARY KEY, "
                       "co_fat_cidadao_pec bigint, co_dim_cid bigint, co_dim_ciap bigint)"))
        for cod, i in CID.items():
            c.execute(text("INSERT INTO public.tb_cid10 VALUES (:i, :c, :n)"), {"i": i, "c": cod, "n": f"nome {cod}"})
        for cod, i in CIAP.items():
            c.execute(text("INSERT INTO public.tb_ciap VALUES (:i, :c)"), {"i": i, "c": cod})
        c.execute(text("INSERT INTO public.tb_dim_cid VALUES (1, '-', '-', 1, 1)"))
        c.execute(text("INSERT INTO public.tb_dim_ciap VALUES (1, '-')"))
        dim_cid = {cod: 100 + i for i, cod in enumerate(["A000", "A001", "B20", "J45"])}
        dim_ciap = {"T90": 200, "K86": 201}
        for cod, i in dim_cid.items():
            c.execute(text("INSERT INTO public.tb_dim_cid VALUES (:i, :c, :c, 1, 1)"), {"i": i, "c": cod})
        for cod, i in dim_ciap.items():
            c.execute(text("INSERT INTO public.tb_dim_ciap VALUES (:i, :c)"), {"i": i, "c": cod})
        for pessoa, cid, ciap in CASOS:
            c.execute(text("INSERT INTO public.tb_fat_cidadao_pec VALUES (:p, :p) ON CONFLICT DO NOTHING"), {"p": pessoa})
            c.execute(text("INSERT INTO public.tb_fat_atd_ind_problemas (co_fat_cidadao_pec, co_dim_cid, co_dim_ciap) "
                           "VALUES (:p, :cid, :ciap)"),
                      {"p": pessoa, "cid": dim_cid.get(cid, 1), "ciap": dim_ciap.get(ciap, 1)})
            for tabela in ("tb_problema", "ta_problema"):
                c.execute(text(f"INSERT INTO public.{tabela} (co_cid10, co_ciap) VALUES (:cid, :ciap)"),
                          {"cid": CID.get(cid), "ciap": CIAP.get(ciap)})


def _op(engine, tabela="tb_problema"):
    with engine.connect() as c:
        return c.execute(text(
            f"SELECT c.nu_cid10, ci.co_ciap FROM public.{tabela} p "
            "LEFT JOIN public.tb_cid10 c ON c.co_cid10 = p.co_cid10 "
            "LEFT JOIN public.tb_ciap ci ON ci.co_seq_ciap = p.co_ciap ORDER BY p.co_seq")).all()


def _dw(engine):
    with engine.connect() as c:
        return c.execute(text(
            "SELECT d.nu_cid, a.nu_ciap FROM public.tb_fat_atd_ind_problemas f "
            "JOIN public.tb_dim_cid d ON d.co_seq_dim_cid = f.co_dim_cid "
            "JOIN public.tb_dim_ciap a ON a.co_seq_dim_ciap = f.co_dim_ciap ORDER BY f.co_seq")).all()


def test_operacional_mantem_generaliza_e_suprime(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    for tabela in ("tb_problema", "ta_problema"):
        linhas = _op(pg_engine, tabela)
        assert linhas[:6] == [("J45", "T90")] * 6
        assert {cid for cid, _ in linhas[6:11]} == {"A00"}
        assert linhas[11:] == [(None, None), (None, None)]


def test_dw_usa_a_categoria_criada_e_nao_informado(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    linhas = _dw(pg_engine)
    assert linhas[:6] == [("J45", "T90")] * 6
    assert {cid for cid, _ in linhas[6:11]} == {"A00"}
    assert linhas[11:] == [("-", "-"), ("-", "-")]
    with pg_engine.connect() as c:
        nome = c.execute(text("SELECT no_cid FROM public.tb_dim_cid WHERE nu_cid = 'A00'")).scalar()
    assert nome == "nome A00"


def test_todo_codigo_publicado_tem_k_pessoas(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    with pg_engine.connect() as c:
        por_codigo = c.execute(text(
            "SELECT d.nu_cid, count(DISTINCT f.co_fat_cidadao_pec) FROM public.tb_fat_atd_ind_problemas f "
            "JOIN public.tb_dim_cid d ON d.co_seq_dim_cid = f.co_dim_cid WHERE d.nu_cid <> '-' GROUP BY 1")).all()
    assert all(n >= m.K for _, n in por_codigo)


def test_banco_vazio_nao_falha(pg_engine):
    m.run(pg_engine)


def test_categoria_rara_como_codigo_mas_comum_com_as_subcategorias_e_mantida():
    """O código de categoria usado por poucas pessoas não pode ser suprimido
    quando as subcategorias raras, ao subir, completam k na categoria."""
    import pandas as pd

    pessoas = pd.DataFrame(
        [(1, "CID", "S02")] + [(p, "CID", "S020") for p in range(2, 5)]
        + [(p, "CID", "S021") for p in range(5, 8)],
        columns=["id", "sistema", "codigo"],
    )
    destino = m.decidir(pessoas, pd.DataFrame(columns=["sistema", "codigo", "linhas"]))
    assert destino[("CID", "S02")] == "S02"
    assert destino[("CID", "S020")] == "S02"
    assert destino[("CID", "S021")] == "S02"
