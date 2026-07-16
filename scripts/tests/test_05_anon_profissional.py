"""Testes da migration 05 (profissionais)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("05_anon_profissional.py")

PROF_A = "Dra. Ana Souza"
PROF_B = "Dr. Bruno Lima"


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_dim_profissional "
                "(co_seq serial PRIMARY KEY, no_profissional text, co_categoria int)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_prof "
                "("
                "co_seq serial PRIMARY KEY, "
                "no_civil_profissional text, "
                "no_profissional_filtro text, "
                "no_social_profissional text, "
                "nu_conselho_classe text"
                ")"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_dim_profissional "
                "(no_profissional, co_categoria) VALUES "
                "(:a, 7), (:b, 8), (NULL, 9)"
            ),
            {"a": PROF_A, "b": PROF_B},
        )
        c.execute(
            text(
                "INSERT INTO public.tb_prof "
                "(no_civil_profissional, no_profissional_filtro, no_social_profissional, "
                "nu_conselho_classe) VALUES (:a, :a, :b, 'ABC123')"
            ),
            {"a": PROF_A, "b": PROF_B},
        )


def _values(engine):
    with engine.connect() as c:
        dim = c.execute(
            text(
                "SELECT no_profissional, co_categoria "
                "FROM public.tb_dim_profissional ORDER BY co_seq"
            )
        ).all()
        prof = c.execute(
            text(
                "SELECT no_civil_profissional, no_profissional_filtro, "
                "no_social_profissional, nu_conselho_classe FROM public.tb_prof"
            )
        ).one()
    return dim, prof


def test_anonimiza_nomes_com_sobrenome_teste(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    dim, prof = _values(pg_engine)

    assert dim[0].no_profissional.endswith("Teste")
    assert dim[1].no_profissional.endswith("Teste")
    assert dim[0].no_profissional != PROF_A
    assert dim[1].no_profissional != PROF_B
    assert prof.no_civil_profissional == dim[0].no_profissional
    assert prof.no_profissional_filtro == dim[0].no_profissional
    assert prof.no_social_profissional == dim[1].no_profissional
    assert dim[2].no_profissional is None


def test_geracao_de_nome_faker_e_deterministica():
    assert m._fake_name(0) == m._fake_name(0)
    assert m._fake_name(1) == m._fake_name(1)
    assert m._fake_name(0).endswith("Teste")
    assert m._fake_name(1).endswith("Teste")
    assert m._fake_name(0) != m._fake_name(1)


def test_substitui_registro_e_preserva_categoria(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    dim, prof = _values(pg_engine)

    assert prof.nu_conselho_classe == m.GENERIC_REGISTRATION
    assert [row.co_categoria for row in dim] == [7, 8, 9]


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_poison "
                "(co_seq serial PRIMARY KEY, no_profissional text)"
            )
        )
        c.execute(
            text("INSERT INTO public.tb_poison (no_profissional) VALUES (:a)"),
            {"a": PROF_A},
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
        "NAME_COLUMNS",
        list(m.NAME_COLUMNS) + [m.ColumnTarget("public", "tb_poison", "no_profissional")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    dim, prof = _values(pg_engine)
    assert dim[0].no_profissional == PROF_A
    assert prof.no_civil_profissional == PROF_A
    assert prof.nu_conselho_classe == "ABC123"
