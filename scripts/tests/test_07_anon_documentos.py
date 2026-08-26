"""Testes da migration 07 (exclusao de documentos/anexos)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("07_anon_documentos.py")


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_arquivo_temporario "
                "(co_seq serial PRIMARY KEY, bl_arquivo bytea)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_arquivo "
                "(co_seq serial PRIMARY KEY, no_arquivo text, co_seq_arquivo bigint)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_arquivo_temporario (bl_arquivo) VALUES "
                "('\\x1234'::bytea), (NULL)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_arquivo (no_arquivo, co_seq_arquivo) VALUES "
                "('receita.pdf', 42), (NULL, 43)"
            )
        )


def _rows(engine):
    with engine.connect() as c:
        arquivo_temp = c.execute(
            text("SELECT bl_arquivo FROM public.tb_arquivo_temporario ORDER BY co_seq")
        ).scalars().all()
        arquivo = c.execute(
            text("SELECT no_arquivo, co_seq_arquivo FROM public.tb_arquivo ORDER BY co_seq")
        ).all()
    return arquivo_temp, arquivo


def test_conteudo_binario_e_excluido(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    arquivo_temp, _ = _rows(pg_engine)
    assert arquivo_temp[0] is None
    assert arquivo_temp[1] is None


def test_nome_de_arquivo_e_excluido_mas_fk_preservada(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    _, arquivo = _rows(pg_engine)
    assert arquivo[0].no_arquivo is None
    assert arquivo[0].co_seq_arquivo == 42  # chave substituta preservada
    assert arquivo[1].no_arquivo is None


def test_coluna_not_null_recebe_placeholder_em_vez_de_null(pg_engine, monkeypatch):
    """No banco real, `tb_arquivo.no_arquivo` e NOT NULL - um UPDATE ... SET
    = NULL quebra com NotNullViolation. Nesse caso a migration deve usar um
    placeholder generico em vez de NULL."""
    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_arquivo_not_null "
                "(co_seq serial PRIMARY KEY, no_arquivo text NOT NULL)"
            )
        )
        c.execute(
            text("INSERT INTO public.tb_arquivo_not_null (no_arquivo) VALUES ('exame.pdf')")
        )

    monkeypatch.setattr(
        m,
        "DOCUMENT_COLUMNS",
        list(m.DOCUMENT_COLUMNS)
        + [m.DocumentColumn("public", "tb_arquivo_not_null", "no_arquivo")],
    )

    m.run(pg_engine)

    with pg_engine.connect() as c:
        valor = c.execute(
            text("SELECT no_arquivo FROM public.tb_arquivo_not_null")
        ).scalar_one()
    assert valor == m.GENERIC_FILENAME


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text("CREATE TABLE public.tb_poison (co_seq serial PRIMARY KEY, no_arquivo text)")
        )
        c.execute(text("INSERT INTO public.tb_poison (no_arquivo) VALUES ('atestado.pdf')"))
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
        "DOCUMENT_COLUMNS",
        list(m.DOCUMENT_COLUMNS) + [m.DocumentColumn("public", "tb_poison", "no_arquivo")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    _, arquivo = _rows(pg_engine)
    assert arquivo[0].no_arquivo == "receita.pdf"
