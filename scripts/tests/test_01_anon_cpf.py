"""Testes da migration 01 (anonimização de CPFs).

Rodam contra a fixture `pg_engine` (Postgres efêmero). O orquestrador
executa este arquivo ANTES de aplicar a migration no banco real; só
aplica se tudo passar.
"""

from __future__ import annotations

import re

import pytest
from _helpers import load_migration
from cpf_generator import CPF
from sqlalchemy import text

m = load_migration("01_anon_cpf.py")

# CPFs reais (válidos) usados nas fixtures. O mesmo cidadão aparece em
# tabelas diferentes para exercitar o mapeamento determinístico.
CPF_A = "529.982.247-25"   # com pontuação
CPF_A_RAW = "52998224725"  # mesmo CPF, sem pontuação, em outra tabela
CPF_B = "11144477735"      # só dígitos
CPF_C = "01234567890"      # zero à esquerda

_DIGITS = re.compile(r"\D")


def _seed(engine):
    """Cria as tabelas-alvo da migration e popula com CPFs conhecidos."""
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq serial PRIMARY KEY, nu_cpf text, nu_cpf_responsavel text)"
            )
        )
        c.execute(
            text("CREATE TABLE public.tb_prof (co_seq serial PRIMARY KEY, nu_cpf text)")
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_atendimento_individual "
                "(co_seq serial PRIMARY KEY, nu_cpf_cidadao text)"
            )
        )
        # cidadão A (pontuado) + responsável B; cidadão C com zero à esquerda;
        # uma linha com CPF nulo (deve permanecer intacta).
        c.execute(
            text(
                "INSERT INTO public.tb_cidadao (nu_cpf, nu_cpf_responsavel) VALUES "
                "(:a, :b), (:c, NULL), (NULL, NULL)"
            ),
            {"a": CPF_A, "b": CPF_B, "c": CPF_C},
        )
        # profissional = mesmo cidadão A, mas sem pontuação.
        c.execute(
            text("INSERT INTO public.tb_prof (nu_cpf) VALUES (:a)"),
            {"a": CPF_A_RAW},
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_atendimento_individual "
                "(nu_cpf_cidadao) VALUES (:a)"
            ),
            {"a": CPF_A_RAW},
        )


def _all_values(engine):
    with engine.connect() as c:
        cidadao = c.execute(
            text("SELECT nu_cpf, nu_cpf_responsavel FROM public.tb_cidadao ORDER BY co_seq")
        ).all()
        prof = c.execute(text("SELECT nu_cpf FROM public.tb_prof")).scalar()
        fat = c.execute(
            text("SELECT nu_cpf_cidadao FROM public.tb_fat_atendimento_individual")
        ).scalar()
    return cidadao, prof, fat


def test_anonimiza_todos_os_cpfs(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, prof, fat = _all_values(pg_engine)

    originais = {CPF_A, CPF_A_RAW, CPF_B, CPF_C}
    presentes = {cidadao[0][0], cidadao[0][1], cidadao[1][0], prof, fat}
    assert presentes.isdisjoint(originais), "algum CPF original sobreviveu"


def test_todos_os_novos_sao_validos(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, prof, fat = _all_values(pg_engine)
    for valor in [cidadao[0][0], cidadao[0][1], cidadao[1][0], prof, fat]:
        assert CPF.validate(_DIGITS.sub("", valor)), f"CPF inválido gerado: {valor}"


def test_mapeamento_deterministico_entre_tabelas(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, prof, fat = _all_values(pg_engine)
    assert _DIGITS.sub("", cidadao[0][0]) == _DIGITS.sub("", prof)
    assert _DIGITS.sub("", cidadao[0][0]) == _DIGITS.sub("", fat)


def test_preserva_formato(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, _, _ = _all_values(pg_engine)
    assert "." in cidadao[0][0] and "-" in cidadao[0][0]
    assert len(cidadao[1][0]) == 11 and "." not in cidadao[1][0]


def test_nulls_permanecem_nulos(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    cidadao, _, _ = _all_values(pg_engine)
    assert cidadao[1][1] is None  # responsável da 2ª linha
    assert cidadao[2][0] is None and cidadao[2][1] is None  # 3ª linha toda nula


def test_recusa_rodar_se_coluna_de_login_estiver_em_cpf_columns(pg_engine, monkeypatch):
    """Guarda de seguranca: anonimizar tb_usuario.ds_login quebraria login
    de todos os profissionais (ds_login = CPF, confirmado no schema real)."""
    monkeypatch.setattr(
        m,
        "CPF_COLUMNS",
        list(m.CPF_COLUMNS) + [m.CpfColumn("public", "tb_usuario", "ds_login")],
    )

    with pytest.raises(RuntimeError, match="PRESERVE_FOR_LOGIN"):
        m.run(pg_engine)


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    """Se uma coluna-alvo falhar no meio, NADA é alterado (rollback)."""
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text("CREATE TABLE public.tb_poison (co_seq serial PRIMARY KEY, nu_cpf text)")
        )
        c.execute(
            text("INSERT INTO public.tb_poison (nu_cpf) VALUES (:a)"), {"a": CPF_A_RAW}
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
        "CPF_COLUMNS",
        list(m.CPF_COLUMNS) + [m.CpfColumn("public", "tb_poison", "nu_cpf")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    # Banco deve estar idêntico ao estado inicial.
    cidadao, prof, fat = _all_values(pg_engine)
    assert cidadao[0][0] == CPF_A
    assert cidadao[0][1] == CPF_B
    assert cidadao[1][0] == CPF_C
    assert prof == CPF_A_RAW
    assert fat == CPF_A_RAW
