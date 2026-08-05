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


def test_numero_da_casa_troca_junto_com_o_resto_do_endereco(pg_engine):
    """nu_numero/st_sem_numero precisam fazer parte do mesmo conjunto
    trocado atomicamente - senao o numero original sobrevive junto com
    rua/bairro de outro endereco (o "Frankenstein" que a migration
    existe para evitar)."""
    with pg_engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "("
                "co_seq serial PRIMARY KEY, "
                "co_dim_municipio int, "
                "ds_cep text, ds_complemento text, ds_logradouro text, "
                "ds_ponto_referencia text, no_bairro text, no_bairro_filtro text, "
                "nu_numero text, st_sem_numero int"
                ")"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_cidadao "
                "(co_dim_municipio, ds_cep, ds_complemento, ds_logradouro, "
                "ds_ponto_referencia, no_bairro, no_bairro_filtro, nu_numero, st_sem_numero) "
                "VALUES "
                "(1, '11111-111', 'Apto 1', 'Rua A', 'Padaria', 'Centro', 'centro', '10', 0), "
                "(1, '22222-222', 'Casa', 'Rua B', 'Escola', 'Norte', 'norte', '20', 0)"
            )
        )

    m.run(pg_engine)

    with pg_engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT ds_logradouro, nu_numero FROM public.tb_cidadao ORDER BY co_seq"
            )
        ).all()

    # Cada linha recebeu o par (logradouro, numero) de UMA candidata real,
    # nao a rua de uma linha com o numero da outra.
    valid_pairs = {("Rua A", "10"), ("Rua B", "20")}
    for row in rows:
        assert (row.ds_logradouro, row.nu_numero) in valid_pairs
    assert (rows[0].ds_logradouro, rows[0].nu_numero) != ("Rua A", "10")
    assert (rows[1].ds_logradouro, rows[1].nu_numero) != ("Rua B", "20")


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
