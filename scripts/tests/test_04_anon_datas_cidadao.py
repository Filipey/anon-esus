"""Testes da migration 04 (datas de nascimento e registros)."""

from __future__ import annotations

import hashlib
from datetime import date, datetime

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("04_anon_datas_cidadao.py")

CPF_A = "52998224725"
CPF_B = "11144477735"


def _seed(engine):
    with engine.begin() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_atendimento_individual "
                "("
                "co_seq serial PRIMARY KEY, "
                "nu_cpf_cidadao text, "
                "dt_nascimento date, "
                "dt_inicial_atendimento timestamp, "
                "dt_final_atendimento timestamp"
                ")"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_atendimento_individual "
                "(nu_cpf_cidadao, dt_nascimento, dt_inicial_atendimento, dt_final_atendimento) "
                "VALUES "
                "(:cpf_a, '1980-05-10', '2020-01-20 08:30:00', '2020-01-20 09:00:00'), "
                "(:cpf_a, '1980-05-10', '2020-02-01 10:00:00', '2020-02-01 10:30:00'), "
                "(:cpf_b, '2000-02-29', '2020-03-10 12:00:00', '2020-03-10 12:30:00'), "
                "(NULL, '1990-07-15', '2020-04-01 12:00:00', '2020-04-01 12:30:00')"
            ),
            {"cpf_a": CPF_A, "cpf_b": CPF_B},
        )


def _rows(engine):
    with engine.connect() as c:
        return c.execute(
            text(
                "SELECT nu_cpf_cidadao, dt_nascimento, dt_inicial_atendimento, "
                "dt_final_atendimento "
                "FROM public.tb_fat_atendimento_individual ORDER BY co_seq"
            )
        ).all()


def test_preserva_mes_ano_e_muda_apenas_dia(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    assert rows[0].dt_nascimento.year == 1980
    assert rows[0].dt_nascimento.month == 5
    assert rows[0].dt_nascimento != date(1980, 5, 10)
    assert 1 <= rows[2].dt_nascimento.day <= 29
    assert rows[3].dt_nascimento == date(1990, 7, 15)


def test_mesmo_cidadao_recebe_mesmo_deslocamento(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    first_delta = rows[0].dt_nascimento - date(1980, 5, 10)
    second_delta = rows[1].dt_nascimento - date(1980, 5, 10)
    assert first_delta == second_delta


def test_preserva_intervalo_entre_nascimento_e_atendimento(pg_engine):
    _seed(pg_engine)
    m.run(pg_engine)
    rows = _rows(pg_engine)

    old_birth = date(1980, 5, 10)
    old_start = datetime(2020, 1, 20, 8, 30)
    old_interval = old_start.date() - old_birth
    new_interval = rows[0].dt_inicial_atendimento.date() - rows[0].dt_nascimento
    assert new_interval == old_interval
    assert rows[0].dt_final_atendimento - rows[0].dt_inicial_atendimento == (
        datetime(2020, 1, 20, 9, 0) - old_start
    )


def _seed_dim_tempo(engine):
    """Cria tb_dim_tempo (calendario) e tb_fat_visita_domiciliar, cuja data
    do evento so existe via FK co_dim_tempo, sem coluna de data literal."""
    with engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_dim_tempo "
                "(co_seq_dim_tempo bigint PRIMARY KEY, dt_registro date)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_dim_tempo (co_seq_dim_tempo, dt_registro) "
                "SELECT (d::date - DATE '2019-01-01') + 1, d::date "
                "FROM generate_series(DATE '2019-01-01', DATE '2021-12-31', interval '1 day') AS d"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_visita_domiciliar "
                "(co_seq_fat_visita_domiciliar serial PRIMARY KEY, "
                "nu_cpf_cidadao text, dt_nascimento date, co_dim_tempo bigint)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_fat_visita_domiciliar "
                "(nu_cpf_cidadao, dt_nascimento, co_dim_tempo) VALUES "
                "(:cpf_a, '1990-05-10', (SELECT co_seq_dim_tempo FROM public.tb_dim_tempo "
                " WHERE dt_registro = '2020-06-01')), "
                "(:cpf_a, '1990-05-10', (SELECT co_seq_dim_tempo FROM public.tb_dim_tempo "
                " WHERE dt_registro = '2020-07-01')), "
                # visita a poucos dias do nascimento: caso sensivel a ficar negativo
                "(:cpf_b, '2020-05-15', (SELECT co_seq_dim_tempo FROM public.tb_dim_tempo "
                " WHERE dt_registro = '2020-05-20'))"
            ),
            {"cpf_a": CPF_A, "cpf_b": CPF_B},
        )


