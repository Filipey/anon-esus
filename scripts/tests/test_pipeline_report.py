"""Testes do relatorio de auditoria (scripts/pipeline_report.py).

Roda contra a fixture `pg_engine` (Postgres efemero). Como
`_column_targets()`/`_table_targets()` leem a lista real declarada nas
migrations (nao sao injetaveis), os testes criam no banco efemero
exatamente as tabelas/colunas reais que essas listas apontam (ex.:
`public.tb_cidadao.nu_cpf`, que `01_anon_cpf.py` declara de verdade).
"""

from __future__ import annotations

from pathlib import Path

from _helpers import load_migration
from sqlalchemy import text

m = load_migration("pipeline_report.py")


def _seed_cpf_table(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(text("CREATE TABLE public.tb_cidadao (co_seq serial PRIMARY KEY, nu_cpf text)"))
        c.execute(text("INSERT INTO public.tb_cidadao (nu_cpf) VALUES ('52998224725'), (NULL)"))


def test_snapshot_de_coluna_existente(pg_engine):
    _seed_cpf_table(pg_engine)
    target = m.ColumnTarget("01_anon_cpf", "public", "tb_cidadao", "nu_cpf")
    with pg_engine.connect() as conn:
        snap = m._snapshot_column(conn, target)

    assert snap.exists
    assert snap.total_rows == 2
    assert snap.non_null == 1
    assert snap.checksum != "0"


def test_snapshot_de_coluna_inexistente_nao_quebra(pg_engine):
    with pg_engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
    target = m.ColumnTarget("01_anon_cpf", "public", "tb_nao_existe", "nu_cpf")
    with pg_engine.connect() as conn:
        snap = m._snapshot_column(conn, target)

    assert not snap.exists
    assert snap.total_rows == 0


def test_diff_detecta_mudanca_de_conteudo_via_checksum(pg_engine):
    _seed_cpf_table(pg_engine)
    target = m.ColumnTarget("01_anon_cpf", "public", "tb_cidadao", "nu_cpf")

    with pg_engine.connect() as conn:
        before = m._snapshot_column(conn, target)

    with pg_engine.begin() as c:
        c.execute(text("UPDATE public.tb_cidadao SET nu_cpf = '11144477735' WHERE nu_cpf IS NOT NULL"))

    with pg_engine.connect() as conn:
        after = m._snapshot_column(conn, target)

    diff = m._column_diff(before, after)
    assert diff["conteudo_mudou"] is True
    assert diff["nao_nulos_antes"] == diff["nao_nulos_depois"] == 1


def test_diff_nao_acusa_mudanca_quando_nada_muda(pg_engine):
    _seed_cpf_table(pg_engine)
    target = m.ColumnTarget("01_anon_cpf", "public", "tb_cidadao", "nu_cpf")

    with pg_engine.connect() as conn:
        before = m._snapshot_column(conn, target)
        after = m._snapshot_column(conn, target)

    diff = m._column_diff(before, after)
    assert diff["conteudo_mudou"] is False


def test_snapshot_de_tabela_detecta_linhas_removidas(pg_engine):
    with pg_engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(text("CREATE TABLE public.tb_envio_log (co_seq serial PRIMARY KEY, data text)"))
        c.execute(text("INSERT INTO public.tb_envio_log (data) VALUES ('a'), ('b'), ('c')"))

    target = m.TableTarget("12_anon_ip_logs", "public", "tb_envio_log", "delete")
    with pg_engine.connect() as conn:
        before = m._snapshot_table(conn, target)

    with pg_engine.begin() as c:
        c.execute(text("DELETE FROM public.tb_envio_log WHERE data <> 'a'"))

    with pg_engine.connect() as conn:
        after = m._snapshot_table(conn, target)

    diff = m._table_diff(before, after)
    assert diff["linhas_antes"] == 3
    assert diff["linhas_depois"] == 1
    assert diff["linhas_removidas"] == 2


def test_build_report_agrupa_por_migration_e_resume(pg_engine):
    _seed_cpf_table(pg_engine)
    target = m.ColumnTarget("01_anon_cpf", "public", "tb_cidadao", "nu_cpf")

    with pg_engine.connect() as conn:
        before_snap = m._snapshot_column(conn, target)

    with pg_engine.begin() as c:
        c.execute(text("UPDATE public.tb_cidadao SET nu_cpf = '11144477735' WHERE nu_cpf IS NOT NULL"))

    with pg_engine.connect() as conn:
        after_snap = m._snapshot_column(conn, target)

    from datetime import datetime, timezone

    before = {"columns": [before_snap], "tables": []}
    after = {"columns": [after_snap], "tables": []}
    now = datetime.now(timezone.utc)
    report = m.build_report(before, after, now, now)

    assert "01_anon_cpf" in report["resumo_por_migration"]
    assert report["resumo_por_migration"]["01_anon_cpf"]["colunas_com_conteudo_alterado"] == 1
    assert report["resumo_por_migration"]["01_anon_cpf"]["colunas_declaradas"] == 1


def test_write_report_grava_json_legivel(tmp_path: Path):
    report = {
        "iniciado_em": "2026-01-01T00:00:00+00:00",
        "concluido_em": "2026-01-01T00:01:00+00:00",
        "resumo_por_migration": {"01_anon_cpf": {"colunas_declaradas": 1}},
        "detalhe_por_migration": {},
    }
    path = tmp_path / "relatorio.json"
    m.write_report(report, path)

    import json

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["resumo_por_migration"]["01_anon_cpf"]["colunas_declaradas"] == 1
