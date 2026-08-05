"""Testes da migration 10 (hash provisorio de CNS)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("10_anon_cns.py")

CNS_A = "700000000000001"


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq serial PRIMARY KEY, nu_cns varchar(15), nu_cns_responsavel varchar(15))"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_cidadao "
                "(co_seq serial PRIMARY KEY, nu_cns char(15))"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_cidadao (nu_cns, nu_cns_responsavel) VALUES "
                "(:a, NULL), (NULL, ''), "
                "(:a, NULL)"
            ),
            {"a": CNS_A},
        )
        c.execute(text("INSERT INTO public.tb_fat_cidadao (nu_cns) VALUES (:a)"), {"a": CNS_A})


def _rows(engine):
    with engine.connect() as c:
        cidadao = c.execute(
            text("SELECT nu_cns, nu_cns_responsavel FROM public.tb_cidadao ORDER BY co_seq")
        ).all()
        fat = c.execute(text("SELECT nu_cns FROM public.tb_fat_cidadao")).scalar()
    return cidadao, fat


def test_valor_e_hasheado(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, fat = _rows(pg_engine)

    assert cidadao[0].nu_cns != CNS_A
    assert cidadao[0].nu_cns is not None
    assert fat.strip() != CNS_A


def test_mesmo_cns_gera_mesmo_hash(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, fat = _rows(pg_engine)

    assert cidadao[0].nu_cns == cidadao[2].nu_cns
    assert cidadao[0].nu_cns == fat.strip()


def test_nulos_e_vazios_preservados(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, _ = _rows(pg_engine)

    assert cidadao[0].nu_cns_responsavel is None
    assert cidadao[1].nu_cns is None
    assert cidadao[1].nu_cns_responsavel == ""


def test_respeita_limite_de_tamanho_da_coluna(pg_engine):
    """Uma coluna mais estreita que 15 (o tamanho do CNS) nao pode estourar."""
    with pg_engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text("CREATE TABLE public.tb_prof (co_seq serial PRIMARY KEY, nu_cns varchar(10))")
        )
        c.execute(text("INSERT INTO public.tb_prof (nu_cns) VALUES (:a)"), {"a": "7000000000"})

    m.run(pg_engine)

    with pg_engine.connect() as c:
        value = c.execute(text("SELECT nu_cns FROM public.tb_prof")).scalar()
    assert value != "7000000000"
    assert len(value) <= 10


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text("CREATE TABLE public.tb_poison (co_seq serial PRIMARY KEY, nu_cns varchar(15))")
        )
        c.execute(text("INSERT INTO public.tb_poison (nu_cns) VALUES (:a)"), {"a": CNS_A})
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
        "CNS_COLUMNS",
        list(m.CNS_COLUMNS) + [m.CnsColumn("public", "tb_poison", "nu_cns")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    cidadao, _ = _rows(pg_engine)
    assert cidadao[0].nu_cns == CNS_A
