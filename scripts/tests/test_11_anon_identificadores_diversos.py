"""Testes da migration 11 (identificadores diversos)."""

from __future__ import annotations

from datetime import date

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("11_anon_identificadores_diversos.py")


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_atendimento_individual "
                "(co_seq serial PRIMARY KEY, nu_prontuario varchar(30))"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq serial PRIMARY KEY, nu_telefone_celular varchar(20), "
                "nu_nis_pis_pasep varchar(11), nu_portaria_naturalizacao varchar(30), "
                "dt_naturalizacao date)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_cad_individual "
                "(co_seq serial PRIMARY KEY, nu_obito_do varchar(30))"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_familia "
                "(co_seq serial PRIMARY KEY, nu_cpf_cns_responsavel varchar(20))"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_atendimento_individual (nu_prontuario) VALUES "
                "('PRONT-001'), ('PRONT-001'), (NULL)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_cidadao "
                "(nu_telefone_celular, nu_nis_pis_pasep, nu_portaria_naturalizacao, "
                "dt_naturalizacao) VALUES "
                "('11999998888', '12345678901', 'PORTARIA-2020-01', '2020-05-15')"
            )
        )
        c.execute(text("INSERT INTO public.tb_fat_cad_individual (nu_obito_do) VALUES ('DO-123')"))
        c.execute(
            text(
                "INSERT INTO public.tb_familia (nu_cpf_cns_responsavel) VALUES "
                "('52998224725'), ('123456789012345')"
            )
        )


def _rows(engine):
    with engine.connect() as c:
        prontuario = c.execute(
            text("SELECT nu_prontuario FROM public.tb_fat_atendimento_individual ORDER BY co_seq")
        ).scalars().all()
        cidadao = c.execute(
            text(
                "SELECT nu_telefone_celular, nu_nis_pis_pasep, nu_portaria_naturalizacao, "
                "dt_naturalizacao FROM public.tb_cidadao"
            )
        ).first()
        obito = c.execute(text("SELECT nu_obito_do FROM public.tb_fat_cad_individual")).scalar()
        familia = c.execute(
            text("SELECT nu_cpf_cns_responsavel FROM public.tb_familia ORDER BY co_seq")
        ).scalars().all()
    return prontuario, cidadao, obito, familia


def test_prontuario_e_hasheado_consistente(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    prontuario, *_ = _rows(pg_engine)

    assert prontuario[0] != "PRONT-001"
    assert prontuario[0] == prontuario[1]  # mesmo valor original -> mesmo hash
    assert prontuario[2] is None


def test_telefone_e_substituido_por_ficticio(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    _, cidadao, _, _ = _rows(pg_engine)

    assert cidadao.nu_telefone_celular != "11999998888"
    assert len(cidadao.nu_telefone_celular) == 11


def test_nis_e_hasheado(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    _, cidadao, _, _ = _rows(pg_engine)

    assert cidadao.nu_nis_pis_pasep != "12345678901"


def test_naturalizacao_numero_hasheado_e_data_reduzida_ao_ano(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    _, cidadao, _, _ = _rows(pg_engine)

    assert cidadao.nu_portaria_naturalizacao != "PORTARIA-2020-01"
    assert cidadao.dt_naturalizacao == date(2020, 1, 1)


def test_obito_e_hasheado(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    _, _, obito, _ = _rows(pg_engine)

    assert obito != "DO-123"


def test_identificacao_mista_detecta_formato_por_tamanho(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    *_, familia = _rows(pg_engine)

    assert familia[0] != "52998224725"
    assert len(familia[0]) == 11  # tratado como CPF (11 digitos originais)
    assert familia[1] != "123456789012345"
    assert len(familia[1]) == 15  # tratado como CNS (15 digitos originais)


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_poison "
                "(co_seq serial PRIMARY KEY, nu_prontuario varchar(30))"
            )
        )
        c.execute(text("INSERT INTO public.tb_poison (nu_prontuario) VALUES ('PRONT-999')"))
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
        "PRONTUARIO_COLUMNS",
        list(m.PRONTUARIO_COLUMNS) + [m.Column("public", "tb_poison", "nu_prontuario")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    prontuario, *_ = _rows(pg_engine)
    assert prontuario[0] == "PRONT-001"
