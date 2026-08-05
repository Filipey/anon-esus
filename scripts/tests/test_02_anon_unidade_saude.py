"""Testes da migration 02 (anonimização de nomes de unidades de saúde).

Rodam contra a fixture `pg_engine` (Postgres efêmero). O orquestrador
executa este arquivo ANTES de aplicar a migration no banco real; só
aplica se tudo passar.
"""

from __future__ import annotations

import re

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("02_anon_unidade_saude.py")

# Nomes de unidades usados nas fixtures. "Posto Alvorada" aparece em duas
# tabelas para exercitar a consistência entre tabelas.
U_A = "UBS Central"
U_B = "Posto Alvorada"
U_C = "Centro de Saúde Norte"

_GENERICO = re.compile(r"^Unidade de Saúde \d+$")


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_unidade_saude "
                "(co_seq serial PRIMARY KEY, no_unidade_saude text)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_dim_unidade_saude "
                "(co_seq serial PRIMARY KEY, no_unidade_saude text, co_dim_unidade_saude int)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_unidade_saude (no_unidade_saude) VALUES "
                "(:a), (:b), (:c), (NULL)"
            ),
            {"a": U_A, "b": U_B, "c": U_C},
        )
        c.execute(
            text(
                "INSERT INTO public.tb_dim_unidade_saude "
                "(no_unidade_saude, co_dim_unidade_saude) VALUES (:b, 10)"
            ),
            {"b": U_B},
        )


def _values(engine):
    with engine.connect() as c:
        unidades = c.execute(
            text("SELECT no_unidade_saude FROM public.tb_unidade_saude ORDER BY co_seq")
        ).scalars().all()
        dim = c.execute(
            text("SELECT no_unidade_saude, co_dim_unidade_saude FROM public.tb_dim_unidade_saude")
        ).one()
    return unidades, dim


def test_substitui_por_denominacao_generica(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    unidades, dim = _values(pg_engine)

    originais = {U_A, U_B, U_C}
    presentes = {v for v in unidades if v is not None} | {dim[0]}
    assert presentes.isdisjoint(originais), "algum nome original sobreviveu"
    for v in presentes:
        assert _GENERICO.match(v), f"formato inesperado: {v}"


def test_consistente_entre_tabelas(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    unidades, dim = _values(pg_engine)
    # U_B em tb_unidade_saude (índice 1) e em tb_dim_unidade_saude -> mesmo rótulo.
    assert unidades[1] == dim[0]
    assert dim[1] == 10


def test_numeracao_deterministica(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    unidades, _ = _values(pg_engine)
    # Ordem alfabética: Centro(1) < Posto(2) < UBS(3).
    assert unidades[0] == "Unidade de Saúde 3"  # UBS Central
    assert unidades[1] == "Unidade de Saúde 2"  # Posto Alvorada
    assert unidades[2] == "Unidade de Saúde 1"  # Centro de Saúde Norte


def test_nomes_distintos_recebem_rotulos_distintos(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    unidades, _ = _values(pg_engine)
    rotulos = [v for v in unidades if v is not None]
    assert len(set(rotulos)) == 3


def test_nulls_permanecem_nulos(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    unidades, _ = _values(pg_engine)
    assert unidades[3] is None  # 4ª linha era NULL


def test_cnes_e_substituido_e_consistente_entre_tabelas(pg_engine):
    with pg_engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_unidade_saude "
                "(co_seq serial PRIMARY KEY, no_unidade_saude text, nu_cnes text)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_dim_unidade_saude "
                "(co_seq serial PRIMARY KEY, no_unidade_saude text, nu_cnes text)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_unidade_saude (no_unidade_saude, nu_cnes) VALUES "
                "(:a, '1234567')"
            ),
            {"a": U_A},
        )
        c.execute(
            text(
                "INSERT INTO public.tb_dim_unidade_saude (no_unidade_saude, nu_cnes) VALUES "
                "(:a, '1234567')"
            ),
            {"a": U_A},
        )

    m.run(pg_engine)

    with pg_engine.connect() as c:
        cnes_a = c.execute(text("SELECT nu_cnes FROM public.tb_unidade_saude")).scalar()
        cnes_b = c.execute(text("SELECT nu_cnes FROM public.tb_dim_unidade_saude")).scalar()

    assert cnes_a != "1234567"
    assert len(cnes_a) == 7 and cnes_a.isdigit()
    assert cnes_a == cnes_b


def test_cnes_e_substituido_tambem_nas_tabelas_de_referencia(pg_engine):
    """tb_familia.nu_cnes guarda o valor real copiado, nao uma FK - se nao
    for trocado com o mesmo mapa, da pra religar a unidade fake a real."""
    with pg_engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_unidade_saude "
                "(co_seq serial PRIMARY KEY, no_unidade_saude text, nu_cnes text)"
            )
        )
        c.execute(text("CREATE TABLE public.tb_familia (co_seq serial PRIMARY KEY, nu_cnes text)"))
        c.execute(
            text(
                "INSERT INTO public.tb_unidade_saude (no_unidade_saude, nu_cnes) VALUES (:a, '1234567')"
            ),
            {"a": U_A},
        )
        c.execute(text("INSERT INTO public.tb_familia (nu_cnes) VALUES ('1234567')"))

    m.run(pg_engine)

    with pg_engine.connect() as c:
        cnes_unidade = c.execute(text("SELECT nu_cnes FROM public.tb_unidade_saude")).scalar()
        cnes_familia = c.execute(text("SELECT nu_cnes FROM public.tb_familia")).scalar()

    assert cnes_familia != "1234567"
    assert cnes_familia == cnes_unidade


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    """Se uma coluna-alvo falhar no meio, NADA é alterado (rollback)."""
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_poison "
                "(co_seq serial PRIMARY KEY, no_unidade_saude text)"
            )
        )
        c.execute(
            text("INSERT INTO public.tb_poison (no_unidade_saude) VALUES (:a)"),
            {"a": U_A},
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
        list(m.NAME_COLUMNS) + [m.NameColumn("public", "tb_poison", "no_unidade_saude")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    unidades, dim = _values(pg_engine)
    assert unidades[0] == U_A
    assert unidades[1] == U_B
    assert unidades[2] == U_C
    assert dim[0] == U_B
