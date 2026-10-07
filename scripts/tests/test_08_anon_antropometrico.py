"""Testes da migration 08 (antropometria: corte de extremos + microagregação)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("08_anon_antropometrico.py")


def _seed_medicao(engine, medidas):
    """medidas: lista de (pessoa, peso, altura, imc) em texto, como no PEC."""
    with engine.begin() as c:
        c.execute(text("CREATE TABLE public.tb_prontuario (co_seq_prontuario serial PRIMARY KEY, co_cidadao int)"))
        c.execute(text("CREATE TABLE public.tb_atend (co_seq_atend serial PRIMARY KEY, co_prontuario int)"))
        c.execute(text("CREATE TABLE public.tb_atend_prof (co_seq_atend_prof serial PRIMARY KEY, co_atend int)"))
        c.execute(text(
            "CREATE TABLE public.tb_medicao (co_seq_medicao serial PRIMARY KEY, co_atend_prof int, "
            "nu_medicao_peso varchar(10), nu_medicao_altura varchar(10), nu_medicao_imc varchar(10))"
        ))
        for pessoa, peso, altura, imc in medidas:
            pr = c.execute(text("INSERT INTO public.tb_prontuario (co_cidadao) VALUES (:p) RETURNING 1"),
                           {"p": pessoa})
            pr = c.execute(text("SELECT max(co_seq_prontuario) FROM public.tb_prontuario")).scalar()
            at = c.execute(text("INSERT INTO public.tb_atend (co_prontuario) VALUES (:p) RETURNING co_seq_atend"),
                           {"p": pr}).scalar()
            ap = c.execute(text("INSERT INTO public.tb_atend_prof (co_atend) VALUES (:a) RETURNING co_seq_atend_prof"),
                           {"a": at}).scalar()
            c.execute(text("INSERT INTO public.tb_medicao (co_atend_prof, nu_medicao_peso, nu_medicao_altura, "
                           "nu_medicao_imc) VALUES (:ap, :pe, :al, :imc)"),
                      {"ap": ap, "pe": peso, "al": altura, "imc": imc})


def _medidas(n=40):
    # 40 pessoas, pesos de 50 a 89 kg, alturas de 150 a 189 cm, mais um erro de digitação
    out = [(i, f"{50 + i}.0", f"{150 + i}", "99.9") for i in range(n)]
    out.append((999, "500.0", "170", "2721.1"))
    return out


def _pesos(engine, tabela="tb_medicao", col="nu_medicao_peso"):
    with engine.connect() as c:
        return c.execute(text(f"SELECT {col} FROM public.{tabela} ORDER BY 1")).scalars().all()


def test_cada_valor_publicado_e_compartilhado_por_k_pessoas(pg_engine):
    _seed_medicao(pg_engine, _medidas())
    m.run(pg_engine)
    with pg_engine.connect() as c:
        por_valor = c.execute(text(
            "SELECT m.nu_medicao_peso, count(DISTINCT p.co_cidadao) FROM public.tb_medicao m "
            "JOIN public.tb_atend_prof ap ON ap.co_seq_atend_prof = m.co_atend_prof "
            "JOIN public.tb_atend a ON a.co_seq_atend = ap.co_atend "
            "JOIN public.tb_prontuario p ON p.co_seq_prontuario = a.co_prontuario GROUP BY 1"
        )).all()
    assert all(n >= m.K for _, n in por_valor)
    assert len(por_valor) > 1  # não colapsou tudo num valor só


def test_erro_de_digitacao_some_no_bloco_da_ponta(pg_engine):
    _seed_medicao(pg_engine, _medidas())
    m.run(pg_engine)
    pesos = [float(p) for p in _pesos(pg_engine)]
    assert max(pesos) < 100  # o 500 kg virou a média do último bloco


def test_imc_recalculado_do_peso_e_altura_publicados(pg_engine):
    _seed_medicao(pg_engine, _medidas())
    m.run(pg_engine)
    with pg_engine.connect() as c:
        linhas = c.execute(text("SELECT nu_medicao_peso, nu_medicao_altura, nu_medicao_imc "
                                "FROM public.tb_medicao")).all()
    for peso, altura, imc in linhas:
        assert float(imc) == pytest.approx(float(peso) / (float(altura) / 100) ** 2, abs=0.01)


def test_mesmo_valor_vira_o_mesmo_publicado_no_dw(pg_engine):
    _seed_medicao(pg_engine, _medidas())
    with pg_engine.begin() as c:
        c.execute(text("CREATE TABLE public.tb_fat_visita_domiciliar (co_seq serial PRIMARY KEY, "
                       "nu_peso double precision, nu_altura double precision)"))
        c.execute(text("INSERT INTO public.tb_fat_visita_domiciliar (nu_peso, nu_altura) VALUES (62, 160), (300, NULL)"))
    with pg_engine.connect() as c:
        id_62 = c.execute(text("SELECT co_seq_medicao FROM public.tb_medicao WHERE nu_medicao_peso = '62.0'")).scalar()
    m.run(pg_engine)
    with pg_engine.connect() as c:
        no_medicao = c.execute(text("SELECT nu_medicao_peso FROM public.tb_medicao WHERE co_seq_medicao = :i"),
                               {"i": id_62}).scalar()
        dw = c.execute(text("SELECT nu_peso FROM public.tb_fat_visita_domiciliar ORDER BY co_seq")).scalars().all()
    assert float(no_medicao) == pytest.approx(dw[0])
    assert dw[1] < 100  # valor só do DW cai na faixa que o contém


def test_valor_que_nao_e_numero_vira_nulo(pg_engine):
    _seed_medicao(pg_engine, _medidas() + [(500, "abc", None, None)])
    m.run(pg_engine)
    assert None in _pesos(pg_engine)
    assert "abc" not in _pesos(pg_engine)


def test_sem_tb_medicao_usa_o_dw(pg_engine):
    with pg_engine.begin() as c:
        c.execute(text("CREATE TABLE public.tb_fat_atendimento_individual (co_seq serial PRIMARY KEY, "
                       "nu_peso double precision, nu_perim_panturrilha numeric(3,1))"))
        c.execute(text("INSERT INTO public.tb_fat_atendimento_individual (nu_peso, nu_perim_panturrilha) "
                       "SELECT 40 + g, 30 + (g % 10) FROM generate_series(1, 30) g"))
    m.run(pg_engine)
    with pg_engine.connect() as c:
        n = c.execute(text("SELECT count(DISTINCT nu_peso) FROM public.tb_fat_atendimento_individual")).scalar()
    assert 1 < n <= 30 // m.K


def test_banco_vazio_nao_falha(pg_engine):
    m.run(pg_engine)


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed_medicao(pg_engine, _medidas())
    antes = _pesos(pg_engine)
    with pg_engine.begin() as c:
        c.execute(text("CREATE TABLE public.tb_poison (co_seq serial PRIMARY KEY, nu_peso numeric)"))
        c.execute(text("INSERT INTO public.tb_poison (nu_peso) VALUES (70)"))
        c.execute(text("CREATE FUNCTION boom() RETURNS trigger AS "
                       "$$ BEGIN RAISE EXCEPTION 'boom'; END $$ LANGUAGE plpgsql"))
        c.execute(text("CREATE TRIGGER trg BEFORE UPDATE ON public.tb_poison FOR EACH ROW EXECUTE FUNCTION boom()"))
    monkeypatch.setattr(m, "ANTHRO_COLUMNS", m.ANTHRO_COLUMNS + [m.AnthroColumn("public", "tb_poison", "nu_peso", "peso")])
    with pytest.raises(Exception):
        m.run(pg_engine)
    assert _pesos(pg_engine) == antes
