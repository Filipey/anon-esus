"""Testes da migration 06 (enderecos)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("06_anon_endereco.py")


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_cad_domiciliar "
                "("
                "co_seq serial PRIMARY KEY, "
                "co_dim_municipio int, "
                "no_bairro text, "
                "no_complemento text, "
                "no_logradouro text, "
                "no_ponto_referencia text, "
                "nu_cep text, "
                "nu_num_logradouro text"
                ")"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_cad_domiciliar "
                "(co_dim_municipio, no_bairro, no_complemento, no_logradouro, "
                "no_ponto_referencia, nu_cep, nu_num_logradouro) VALUES "
                "(1, 'Centro', 'Apto 1', 'Rua A', 'Padaria', '11111-111', '10'), "
                "(1, 'Norte', 'Casa', 'Rua B', 'Escola', '22222-222', '20'), "
                "(2, 'Sul', 'Fundos', 'Rua C', 'Praça', '33333-333', '30'), "
                "(2, 'Leste', 'Bloco 2', 'Rua D', 'Posto', '44444-444', '40'), "
                "(3, 'Unico', NULL, 'Rua E', NULL, '55555-555', '50'), "
                "(1, NULL, NULL, NULL, NULL, NULL, NULL)"
            )
        )


def _rows(engine):
    with engine.connect() as c:
        return c.execute(
            text(
                "SELECT co_dim_municipio, no_bairro, no_complemento, no_logradouro, "
                "no_ponto_referencia, nu_cep, nu_num_logradouro "
                "FROM public.tb_fat_cad_domiciliar ORDER BY co_seq"
            )
        ).all()


def _address(row):
    return (
        row.no_bairro,
        row.no_complemento,
        row.no_logradouro,
        row.no_ponto_referencia,
        row.nu_cep,
        row.nu_num_logradouro,
    )


def test_substitui_por_outro_endereco_do_mesmo_municipio(pg_engine):
    _seed(pg_engine)
    before = _rows(pg_engine)
    before_by_municipality = {}
    for row in before:
        if any(_address(row)):
            before_by_municipality.setdefault(row.co_dim_municipio, set()).add(_address(row))

    m.run(pg_engine)
    after = _rows(pg_engine)

    for old, new in zip(before[:4], after[:4], strict=True):
        assert new.co_dim_municipio == old.co_dim_municipio
        assert _address(new) in before_by_municipality[old.co_dim_municipio]
        assert _address(new) != _address(old)


def test_municipio_com_apenas_um_endereco_permanece_igual(pg_engine):
    _seed(pg_engine)
    before = _rows(pg_engine)
    m.run(pg_engine)
    after = _rows(pg_engine)

    assert _address(after[4]) == _address(before[4])


def test_linha_sem_endereco_permanece_igual(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    after = _rows(pg_engine)

    assert _address(after[5]) == (None, None, None, None, None, None)


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_poison "
                "(co_seq serial PRIMARY KEY, co_dim_municipio int, no_bairro text)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_poison (co_dim_municipio, no_bairro) "
                "VALUES (1, 'Centro'), (1, 'Norte')"
            )
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
        "ADDRESS_TABLES",
        list(m.ADDRESS_TABLES)
        + [
            m.AddressTable(
                "public",
                "tb_poison",
                ("no_bairro",),
                ("co_dim_municipio",),
            )
        ],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    after = _rows(pg_engine)
    assert _address(after[0]) == (
        "Centro",
        "Apto 1",
        "Rua A",
        "Padaria",
        "11111-111",
        "10",
    )
