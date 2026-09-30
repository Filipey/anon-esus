"""Testes da migration 13 (INE - Identificador Nacional de Equipe)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text
from sqlalchemy.exc import DataError

m = load_migration("13_anon_ine.py")


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_equipe "
                "(co_seq serial PRIMARY KEY, nu_ine varchar(10), co_equipe bigint)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_familia "
                "(co_seq serial PRIMARY KEY, nu_ine varchar(10))"
            )
        )
        # Coluna de papel: se so as tabelas "mestras" fossem trocadas, o INE
        # original sobreviveria aqui e religaria a equipe ficticia a real.
        c.execute(
            text(
                "CREATE TABLE public.tb_acomp_cidadaos_vinculados "
                "(co_seq serial PRIMARY KEY, nu_ine_vinc_equipe varchar(10))"
            )
        )
        # Largura menor que 10: o valor ficticio precisa caber aqui tambem.
        c.execute(
            text(
                "CREATE TABLE public.tb_historico_dados_fcc "
                "(co_seq serial PRIMARY KEY, nu_ine_executante varchar(6), "
                "nu_ine_solicitante varchar(6))"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_equipe (nu_ine, co_equipe) VALUES "
                "('0000123456', 77), ('0000987654', 88), (NULL, 99)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_familia (nu_ine) VALUES "
                "('0000123456'), ('0000123456')"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_acomp_cidadaos_vinculados "
                "(nu_ine_vinc_equipe) VALUES ('0000123456')"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_historico_dados_fcc "
                "(nu_ine_executante, nu_ine_solicitante) VALUES ('123456', '987654')"
            )
        )


def test_ine_e_substituido(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        ines = c.execute(
            text("SELECT nu_ine FROM public.tb_equipe ORDER BY co_seq")
        ).scalars().all()

    assert ines[0] != "0000123456"
    assert ines[1] != "0000987654"
    assert ines[2] is None
    assert ines[0] != ines[1]  # INEs distintos continuam distintos


def test_mapa_e_consistente_entre_tabelas(pg_engine):
    """O mesmo INE original vira o mesmo ficticio em toda a base.

    E o que preserva os joins de equipe - e o que impede que a equipe
    ficticia seja religada a real por uma coluna esquecida.
    """
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        equipe = c.execute(
            text("SELECT nu_ine FROM public.tb_equipe ORDER BY co_seq")
        ).scalars().first()
        familia = c.execute(
            text("SELECT nu_ine FROM public.tb_familia ORDER BY co_seq")
        ).scalars().all()
        acomp = c.execute(
            text("SELECT nu_ine_vinc_equipe FROM public.tb_acomp_cidadaos_vinculados")
        ).scalar()

    assert familia[0] == familia[1] == equipe
    assert acomp == equipe


def test_chave_substituta_de_equipe_nao_e_tocada(pg_engine):
    """`co_equipe` preserva o vinculo sem revelar a equipe real."""
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        cos = c.execute(
            text("SELECT co_equipe FROM public.tb_equipe ORDER BY co_seq")
        ).scalars().all()

    assert cos == [77, 88, 99]


def test_ficticio_preserva_comprimento_e_cabe_em_coluna_estreita(pg_engine):
    """Regressao preventiva: o erro que derrubou a migration 11.

    Gerar um comprimento fixo estoura qualquer coluna mais estreita que
    ele. Preservando a contagem de digitos do original, o valor cabe em
    qualquer coluna onde o original ja cabia.
    """
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        largo = c.execute(
            text("SELECT nu_ine FROM public.tb_equipe ORDER BY co_seq")
        ).scalars().first()
        estreito = c.execute(
            text(
                "SELECT nu_ine_executante, nu_ine_solicitante "
                "FROM public.tb_historico_dados_fcc"
            )
        ).first()

    assert len(largo) == 10
    assert len(estreito.nu_ine_executante) == 6
    assert len(estreito.nu_ine_solicitante) == 6
    assert estreito.nu_ine_executante != "123456"


def test_e_deterministico_entre_execucoes(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    with pg_engine.connect() as c:
        primeiro = c.execute(
            text("SELECT nu_ine FROM public.tb_equipe ORDER BY co_seq")
        ).scalars().first()

    esperado = m._fake_ine("0000123456")
    assert primeiro == esperado


def test_atomicidade_rollback_apos_escrita_parcial(pg_engine, monkeypatch):
    """Falha no meio do loop de UPDATE reverte inclusive o que ja passou.

    Forcando um valor ficticio de comprimento fixo, as tabelas largas sao
    atualizadas e `tb_historico_dados_fcc` (`varchar(6)`) estoura - a
    mesma classe de falha que derrubou a migration 11 no banco real.
    Aqui o que se verifica e a consequencia: as escritas anteriores nao
    sobrevivem.
    """
    _seed(pg_engine)

    monkeypatch.setattr(m, "_fake_ine", lambda value: "9999999999")

    with pytest.raises(DataError):
        m.run(pg_engine)

    with pg_engine.connect() as c:
        equipe = c.execute(
            text("SELECT nu_ine FROM public.tb_equipe ORDER BY co_seq")
        ).scalars().first()
        familia = c.execute(
            text("SELECT nu_ine FROM public.tb_familia ORDER BY co_seq")
        ).scalars().first()
        acomp = c.execute(
            text("SELECT nu_ine_vinc_equipe FROM public.tb_acomp_cidadaos_vinculados")
        ).scalar()

    assert equipe == "0000123456"
    assert familia == "0000123456"
    assert acomp == "0000123456"
