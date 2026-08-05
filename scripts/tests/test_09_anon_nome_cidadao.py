"""Testes da migration 09 (nome do cidadao)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("09_anon_nome_cidadao.py")

NOME_A = "Joana da Silva"
NOME_MAE_A = "Maria da Silva"


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_cad_individual "
                "(co_seq serial PRIMARY KEY, no_nome text, no_nome_mae text, "
                "no_nome_pai text, no_nome_social text)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_marca_consumo_alimnt "
                "(co_seq serial PRIMARY KEY, no_nome text)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_cad_individual "
                "(no_nome, no_nome_mae, no_nome_pai, no_nome_social) VALUES "
                "(:nome, :mae, NULL, ''), "
                "(NULL, NULL, NULL, NULL)"
            ),
            {"nome": NOME_A, "mae": NOME_MAE_A},
        )
        # mesma pessoa aparece em outra tabela - deve receber o mesmo nome ficticio.
        c.execute(
            text("INSERT INTO public.tb_fat_marca_consumo_alimnt (no_nome) VALUES (:nome)"),
            {"nome": NOME_A},
        )


def _rows(engine):
    with engine.connect() as c:
        cad = c.execute(
            text(
                "SELECT no_nome, no_nome_mae, no_nome_pai, no_nome_social "
                "FROM public.tb_fat_cad_individual ORDER BY co_seq"
            )
        ).all()
        marca = c.execute(
            text("SELECT no_nome FROM public.tb_fat_marca_consumo_alimnt")
        ).scalar()
    return cad, marca


def test_substitui_nomes_por_ficticios(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cad, marca = _rows(pg_engine)

    assert cad[0].no_nome != NOME_A
    assert cad[0].no_nome_mae != NOME_MAE_A
    assert marca != NOME_A


def test_mesmo_valor_gera_mesmo_ficticio_entre_tabelas(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cad, marca = _rows(pg_engine)

    assert cad[0].no_nome == marca


def test_nulos_e_vazios_preservados(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cad, _ = _rows(pg_engine)

    assert cad[0].no_nome_pai is None
    assert cad[0].no_nome_social == ""
    assert cad[1].no_nome is None


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text("CREATE TABLE public.tb_poison (co_seq serial PRIMARY KEY, no_nome text)")
        )
        c.execute(text("INSERT INTO public.tb_poison (no_nome) VALUES (:n)"), {"n": NOME_A})
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
        list(m.NAME_COLUMNS) + [m.NameColumn("public", "tb_poison", "no_nome")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    cad, _ = _rows(pg_engine)
    assert cad[0].no_nome == NOME_A
