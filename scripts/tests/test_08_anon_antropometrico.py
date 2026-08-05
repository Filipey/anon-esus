"""Testes da migration 08 (hash provisorio de dados antropometricos)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("08_anon_antropometrico.py")


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_atendimento_individual "
                "("
                "co_seq serial PRIMARY KEY, "
                "nu_peso numeric, "
                "nu_altura numeric, "
                "nu_perimetro_cefalico numeric, "
                "nu_circ_abdominal numeric, "
                "nu_perim_panturrilha numeric"
                ")"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_atendimento_individual "
                "(nu_peso, nu_altura, nu_perimetro_cefalico, nu_circ_abdominal, "
                "nu_perim_panturrilha) VALUES "
                "(72.5, 170.0, 55.0, 90.0, 35.0), "
                "(72.5, 170.0, 55.0, 90.0, 35.0), "
                "(NULL, NULL, NULL, NULL, NULL)"
            )
        )


def _rows(engine):
    with engine.connect() as c:
        return c.execute(
            text(
                "SELECT nu_peso, nu_altura, nu_perimetro_cefalico, "
                "nu_circ_abdominal, nu_perim_panturrilha "
                "FROM public.tb_fat_atendimento_individual ORDER BY co_seq"
            )
        ).all()


def test_valores_sao_alterados(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    assert rows[0].nu_peso != 72.5
    assert rows[0].nu_altura != 170.0
    assert rows[0].nu_perimetro_cefalico != 55.0
    assert rows[0].nu_circ_abdominal != 90.0
    assert rows[0].nu_perim_panturrilha != 35.0


def test_mesmo_valor_original_gera_mesmo_hash(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    assert rows[0].nu_peso == rows[1].nu_peso
    assert rows[0].nu_altura == rows[1].nu_altura


def test_nulos_permanecem_nulos(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    assert rows[2].nu_peso is None
    assert rows[2].nu_altura is None
    assert rows[2].nu_perimetro_cefalico is None


def test_tb_medicao_colunas_texto_sao_hasheadas(pg_engine):
    """tb_medicao guarda os sinais vitais como character varying, nao
    numeric - exercita o branch de texto do hash."""
    with pg_engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_medicao "
                "(co_seq_medicao serial PRIMARY KEY, nu_medicao_peso varchar(20), "
                "nu_medicao_altura varchar(20))"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_medicao (nu_medicao_peso, nu_medicao_altura) VALUES "
                "('72.5', '170.0'), ('72.5', '170.0')"
            )
        )

    m.run(pg_engine)

    with pg_engine.connect() as c:
        rows = c.execute(
            text("SELECT nu_medicao_peso, nu_medicao_altura FROM public.tb_medicao ORDER BY co_seq_medicao")
        ).all()

    assert rows[0].nu_medicao_peso != "72.5"
    assert rows[0].nu_medicao_peso == rows[1].nu_medicao_peso  # mesmo valor -> mesmo hash


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text("CREATE TABLE public.tb_poison (co_seq serial PRIMARY KEY, nu_peso numeric)")
        )
        c.execute(text("INSERT INTO public.tb_poison (nu_peso) VALUES (80.0)"))
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
        "ANTHRO_COLUMNS",
        list(m.ANTHRO_COLUMNS) + [m.AnthroColumn("public", "tb_poison", "nu_peso")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    rows = _rows(pg_engine)
    assert rows[0].nu_peso == 72.5