def _rows_visita_domiciliar(engine):
    with engine.connect() as c:
        return c.execute(
            text(
                "SELECT t.co_seq_fat_visita_domiciliar, t.nu_cpf_cidadao, t.dt_nascimento, "
                "dt.dt_registro AS data_visita "
                "FROM public.tb_fat_visita_domiciliar t "
                "JOIN public.tb_dim_tempo dt ON dt.co_seq_dim_tempo = t.co_dim_tempo "
                "ORDER BY t.co_seq_fat_visita_domiciliar"
            )
        ).all()


def test_dim_tempo_preserva_intervalo_nascimento_evento(pg_engine):
    """co_dim_tempo precisa ser reapontado junto com o nascimento, senao o
    intervalo entre nascimento e evento muda (podendo ficar negativo)."""
    _seed_dim_tempo(pg_engine)
    antes = {r.co_seq_fat_visita_domiciliar: r.data_visita - r.dt_nascimento for r in _rows_visita_domiciliar(pg_engine)}

    m.run(pg_engine)

    depois = _rows_visita_domiciliar(pg_engine)
    for row in depois:
        assert row.data_visita - row.dt_nascimento == antes[row.co_seq_fat_visita_domiciliar]
    # o caso sensivel (5 dias de vida) continua positivo, nunca negativo
    assert (depois[2].data_visita - depois[2].dt_nascimento).days >= 0


def test_dim_tempo_mesmo_cidadao_mesmo_deslocamento(pg_engine):
    _seed_dim_tempo(pg_engine)
    m.run(pg_engine)
    rows = _rows_visita_domiciliar(pg_engine)

    assert rows[0].dt_nascimento == rows[1].dt_nascimento
    first_delta = rows[0].data_visita - date(2020, 6, 1)
    second_delta = rows[1].data_visita - date(2020, 7, 1)
    assert first_delta == second_delta


def _seed_joined_date(engine):
    """tb_atend/tb_atend_prof: data literal, mas CPF/nascimento so acessivel
    via join ate tb_cidadao (tb_atend -> tb_prontuario -> tb_cidadao)."""
    with engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq_cidadao serial PRIMARY KEY, nu_cpf text, dt_nascimento date)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_prontuario "
                "(co_seq_prontuario serial PRIMARY KEY, co_cidadao bigint, "
                "co_prontuario_grupo bigint)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_atend "
                "(co_seq_atend serial PRIMARY KEY, co_prontuario bigint, "
                "dt_inicio timestamp, dt_fim timestamp)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_atend_prof "
                "(co_seq_atend_prof serial PRIMARY KEY, co_atend bigint, "
                "dt_inicio timestamp, dt_fim timestamp)"
            )
        )
        cidadao_id = c.execute(
            text(
                "INSERT INTO public.tb_cidadao (nu_cpf, dt_nascimento) "
                "VALUES (:cpf, '1990-05-10') RETURNING co_seq_cidadao"
            ),
            {"cpf": CPF_A},
        ).scalar_one()
        prontuario_id = c.execute(
            text("INSERT INTO public.tb_prontuario (co_cidadao) VALUES (:c) RETURNING co_seq_prontuario"),
            {"c": cidadao_id},
        ).scalar_one()
        # consulta 25 dias depois do nascimento: caso sensivel, perto da
        # borda que o bug original (datas nunca deslocadas) quebraria.
        atend_id = c.execute(
            text(
                "INSERT INTO public.tb_atend (co_prontuario, dt_inicio, dt_fim) "
                "VALUES (:p, '1990-06-04 10:00:00', '1990-06-04 10:30:00') "
                "RETURNING co_seq_atend"
            ),
            {"p": prontuario_id},
        ).scalar_one()
        c.execute(
            text(
                "INSERT INTO public.tb_atend_prof (co_atend, dt_inicio, dt_fim) "
                "VALUES (:a, '1990-06-04 10:00:00', '1990-06-04 10:30:00')"
            ),
            {"a": atend_id},
        )


