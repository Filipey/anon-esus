"""Testes da migration 15 (k-anonimato do núcleo de quase-identificadores)."""

from __future__ import annotations

import random
from datetime import date, timedelta

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("15_anon_k_anonimato.py")


def _seed(engine, n=80, semente=7):
    rnd = random.Random(semente)
    with engine.begin() as c:
        c.execute(text(
            "CREATE TABLE public.tb_cidadao (co_seq_cidadao serial PRIMARY KEY, no_sexo text, "
            "dt_nascimento date, co_raca_cor int, co_escolaridade int, co_estado_civil int, nu_cpf text, "
            "nu_cns text, co_localidade int, co_localidade_endereco int, co_cbo int)"))
        c.execute(text("CREATE TABLE public.tb_cidadao_vinculacao_equipe (co_cidadao int, nu_ine text)"))
        c.execute(text("CREATE TABLE public.tb_fat_vacinacao (co_seq serial PRIMARY KEY, "
                       "nu_cpf_cidadao text, dt_nascimento date)"))
        c.execute(text("CREATE TABLE public.tb_prof (co_seq serial PRIMARY KEY, nu_cpf text, dt_nascimento date)"))
        c.execute(text(
            "CREATE TABLE public.tb_cds_cad_individual (co_seq serial PRIMARY KEY, co_unico_ficha_origem text, "
            "st_versao_atual int, co_sexo int, dt_nascimento date, co_raca_cor int, co_estado_civil int, "
            "nu_cpf_cidadao text, nu_cns_cidadao text, co_municipio int, co_cbo int)"))
        for i in range(n):
            nasc = date(1940, 1, 1) + timedelta(days=rnd.randrange(0, 30000))
            c.execute(text(
                "INSERT INTO public.tb_cidadao (no_sexo, dt_nascimento, co_raca_cor, co_escolaridade, "
                "co_estado_civil, nu_cpf, nu_cns, co_localidade, co_localidade_endereco, co_cbo) VALUES "
                "(:s, :d, :r, :e, :ec, :cpf, :cns, :ln, :lr, :cbo)"),
                {"s": rnd.choice(["MASCULINO", "FEMININO"]), "d": nasc, "r": rnd.choice([1, 4, 4, 2]),
                 "e": rnd.choice([4, 5, 10, 13, None]), "ec": rnd.choice([None, None, 1, 2]),
                 "cpf": f"{i:011d}", "cns": f"7{i:014d}", "ln": rnd.choice([1, 1, 1, 2, 3 + i]),
                 "lr": 1, "cbo": rnd.choice([None, 10, 10, 500 + i])})
            c.execute(text("INSERT INTO public.tb_cidadao_vinculacao_equipe VALUES (:c, :ine)"),
                      {"c": i + 1, "ine": rnd.choice(["A", "B"])})
            c.execute(text("INSERT INTO public.tb_fat_vacinacao (nu_cpf_cidadao, dt_nascimento) VALUES (:c, :d)"),
                      {"c": f"{i:011d}", "d": nasc})
        # pessoa só do CDS: versão antiga sem CPF + versão atual com CPF
        for versao, cpf in ((0, None), (1, "99999999999")):
            c.execute(text(
                "INSERT INTO public.tb_cds_cad_individual (co_unico_ficha_origem, st_versao_atual, co_sexo, "
                "dt_nascimento, co_raca_cor, nu_cpf_cidadao) VALUES ('ficha-x', :v, 1, '1990-05-17', 5, :cpf)"),
                {"v": versao, "cpf": cpf})
        for i in range(12):
            c.execute(text("INSERT INTO public.tb_prof (nu_cpf, dt_nascimento) VALUES (:c, :d)"),
                      {"c": f"p{i}", "d": date(1970, 1, 1) + timedelta(days=97 * i)})


