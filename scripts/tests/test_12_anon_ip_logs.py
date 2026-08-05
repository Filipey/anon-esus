"""Testes da migration 12 (logs de acesso/auditoria e IP)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("12_anon_ip_logs.py")


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_historico_acesso "
                "(co_seq_hist_acesso serial PRIMARY KEY, co_usuario bigint, "
                "dt_acesso timestamptz, co_ip text)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_envio_log "
                "(co_seq_envio_log serial PRIMARY KEY, data timestamptz, mensagem text)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_auditoria_evento "
                "(co_seq_auditoria_evento bigint PRIMARY KEY, dt_evento timestamptz, "
                "co_usuario bigint, ds_detalhes text)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_retificacao_atend "
                "(co_seq_retificacao_atend serial PRIMARY KEY, "
                "co_auditoria_evento_retificado bigint "
                "REFERENCES public.tb_auditoria_evento(co_seq_auditoria_evento))"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_historico_acesso (co_usuario, dt_acesso, co_ip) VALUES "
                "(1, '2024-01-01 10:00:00+00', '192.168.0.10')"
            )
        )
        c.execute(text("INSERT INTO public.tb_envio_log (data, mensagem) VALUES (now(), 'ok')"))
        c.execute(
            text(
                "INSERT INTO public.tb_auditoria_evento "
                "(co_seq_auditoria_evento, dt_evento, co_usuario, ds_detalhes) VALUES "
                "(1, '2024-01-01 10:00:00+00', 42, 'detalhe sensivel')"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_retificacao_atend (co_auditoria_evento_retificado) "
                "VALUES (1)"
            )
        )


def test_tabelas_de_log_sao_esvaziadas_por_completo(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        acesso = c.execute(text("SELECT count(*) FROM public.tb_historico_acesso")).scalar()
        envio = c.execute(text("SELECT count(*) FROM public.tb_envio_log")).scalar()

    assert acesso == 0
    assert envio == 0


def test_auditoria_evento_e_esvaziada_sem_apagar_a_linha(pg_engine):
    """Ha uma FK apontando pra essa tabela - a linha deve continuar
    existindo (so o conteudo eh zerado), senao quebraria a referencia."""
    _seed(pg_engine)
    m.run(pg_engine)

    with pg_engine.connect() as c:
        row = c.execute(
            text(
                "SELECT co_seq_auditoria_evento, dt_evento, co_usuario, ds_detalhes "
                "FROM public.tb_auditoria_evento"
            )
        ).one()
        ref = c.execute(
            text("SELECT co_auditoria_evento_retificado FROM public.tb_retificacao_atend")
        ).scalar()

    assert row.co_seq_auditoria_evento == 1  # PK preservada
    assert row.dt_evento is None
    assert row.co_usuario is None
    assert row.ds_detalhes is None
    assert ref == 1  # referencia da outra tabela continua valida


def test_tabela_com_fk_inesperada_e_pulada_nao_deletada(pg_engine, monkeypatch):
    """Se uma tabela do DELETE_TABLES tiver uma FK apontando pra ela
    (schema mudou), a migration deve pular em vez de tentar deletar."""
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_referencia_externa "
                "(co_seq serial PRIMARY KEY, co_envio_log bigint "
                "REFERENCES public.tb_envio_log(co_seq_envio_log))"
            )
        )
        c.execute(
            text("INSERT INTO public.tb_envio_log (co_seq_envio_log, data) VALUES (99, now())")
        )
        c.execute(text("INSERT INTO public.tb_referencia_externa (co_envio_log) VALUES (99)"))

    m.run(pg_engine)

    with pg_engine.connect() as c:
        count = c.execute(
            text("SELECT count(*) FROM public.tb_envio_log WHERE co_seq_envio_log = 99")
        ).scalar()
    assert count == 1  # nao foi deletada por causa da FK inesperada


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_poison "
                "(co_seq serial PRIMARY KEY, co_ip text)"
            )
        )
        c.execute(text("INSERT INTO public.tb_poison (co_ip) VALUES ('10.0.0.1')"))
        c.execute(
            text(
                "CREATE FUNCTION boom() RETURNS trigger AS "
                "$$ BEGIN RAISE EXCEPTION 'boom'; END $$ LANGUAGE plpgsql"
            )
        )
        c.execute(
            text(
                "CREATE TRIGGER trg_boom BEFORE DELETE ON public.tb_poison "
                "FOR EACH ROW EXECUTE FUNCTION boom()"
            )
        )

    monkeypatch.setattr(
        m,
        "DELETE_TABLES",
        list(m.DELETE_TABLES) + [m.LogTable("public", "tb_poison")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    with pg_engine.connect() as c:
        acesso = c.execute(text("SELECT count(*) FROM public.tb_historico_acesso")).scalar()
        poison = c.execute(text("SELECT co_ip FROM public.tb_poison")).scalar()
    assert acesso == 1  # nada foi excluido - rollback total
    assert poison == "10.0.0.1"