def _rows_joined_date(engine):
    with engine.connect() as c:
        nascimento = c.execute(text("SELECT dt_nascimento FROM public.tb_cidadao")).scalar_one()
        atend = c.execute(text("SELECT dt_inicio FROM public.tb_atend")).scalar_one()
        atend_prof = c.execute(text("SELECT dt_inicio FROM public.tb_atend_prof")).scalar_one()
    return nascimento, atend, atend_prof


def test_joined_date_preserva_intervalo_nascimento_atendimento(pg_engine):
    """tb_atend/tb_atend_prof nao tem CPF/nascimento na propria linha; sem a
    correcao, a data do atendimento nunca seria deslocada e o intervalo com
    o nascimento (ja deslocado) mudaria."""
    _seed_joined_date(pg_engine)
    _, atend_antes, _ = _rows_joined_date(pg_engine)
    intervalo_antes = (atend_antes.date() - date(1990, 5, 10)).days

    m.run(pg_engine)

    nascimento_depois, atend_depois, atend_prof_depois = _rows_joined_date(pg_engine)
    intervalo_depois = (atend_depois.date() - nascimento_depois).days
    assert intervalo_depois == intervalo_antes
    assert atend_depois == atend_prof_depois


def test_atomicidade_rollback_em_falha(pg_engine, monkeypatch):
    _seed(pg_engine)

    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_poison "
                "(co_seq serial PRIMARY KEY, nu_cpf_cidadao text, dt_nascimento date)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_poison (nu_cpf_cidadao, dt_nascimento) "
                "VALUES (:cpf, '1980-05-10')"
            ),
            {"cpf": CPF_A},
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
        "DATE_TABLES",
        list(m.DATE_TABLES)
        + [m.DateTable("public", "tb_poison", "dt_nascimento", "nu_cpf_cidadao")],
    )

    with pytest.raises(Exception):
        m.run(pg_engine)

    rows = _rows(pg_engine)
    assert rows[0].dt_nascimento == date(1980, 5, 10)
    assert rows[0].dt_inicial_atendimento == datetime(2020, 1, 20, 8, 30)


def _nova_data_esperada(seed_source: str, nascimento_antigo: date) -> date:
    """Reproduz em Python a mesma formula SQL de _build_new_birth_expr, pra
    comparar com um valor exato (nao so mes/ano) sem depender do
    comportamento de um CPF especifico escolhido a dedo."""
    month_start = nascimento_antigo.replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    days_in_month = (next_month - month_start).days
    seed = int(hashlib.md5(seed_source.encode()).hexdigest()[:8], 16)
    offset = seed % days_in_month
    return date(month_start.year, month_start.month, 1 + offset)


