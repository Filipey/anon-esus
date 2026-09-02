"""Testes da migration 14 (coordenada de visita e micro-area)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("14_anon_territorio.py")


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_visita_domiciliar "
                "(co_seq serial PRIMARY KEY, nu_latitude double precision, "
                "nu_longitude double precision, nu_micro_area varchar(10), "
                "nu_cpf_cidadao varchar(11))"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_cds_visita_domiciliar "
                "(co_seq serial PRIMARY KEY, nu_latitude double precision, "
                "nu_longitude double precision, nu_micro_area varchar(10))"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq serial PRIMARY KEY, nu_micro_area varchar(10), "
                "co_dim_equipe bigint)"
            )
        )
        # NOT NULL de texto: nao aceita NULL, recebe placeholder.
        c.execute(
            text(
                "CREATE TABLE public.tb_dim_agrupador_filtro "
                "(co_seq serial PRIMARY KEY, nu_micro_area varchar(10) NOT NULL)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_visita_domiciliar "
                "(nu_latitude, nu_longitude, nu_micro_area, nu_cpf_cidadao) VALUES "
                "(-19.9227, -43.9451, '01', '52998224725'), "
                "(-19.9228, -43.9450, '01', '52998224725'), "
                "(NULL, NULL, '02', '11144477735')"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_cds_visita_domiciliar "
                "(nu_latitude, nu_longitude, nu_micro_area) VALUES "
                "(-19.9227, -43.9451, '01')"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_cidadao (nu_micro_area, co_dim_equipe) VALUES "
                "('01', 7), ('02', 8)"
            )
        )
        c.execute(
            text("INSERT INTO public.tb_dim_agrupador_filtro (nu_micro_area) VALUES ('01')")
        )


def test_coordenada_de_visita_e_suprimida(pg_engine):
    """O achado central: a coordenada da visita e a residencia em outro formato."""
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        pontos = c.execute(
            text(
                "SELECT nu_latitude, nu_longitude "
                "FROM public.tb_fat_visita_domiciliar ORDER BY co_seq"
            )
        ).all()
        cds = c.execute(
            text("SELECT nu_latitude, nu_longitude FROM public.tb_cds_visita_domiciliar")
        ).first()

    assert all(lat is None and lng is None for lat, lng in pontos)
    assert cds.nu_latitude is None and cds.nu_longitude is None


def test_nao_sobra_nenhum_rastro_geolocalizado_por_cidadao(pg_engine):
    """Sem coordenada nenhuma, o aglomerado de pontos por cidadao deixa de existir.

    Era ele que estimava a residencia com erro da ordem de 5 m e permitia
    inverter a troca de endereco da migration 06.
    """
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        geolocalizados = c.execute(
            text(
                "SELECT count(DISTINCT nu_cpf_cidadao) "
                "FROM public.tb_fat_visita_domiciliar "
                "WHERE nu_latitude IS NOT NULL AND nu_longitude IS NOT NULL"
            )
        ).scalar()

    assert geolocalizados == 0


def test_micro_area_e_suprimida(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        cidadao = c.execute(
            text("SELECT nu_micro_area FROM public.tb_cidadao ORDER BY co_seq")
        ).scalars().all()
        visita = c.execute(
            text("SELECT nu_micro_area FROM public.tb_fat_visita_domiciliar ORDER BY co_seq")
        ).scalars().all()

    assert all(v is None for v in cidadao)
    assert all(v is None for v in visita)


def test_coluna_not_null_recebe_placeholder(pg_engine):
    """Coluna de texto NOT NULL nao aceita NULL - esvazia sem quebrar a constraint."""
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        valor = c.execute(
            text("SELECT nu_micro_area FROM public.tb_dim_agrupador_filtro")
        ).scalar()

    assert valor == ""


def test_chave_substituta_de_equipe_nao_e_tocada(pg_engine):
    """A equipe continua vinculada: some o territorio, nao o vinculo."""
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        equipes = c.execute(
            text("SELECT co_dim_equipe FROM public.tb_cidadao ORDER BY co_seq")
        ).scalars().all()

    assert equipes == [7, 8]


def test_coordenada_not_null_nao_textual_e_pulada_com_aviso(pg_engine, caplog):
    """Zerar criaria coordenada ficticia plausivel - pior que nao tratar."""
    with pg_engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_cds_visita_domiciliar "
                "(co_seq serial PRIMARY KEY, nu_latitude double precision NOT NULL, "
                "nu_longitude double precision NOT NULL)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_cds_visita_domiciliar (nu_latitude, nu_longitude) "
                "VALUES (-19.9227, -43.9451)"
            )
        )

    m.run(pg_engine)

    with pg_engine.connect() as c:
        lat = c.execute(
            text("SELECT nu_latitude FROM public.tb_cds_visita_domiciliar")
        ).scalar()

    assert lat == pytest.approx(-19.9227)  # preservada, e sinalizada no log
    assert "NOT NULL nao textual" in caplog.text


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    alvos = list(m.MICRO_AREA_COLUMNS) + [m.Column("public", "tb_cidadao", "nu_micro_area")]
    monkeypatch.setattr(m, "MICRO_AREA_COLUMNS", alvos)

    original = m._column_info
    chamadas = {"n": 0}

    def explode(conn, col):
        chamadas["n"] += 1
        if chamadas["n"] > 3:
            raise RuntimeError("falha simulada no meio da migration")
        return original(conn, col)

    monkeypatch.setattr(m, "_column_info", explode)

    with pytest.raises(RuntimeError):
        m.run(pg_engine)

    with pg_engine.connect() as c:
        lat = c.execute(
            text(
                "SELECT nu_latitude FROM public.tb_fat_visita_domiciliar ORDER BY co_seq"
            )
        ).scalars().first()

    assert lat == pytest.approx(-19.9227)  # nada foi commitado
