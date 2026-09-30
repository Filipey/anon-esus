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


def _seed_cidadao(engine):
    """Tabela mestra do cidadão com colunas de busca, como no PEC."""
    with engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao (co_seq serial PRIMARY KEY, no_cidadao text, "
                "no_social text, no_mae text, no_pai text, no_cidadao_filtro text, no_mae_filtro text)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_cidadao (no_cidadao, no_social, no_mae, no_pai, "
                "no_cidadao_filtro, no_mae_filtro) VALUES "
                "('JOSÉ AÇAÍ', NULL, 'Maria da Silva', NULL, 'jose acai', 'maria da silva'), "
                "('Ana Souza', 'Beto', NULL, NULL, 'beto ana souza', NULL)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_cds_cad_individual (co_seq serial PRIMARY KEY, "
                "no_cidadao text, no_social_cidadao text, no_mae_cidadao text, no_cidadao_filtro text)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_cds_cad_individual (no_cidadao, no_social_cidadao, "
                "no_mae_cidadao, no_cidadao_filtro) VALUES ('José Açaí', NULL, 'MARIA DA SILVA', 'jose acai')"
            )
        )


def test_tabela_mestra_do_cidadao_e_coberta(pg_engine):
    _seed_cidadao(pg_engine)
    m.run(pg_engine)
    with pg_engine.connect() as c:
        rows = c.execute(
            text("SELECT no_cidadao, no_social, no_mae, no_cidadao_filtro, no_mae_filtro "
                 "FROM public.tb_cidadao ORDER BY co_seq")
        ).all()
    reais = {"JOSÉ AÇAÍ", "Ana Souza", "Beto", "Maria da Silva", "jose acai", "maria da silva",
             "beto ana souza"}
    for row in rows:
        assert not (set(filter(None, row)) & reais), "nome real sobreviveu"


def test_mesma_pessoa_com_grafias_diferentes_recebe_o_mesmo_ficticio(pg_engine):
    _seed_cidadao(pg_engine)
    m.run(pg_engine)
    with pg_engine.connect() as c:
        mestre = c.execute(text("SELECT no_cidadao, no_mae FROM public.tb_cidadao ORDER BY co_seq")).first()
        cad = c.execute(text("SELECT no_cidadao, no_mae_cidadao FROM public.tb_cds_cad_individual")).one()
    assert m.normalizar(mestre.no_cidadao) == m.normalizar(cad.no_cidadao)
    assert m.normalizar(mestre.no_mae) == m.normalizar(cad.no_mae_cidadao)
    # e preserva o estilo de caixa de cada original
    assert mestre.no_cidadao == mestre.no_cidadao.upper()
    assert cad.no_mae_cidadao == cad.no_mae_cidadao.upper()
    assert cad.no_cidadao != cad.no_cidadao.upper()


def test_colunas_de_busca_recalculadas_a_partir_do_ficticio(pg_engine):
    _seed_cidadao(pg_engine)
    m.run(pg_engine)
    with pg_engine.connect() as c:
        rows = c.execute(
            text("SELECT no_cidadao, no_social, no_mae, no_cidadao_filtro, no_mae_filtro "
                 "FROM public.tb_cidadao ORDER BY co_seq")
        ).all()
        cad = c.execute(text("SELECT no_cidadao, no_cidadao_filtro FROM public.tb_cds_cad_individual")).one()
    jose, ana = rows
    assert jose.no_cidadao_filtro == m.normalizar(jose.no_cidadao)
    assert jose.no_mae_filtro == m.normalizar(jose.no_mae)
    assert ana.no_cidadao_filtro == m.normalizar(f"{ana.no_social} {ana.no_cidadao}")
    assert ana.no_mae_filtro is None  # sem mãe, a busca continua nula
    assert cad.no_cidadao_filtro == m.normalizar(cad.no_cidadao)


def test_mapa_reprodutivel_e_independente_da_ordem():
    nomes = {"JOSÉ AÇAÍ", "José Açaí", "Maria", " maria  ", ""}
    a = m.build_name_map(nomes)
    b = m.build_name_map(set(sorted(nomes, reverse=True)))
    assert a == b
    assert "" not in a
    assert m.normalizar(a["JOSÉ AÇAÍ"]) == m.normalizar(a["José Açaí"])
    assert m.normalizar(a["Maria"]) == m.normalizar(a[" maria  "])