def _seed_atend_prof_family(engine, cpf=CPF_A, nascimento="1988-03-12"):
    """Monta a cadeia tb_cidadao -> tb_prontuario -> tb_atend -> tb_atend_prof
    e uma tabela generica (fora de DATE_TABLES) ligada so por co_atend_prof,
    igual tb_problema_evolucao/tb_medicao na base real."""
    with engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq_cidadao serial PRIMARY KEY, nu_cpf text, dt_nascimento date)"
            )
        )
        c.execute(text("CREATE TABLE public.tb_prontuario (co_seq_prontuario serial PRIMARY KEY, co_cidadao bigint)"))
        c.execute(text("CREATE TABLE public.tb_atend (co_seq_atend serial PRIMARY KEY, co_prontuario bigint)"))
        c.execute(text("CREATE TABLE public.tb_atend_prof (co_seq_atend_prof serial PRIMARY KEY, co_atend bigint)"))
        c.execute(
            text(
                "CREATE TABLE public.tb_problema_evolucao "
                "(co_seq_problema_evolucao serial PRIMARY KEY, co_atend_prof bigint, "
                "dt_inicio_problema date, dt_auditoria timestamp)"
            )
        )
        cidadao_id = c.execute(
            text("INSERT INTO public.tb_cidadao (nu_cpf, dt_nascimento) VALUES (:cpf, :n) RETURNING co_seq_cidadao"),
            {"cpf": cpf, "n": nascimento},
        ).scalar_one()
        prontuario_id = c.execute(
            text("INSERT INTO public.tb_prontuario (co_cidadao) VALUES (:c) RETURNING co_seq_prontuario"),
            {"c": cidadao_id},
        ).scalar_one()
        atend_id = c.execute(
            text("INSERT INTO public.tb_atend (co_prontuario) VALUES (:p) RETURNING co_seq_atend"),
            {"p": prontuario_id},
        ).scalar_one()
        atend_prof_id = c.execute(
            text("INSERT INTO public.tb_atend_prof (co_atend) VALUES (:a) RETURNING co_seq_atend_prof"),
            {"a": atend_id},
        ).scalar_one()
        c.execute(
            text(
                "INSERT INTO public.tb_problema_evolucao (co_atend_prof, dt_inicio_problema, dt_auditoria) "
                "VALUES (:ap, '1988-04-02', '2024-01-01 00:00:00')"
            ),
            {"ap": atend_prof_id},
        )
    return cidadao_id


def test_atend_prof_family_desloca_tabela_fora_de_date_tables(pg_engine):
    """tb_problema_evolucao (e qualquer outra tabela com co_atend_prof que
    nao esteja explicitamente listada) deve ser descoberta e deslocada pela
    familia generica, preservando o intervalo com o nascimento. dt_auditoria
    e metadado e nao deve ser tocado."""
    _seed_atend_prof_family(pg_engine)

    m.run(pg_engine)

    with pg_engine.connect() as c:
        row = c.execute(
            text("SELECT dt_inicio_problema, dt_auditoria FROM public.tb_problema_evolucao")
        ).one()
        nascimento = c.execute(text("SELECT dt_nascimento FROM public.tb_cidadao")).scalar_one()

    intervalo_antigo = (date(1988, 4, 2) - date(1988, 3, 12)).days
    assert (row.dt_inicio_problema - nascimento).days == intervalo_antigo
    assert row.dt_auditoria == datetime(2024, 1, 1, 0, 0)


def test_prontuario_family_desloca_tabela_fora_de_date_tables(pg_engine):
    """Tabela ligada so por co_prontuario (sem co_atend_prof), igual
    tb_exame_requisitado/tb_pre_natal na base real."""
    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq_cidadao serial PRIMARY KEY, nu_cpf text, dt_nascimento date)"
            )
        )
        c.execute(text("CREATE TABLE public.tb_prontuario (co_seq_prontuario serial PRIMARY KEY, co_cidadao bigint)"))
        c.execute(
            text(
                "CREATE TABLE public.tb_exame_requisitado "
                "(co_seq_exame_requisitado serial PRIMARY KEY, co_prontuario bigint, dt_solicitacao date)"
            )
        )
        cidadao_id = c.execute(
            text(
                "INSERT INTO public.tb_cidadao (nu_cpf, dt_nascimento) "
                "VALUES (:cpf, '1975-11-20') RETURNING co_seq_cidadao"
            ),
            {"cpf": CPF_A},
        ).scalar_one()
        prontuario_id = c.execute(
            text("INSERT INTO public.tb_prontuario (co_cidadao) VALUES (:c) RETURNING co_seq_prontuario"),
            {"c": cidadao_id},
        ).scalar_one()
        c.execute(
            text(
                "INSERT INTO public.tb_exame_requisitado (co_prontuario, dt_solicitacao) "
                "VALUES (:p, '1975-12-05')"
            ),
            {"p": prontuario_id},
        )

    m.run(pg_engine)

    with pg_engine.connect() as c:
        dt_solicitacao = c.execute(text("SELECT dt_solicitacao FROM public.tb_exame_requisitado")).scalar_one()
        nascimento = c.execute(text("SELECT dt_nascimento FROM public.tb_cidadao")).scalar_one()
    assert (dt_solicitacao - nascimento).days == (date(1975, 12, 5) - date(1975, 11, 20)).days