def _classes(engine):
    """Classes sobre todas as pessoas publicadas: tb_cidadao + pessoas só do
    CDS (versão atual do cadastro), que não têm equipe nem escolaridade."""
    with engine.connect() as c:
        return c.execute(text(
            "SELECT sexo, ine, raca, escol, civil, nasc, count(*) FROM ("
            "  SELECT c.no_sexo AS sexo, v.nu_ine AS ine, c.co_raca_cor AS raca, "
            "         c.co_escolaridade AS escol, c.co_estado_civil AS civil, c.dt_nascimento AS nasc "
            "  FROM public.tb_cidadao c "
            "  LEFT JOIN public.tb_cidadao_vinculacao_equipe v ON v.co_cidadao = c.co_seq_cidadao "
            "  UNION ALL "
            "  SELECT CASE co_sexo WHEN 0 THEN 'MASCULINO' WHEN 1 THEN 'FEMININO' END, NULL, "
            "         co_raca_cor, NULL, co_estado_civil, dt_nascimento "
            "  FROM public.tb_cds_cad_individual WHERE st_versao_atual = 1"
            ") p GROUP BY 1, 2, 3, 4, 5, 6")).all()


def test_k_garantido_sobre_os_qi_publicados(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    assert min(n for *_, n in _classes(pg_engine)) >= m.K


def test_data_propagada_pelo_cpf(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    with pg_engine.connect() as c:
        diferentes = c.execute(text(
            "SELECT count(*) FROM public.tb_fat_vacinacao f JOIN public.tb_cidadao c "
            "ON c.nu_cpf = f.nu_cpf_cidadao WHERE c.dt_nascimento <> f.dt_nascimento")).scalar()
    assert diferentes == 0


def test_pessoa_so_do_cds_entra_e_todas_as_versoes_recebem_a_mesma_data(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    with pg_engine.connect() as c:
        datas = c.execute(text("SELECT DISTINCT dt_nascimento FROM public.tb_cds_cad_individual "
                               "WHERE co_unico_ficha_origem = 'ficha-x'")).scalars().all()
    assert len(datas) == 1


def test_quem_nao_se_liga_a_ninguem_recebe_data_microagregada(pg_engine):
    _seed(pg_engine)
    with pg_engine.connect() as c:
        antes = set(c.execute(text("SELECT dt_nascimento FROM public.tb_prof")).scalars())
    m.run(pg_engine)
    with pg_engine.connect() as c:
        por_data = c.execute(text("SELECT dt_nascimento, count(*) FROM public.tb_prof GROUP BY 1")).all()
    assert all(n >= m.K for _, n in por_data)
    assert len(por_data) < len(antes)


def test_atributo_suprimido_vira_sem_informacao(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    with pg_engine.connect() as c:
        racas = set(c.execute(text("SELECT co_raca_cor FROM public.tb_cidadao")).scalars())
    assert None not in racas  # raça suprimida vira 6 (sem informação), não nulo


def test_municipio_raro_vira_nulo(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    with pg_engine.connect() as c:
        por_mun = c.execute(text("SELECT co_localidade, count(*) FROM public.tb_cidadao "
                                 "WHERE co_localidade IS NOT NULL GROUP BY 1")).all()
    assert all(n >= m.K for _, n in por_mun)


def test_aborta_sem_gravar_quando_k_nao_e_alcancavel(pg_engine, monkeypatch):
    _seed(pg_engine, n=6)
    monkeypatch.setattr(m, "K", 50)
    with pg_engine.connect() as c:
        antes = c.execute(text("SELECT dt_nascimento FROM public.tb_cidadao ORDER BY 1")).scalars().all()
    with pytest.raises(RuntimeError, match="k-anonimato não alcançado"):
        m.run(pg_engine)
    with pg_engine.connect() as c:
        depois = c.execute(text("SELECT dt_nascimento FROM public.tb_cidadao ORDER BY 1")).scalars().all()
    assert antes == depois


def test_banco_vazio_nao_falha(pg_engine):
    m.run(pg_engine)
