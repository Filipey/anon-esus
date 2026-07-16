"""Testes da migration 03 (anonimização de e-mails).

Rodam contra a fixture `pg_engine` (Postgres efêmero). O orquestrador
executa este arquivo ANTES de aplicar a migration no banco real; só
aplica se tudo passar.
"""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("03_anon_email.py")

EMAIL_1 = "joao.silva@gmail.com"
EMAIL_2 = "MARIA@HOTMAIL.COM"


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq serial PRIMARY KEY, ds_email text)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_cad_individual "
                "(co_seq serial PRIMARY KEY, no_email text)"
            )
        )
        # e-mail preenchido, nulo e vazio (vazio deve ser preservado).
        c.execute(
            text(
                "INSERT INTO public.tb_cidadao (ds_email) VALUES "
                "(:e1), (NULL), ('')"
            ),
            {"e1": EMAIL_1},
        )
        c.execute(
            text("INSERT INTO public.tb_fat_cad_individual (no_email) VALUES (:e1)"),
            {"e1": EMAIL_1},
        )


def _values(engine):
    with engine.connect() as c:
        cidadao = c.execute(
            text("SELECT ds_email FROM public.tb_cidadao ORDER BY co_seq")
        ).scalars().all()
        fat = c.execute(text("SELECT no_email FROM public.tb_fat_cad_individual")).scalar()
    return cidadao, fat


def test_substitui_emails_pela_constante(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, fat = _values(pg_engine)
    assert cidadao[0] == m.GENERIC_EMAIL
    assert fat == m.GENERIC_EMAIL


def test_nulls_e_vazios_preservados(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, _ = _values(pg_engine)
    assert cidadao[1] is None  # era NULL
    assert cidadao[2] == ""    # era string vazia


def test_nenhum_email_original_permanece(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, fat = _values(pg_engine)
    todos = {v for v in cidadao if v} | {fat}
    assert EMAIL_1 not in todos and EMAIL_2 not in todos


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    """Se uma coluna-alvo falhar no meio, NADA é alterado (rollback)."""
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_poison "
                "(co_seq serial PRIMARY KEY, no_email text)"
            )
        )
        c.execute(
            text("INSERT INTO public.tb_poison (no_email) VALUES (:e)"),
            {"e": EMAIL_1},
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
        "EMAIL_COLUMNS",
        list(m.EMAIL_COLUMNS) + [m.EmailColumn("public", "tb_poison", "no_email")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    cidadao, fat = _values(pg_engine)
    assert cidadao[0] == EMAIL_1
    assert fat == EMAIL_1
