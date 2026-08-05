"""Testes da migration 04 (datas de nascimento e registros)."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("04_anon_datas_cidadao.py")

CPF_A = "52998224725"
CPF_B = "11144477735"


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_atendimento_individual "
                "("
                "co_seq serial PRIMARY KEY, "
                "nu_cpf_cidadao text, "
                "dt_nascimento date, "
                "dt_inicial_atendimento timestamp, "
                "dt_final_atendimento timestamp, "
                "dt_visita date, "
                "dt_atualizacao_sistema timestamp"
                ")"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_atendimento_individual "
                "(nu_cpf_cidadao, dt_nascimento, dt_inicial_atendimento, dt_final_atendimento, "
                "dt_visita, dt_atualizacao_sistema) "
                "VALUES "
                "(:cpf_a, '1980-05-10', '2020-01-20 08:30:00', '2020-01-20 09:00:00', "
                "'2020-01-20', '2024-06-01 00:00:00'), "
                "(:cpf_a, '1980-05-10', '2020-02-01 10:00:00', '2020-02-01 10:30:00', "
                "'2020-02-01', '2024-06-01 00:00:00'), "
                "(:cpf_b, '2000-02-29', '2020-03-10 12:00:00', '2020-03-10 12:30:00', "
                "'2020-03-10', '2024-06-01 00:00:00'), "
                "(NULL, '1990-07-15', '2020-04-01 12:00:00', '2020-04-01 12:30:00', "
                "'2020-04-01', '2024-06-01 00:00:00')"
            ),
            {"cpf_a": CPF_A, "cpf_b": CPF_B},
        )


def _rows(engine):
    with engine.connect() as c:
        return c.execute(
            text(
                "SELECT nu_cpf_cidadao, dt_nascimento, dt_inicial_atendimento, "
                "dt_final_atendimento, dt_visita, dt_atualizacao_sistema "
                "FROM public.tb_fat_atendimento_individual ORDER BY co_seq"
            )
        ).all()


def test_preserva_mes_ano_e_muda_apenas_dia(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    assert rows[0].dt_nascimento.year == 1980
    assert rows[0].dt_nascimento.month == 5
    assert rows[0].dt_nascimento != date(1980, 5, 10)
    assert 1 <= rows[2].dt_nascimento.day <= 29
    assert rows[3].dt_nascimento == date(1990, 7, 15)


def test_mesmo_cidadao_recebe_mesmo_deslocamento(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    first_delta = rows[0].dt_nascimento - date(1980, 5, 10)
    second_delta = rows[1].dt_nascimento - date(1980, 5, 10)
    assert first_delta == second_delta


def test_preserva_intervalo_entre_nascimento_e_atendimento(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    old_birth = date(1980, 5, 10)
    old_start = datetime(2020, 1, 20, 8, 30)
    old_interval = old_start.date() - old_birth
    new_interval = rows[0].dt_inicial_atendimento.date() - rows[0].dt_nascimento
    assert new_interval == old_interval
    assert rows[0].dt_final_atendimento - rows[0].dt_inicial_atendimento == (
        datetime(2020, 1, 20, 9, 0) - old_start
    )


def test_descobre_coluna_de_data_nao_declarada(pg_engine):
    """`dt_visita` nao esta em nenhuma lista curada - deve ser descoberta
    via information_schema e deslocada junto com o nascimento."""
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    old_birth = date(1980, 5, 10)
    old_visita = date(2020, 1, 20)
    old_interval = old_visita - old_birth
    new_interval = rows[0].dt_visita - rows[0].dt_nascimento
    assert new_interval == old_interval
    assert rows[0].dt_visita != old_visita


def test_ignora_coluna_de_metadado_do_sistema(pg_engine):
    """`dt_atualizacao_sistema` bate no denylist (%atualizacao%) - nao e
    evento clinico do cidadao e nao deve ser deslocada."""
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    assert rows[0].dt_atualizacao_sistema == datetime(2024, 6, 1, 0, 0)


def test_tabela_satelite_sem_nascimento_proprio_usa_delta_da_referencia(pg_engine):
    """tb_fat_atd_ind_procedimentos nao tem dt_nascimento proprio - o
    delta deve vir do join com tb_cidadao, calculado ANTES de
    tb_cidadao.dt_nascimento ser sobrescrito."""
    with pg_engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq serial PRIMARY KEY, nu_cpf text, dt_nascimento date)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_atd_ind_procedimentos "
                "(co_seq serial PRIMARY KEY, nu_cpf_cidadao text, dt_inicial_atendimento timestamp)"
            )
        )
        c.execute(
            text("INSERT INTO public.tb_cidadao (nu_cpf, dt_nascimento) VALUES (:cpf, '1980-05-10')"),
            {"cpf": CPF_A},
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_atd_ind_procedimentos "
                "(nu_cpf_cidadao, dt_inicial_atendimento) VALUES (:cpf, '2020-01-20 08:30:00')"
            ),
            {"cpf": CPF_A},
        )

    m.run(pg_engine)

    with pg_engine.connect() as c:
        nascimento = c.execute(text("SELECT dt_nascimento FROM public.tb_cidadao")).scalar()
        atendimento = c.execute(
            text("SELECT dt_inicial_atendimento FROM public.tb_fat_atd_ind_procedimentos")
        ).scalar()

    old_birth = date(1980, 5, 10)
    old_atendimento = datetime(2020, 1, 20, 8, 30)
    assert nascimento != old_birth
    assert atendimento.date() - nascimento == old_atendimento.date() - old_birth


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_poison "
                "(co_seq serial PRIMARY KEY, nu_cpf_cidadao text, dt_nascimento date)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_poison (nu_cpf_cidadao, dt_nascimento) "
                "VALUES (:cpf, '1980-05-10')"
            ),
            {"cpf": CPF_A},
        )
        c.execute(
            text(
                "CREATE FUNCTION boom() RETURNS trigger AS "
                "$$ BEGIN RAISE EXCEPTION 'boom'; END $$ LANGUAGE plpgsql"
            )
        )
        c.execute(
            text(
                "CREATE TRIGGER trg_boom BEFORE UPDATE ON public.tb_poison "
                "FOR EACH ROW EXECUTE FUNCTION boom()"
            )
        )

    monkeypatch.setattr(
        m,
        "DATE_TABLES",
        list(m.DATE_TABLES)
        + [m.DateTable("public", "tb_poison", "dt_nascimento", "nu_cpf_cidadao")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    rows = _rows(pg_engine)
    assert rows[0].dt_nascimento == date(1980, 5, 10)
    assert rows[0].dt_inicial_atendimento == datetime(2020, 1, 20, 8, 30)