def test_fat_cidadao_pec_family_desloca_tabela_fora_de_date_tables(pg_engine):
    """Tabela ligada so por co_fat_cidadao_pec direto (sem co_atend_prof nem
    co_prontuario), igual tb_fat_rel_op_crianca/tb_fat_ivcf na base real."""
    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq_cidadao serial PRIMARY KEY, nu_cpf text, dt_nascimento date)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_cidadao_pec "
                "(co_seq_fat_cidadao_pec serial PRIMARY KEY, co_cidadao bigint)"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_fat_rel_op_crianca "
                "(co_seq_fat_rel_op_crianca serial PRIMARY KEY, co_fat_cidadao_pec bigint, "
                "dt_1_consulta_puericultura date)"
            )
        )
        cidadao_id = c.execute(
            text(
                "INSERT INTO public.tb_cidadao (nu_cpf, dt_nascimento) "
                "VALUES (:cpf, '2019-06-14') RETURNING co_seq_cidadao"
            ),
            {"cpf": CPF_A},
        ).scalar_one()
        fcp_id = c.execute(
            text("INSERT INTO public.tb_fat_cidadao_pec (co_cidadao) VALUES (:c) RETURNING co_seq_fat_cidadao_pec"),
            {"c": cidadao_id},
        ).scalar_one()
        c.execute(
            text(
                "INSERT INTO public.tb_fat_rel_op_crianca (co_fat_cidadao_pec, dt_1_consulta_puericultura) "
                "VALUES (:fcp, '2019-07-15')"
            ),
            {"fcp": fcp_id},
        )

    m.run(pg_engine)

    with pg_engine.connect() as c:
        dt_consulta = c.execute(
            text("SELECT dt_1_consulta_puericultura FROM public.tb_fat_rel_op_crianca")
        ).scalar_one()
        nascimento = c.execute(text("SELECT dt_nascimento FROM public.tb_cidadao")).scalar_one()
    assert (dt_consulta - nascimento).days == (date(2019, 7, 15) - date(2019, 6, 14)).days


def test_cpf_nulo_usa_co_seq_cidadao_como_semente(pg_engine):
    """Cidadao sem CPF nao pode ficar sem nenhum deslocamento: a formula
    precisa cair pra um identificador que sempre existe (co_seq_cidadao),
    senao esse cidadao (e tudo ligado a ele) nunca e anonimizado."""
    with pg_engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao "
                "(co_seq_cidadao serial PRIMARY KEY, nu_cpf text, dt_nascimento date)"
            )
        )
        cidadao_id = c.execute(
            text(
                "INSERT INTO public.tb_cidadao (nu_cpf, dt_nascimento) "
                "VALUES (NULL, '1985-03-20') RETURNING co_seq_cidadao"
            )
        ).scalar_one()

    m.run(pg_engine)

    with pg_engine.connect() as c:
        nascimento = c.execute(text("SELECT dt_nascimento FROM public.tb_cidadao")).scalar_one()

    esperado = _nova_data_esperada(str(cidadao_id), date(1985, 3, 20))
    assert nascimento == esperado
    assert nascimento.year == 1985
    assert nascimento.month == 3


def test_cpf_nulo_propaga_para_familia_atend_prof(pg_engine):
    """O fallback de CPF nulo precisa valer tambem pras tabelas descobertas
    pelas familias genericas, nao so pro proprio tb_cidadao."""
    cidadao_id = _seed_atend_prof_family(pg_engine, cpf=None, nascimento="1988-03-12")

    m.run(pg_engine)

    with pg_engine.connect() as c:
        row = c.execute(
            text("SELECT dt_inicio_problema FROM public.tb_problema_evolucao")
        ).one()
        nascimento = c.execute(text("SELECT dt_nascimento FROM public.tb_cidadao")).scalar_one()

    esperado_nascimento = _nova_data_esperada(str(cidadao_id), date(1988, 3, 12))
    assert nascimento == esperado_nascimento
    intervalo_antigo = (date(1988, 4, 2) - date(1988, 3, 12)).days
    assert (row.dt_inicio_problema - nascimento).days == intervalo_antigo
