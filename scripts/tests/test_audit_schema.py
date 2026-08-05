"""Testes da classificacao de colunas em audit_schema.py (sem banco)."""

from __future__ import annotations

from _helpers import load_migration

audit = load_migration("audit_schema.py")

T = "qualquer_tabela"  # tabela generica, nao esta em LOG_TABLES


def test_classifica_cpf():
    assert audit._classify(T, "nu_cpf_cidadao")[0] == "CPF"
    assert audit._classify(T, "nu_cpf")[0] == "CPF"


def test_classifica_cns_antes_de_cpf_quando_aplicavel():
    assert audit._classify(T, "nu_cns_cidadao")[0] == "CNS"


def test_identificacao_mista_tem_prioridade_sobre_cpf_isolado():
    assert audit._classify(T, "nu_cpf_cns_responsavel")[0] == "Identificacao mista"


def test_classifica_email_telefone_endereco():
    assert audit._classify(T, "ds_email")[0] == "E-mail"
    assert audit._classify(T, "nu_telefone_celular")[0] == "Telefone"
    assert audit._classify(T, "no_logradouro")[0] == "Endereco"


def test_coluna_sem_padrao_retorna_none():
    assert audit._classify(T, "co_seq") is None
    assert audit._classify(T, "st_ativo") is None


def test_tabela_de_log_classifica_qualquer_coluna_como_log_de_acesso():
    assert audit._classify("tb_historico_acesso", "co_ip")[0] == "Log de acesso"
    assert audit._classify("tb_auditoria_evento", "dt_evento")[0] == "Log de acesso"


def test_tabela_de_controle_de_permissao_nao_e_log():
    # tl_acesso e RBAC, nao log - nao deve cair em LOG_TABLES.
    assert "tl_acesso" not in audit.LOG_TABLES


def test_ip_fora_de_log_tables_ainda_e_classificado_por_padrao_de_coluna():
    assert audit._classify(T, "co_ip")[0] == "IP de acesso"


def test_ilike_coringa():
    assert audit._ilike("nu_cpf_cidadao", "nu_cpf%")
    assert not audit._ilike("nu_cpf_cidadao", "nu_cns%")
    assert audit._ilike("qualquer_coisa_prontuario", "%prontuario%")
