# Auditoria do schema real

O script le apenas metadados de tabelas/colunas; nao le valores de celulas.

- Tabelas inspecionadas: 1154
- Colunas inspecionadas: 10033
- Achados cobertos: 623
- Achados suspeitos nao cobertos: 432
- Colunas declaradas em migrations mas ausentes no banco: 0

## Resumo por categoria

| Status | Categoria | Quantidade |
|---|---|---|
| Coberto | Antropometria | 27 |
| Coberto | CNES unidade | 27 |
| Coberto | CNS | 91 |
| Coberto | CPF | 92 |
| Coberto | Data nascimento | 55 |
| Coberto | Documento/anexo | 6 |
| Coberto | E-mail | 20 |
| Coberto | Endereco | 146 |
| Coberto | Identificacao mista | 12 |
| Coberto | NIS | 7 |
| Coberto | Naturalizacao | 18 |
| Coberto | Nome cidadao | 11 |
| Coberto | Nome profissional | 10 |
| Coberto | Nome unidade de saude | 4 |
| Coberto | Obito/DO | 3 |
| Coberto | Prontuario | 33 |
| Coberto | Registro profissional | 6 |
| Coberto | Telefone | 55 |
| Suspeito nao coberto | CNS | 1 |
| Suspeito nao coberto | Data nascimento | 15 |
| Suspeito nao coberto | Data registro | 32 |
| Suspeito nao coberto | Documento/anexo | 18 |
| Suspeito nao coberto | E-mail | 13 |
| Suspeito nao coberto | Endereco | 88 |
| Suspeito nao coberto | Identificacao | 1 |
| Suspeito nao coberto | Identificacao mista | 4 |
| Suspeito nao coberto | Log de acesso | 42 |
| Suspeito nao coberto | Nome cidadao | 3 |
| Suspeito nao coberto | Nome unidade de saude | 2 |
| Suspeito nao coberto | Obito/DO | 32 |
| Suspeito nao coberto | Prontuario | 118 |
| Suspeito nao coberto | Registro profissional | 63 |

## Suspeito nao coberto

| Categoria | Coluna | Tipo | Detalhe |
|---|---|---|---|
| CNS | `public.tb_fat_cad_domiciliar.nu_instituicao_cns` | `character varying` | identificador nacional de saude |
| Data nascimento | `public.ta_cidadao.co_pais_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.ta_cidadao_aldeado.co_aldeia_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.ta_cidadao_aldeado.co_uf_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.tb_cidadao.co_pais_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.tb_cidadao_aldeado.co_aldeia_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.tb_cidadao_aldeado.co_uf_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.tb_familia.dt_nascimento_responsavel` | `date` | data de nascimento |
| Data nascimento | `public.tb_fat_avaliacao_elegibilidade.co_dim_pais_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.tb_fat_cad_dom_familia.dt_nascimento` | `date` | data de nascimento |
| Data nascimento | `public.tb_fat_cad_individual.co_dim_pais_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.tb_fat_cidadao_aldeado.co_aldeia_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.tb_fat_cidadao_pec.co_dim_tempo_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.tb_fat_consolidado_cidadao_fci.dt_nascimento` | `date` | data de nascimento |
| Data nascimento | `public.tl_cidadao.co_pais_nascimento` | `bigint` | data de nascimento |
| Data nascimento | `public.tl_familia.dt_nascimento_responsavel` | `date` | data de nascimento |
| Data registro | `public.ta_cuidado_compartilhado_evol.dt_evolucao` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.ta_exame_requisitado.dt_resultado` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.ta_ivcf.dt_resultado` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.ta_lembrete_evolucao.dt_prontuario_lembrete` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tb_cuidado_compartilhado_evol.dt_evolucao` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tb_exame_requisitado.dt_resultado` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_atd_ind_exames.dt_resultado` | `date` | data de registro/atendimento |
| Data registro | `public.tb_fat_atd_ind_procedimentos.dt_inicial_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_atend_odonto_exames.dt_inicial_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_atend_odonto_exames.dt_resultado` | `date` | data de registro/atendimento |
| Data registro | `public.tb_fat_atend_odonto_proced.dt_inicial_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_atendimento_individual.dt_final_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_atendimento_individual.dt_inicial_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_atendimento_odonto.dt_final_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_atendimento_odonto.dt_inicial_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_cuidado_compartilhado.dt_criacao_cuidado` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_cuidado_compartilhado.dt_evolucao` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_cuidado_compartilhado.dt_evolucao_anterior` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_ivcf.dt_resultado` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_proced_atend.dt_final_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_proced_atend.dt_inicial_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_vacinacao.dt_final_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_fat_vacinacao.dt_inicial_atendimento` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_ivcf.dt_resultado` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tb_justificativa_prontuario.dt_acesso_prontuario` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tb_lembrete_evolucao.dt_prontuario_lembrete` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tb_regulacao_evolucao.dt_evolucao_regulacao` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tl_exame_requisitado.dt_resultado` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tl_justificativa_prontuario.dt_acesso_prontuario` | `timestamp with time zone` | data de registro/atendimento |
| Data registro | `public.tl_lembrete.dt_prontuario_lembrete` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tl_lembrete_evolucao.dt_prontuario_lembrete` | `timestamp without time zone` | data de registro/atendimento |
| Data registro | `public.tl_regulacao_evolucao.dt_evolucao_regulacao` | `timestamp without time zone` | data de registro/atendimento |
| Documento/anexo | `public.rl_arquivo_atendprof.co_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.rl_arquivo_atendprof.co_seq_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo.co_seq_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo.co_seq_taarquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo_atendprof.co_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo_atendprof.co_seq_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo_atendprof.co_seq_taarquivoatendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_exame_requisitado.co_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_arquivo.co_seq_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_arquivo_temporario.co_seq_arquivo_temporario` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_arquivo_temporario.st_arquivo` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_categoria_arquivo_atendprof.co_categoria_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_categoria_arquivo_atendprof.no_categoria_arquivo_atendprof` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_cidadao_bolsa_familia.nu_documento` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_cidadao_bolsa_familia.nu_posicao_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_exame_requisitado.co_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_historico_dados_tags.st_anexo_arquivo` | `integer` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_importacao_bolsa_familia.ds_hash_arquivo` | `character varying` | arquivo ou documento anexado |
| E-mail | `public.ta_agendado.st_enviou_email_cidadao` | `integer` | endereco de e-mail |
| E-mail | `public.ta_credencial_integracao.ds_email` | `character varying` | endereco de e-mail |
| E-mail | `public.ta_servidor_smtp.ds_email` | `character varying` | endereco de e-mail |
| E-mail | `public.ta_servidor_smtp.st_usuario_email` | `integer` | endereco de e-mail |
| E-mail | `public.ta_sistema_externo.ds_email` | `character varying` | endereco de e-mail |
| E-mail | `public.ta_usuario.dt_envio_email_recuperar_senha` | `timestamp without time zone` | endereco de e-mail |
| E-mail | `public.tb_agendado.st_enviou_email_cidadao` | `integer` | endereco de e-mail |
| E-mail | `public.tb_credencial_integracao.ds_email` | `character varying` | endereco de e-mail |
| E-mail | `public.tb_dado_recebido_info_instalac.ds_email` | `character varying` | endereco de e-mail |
| E-mail | `public.tb_servidor_smtp.ds_email` | `character varying` | endereco de e-mail |
| E-mail | `public.tb_servidor_smtp.st_usuario_email` | `integer` | endereco de e-mail |
| E-mail | `public.tb_sistema_externo.ds_email` | `character varying` | endereco de e-mail |
| E-mail | `public.tb_usuario.dt_envio_email_recuperar_senha` | `timestamp without time zone` | endereco de e-mail |
| Endereco | `public.ta_cds_domicilio.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.ta_cidadao.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.ta_encaminhamento.ds_complemento` | `character varying` | endereco |
| Endereco | `public.ta_prof.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.ta_unidade_saude.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_cep_domicilio` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_cep_tb_cidadao` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_complemento_domicilio` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_complemento_tb_cidadao` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_logradouro_domicilio` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_logradouro_domicilio_filtro` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_logradouro_tb_cidadao` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_logradouro_tb_cidadao_filtr` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_bairro_domicilio` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_bairro_domicilio_filtro` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_bairro_tb_cidadao` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_bairro_tb_cidadao_filtro` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_tipo_logradouro_domicilio` | `character varying` | endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_tipo_logradouro_tb_cidadao` | `character varying` | endereco |
| Endereco | `public.tb_aldeia.nu_cep` | `character varying` | endereco |
| Endereco | `public.tb_bairro.co_bairro` | `bigint` | endereco |
| Endereco | `public.tb_bairro.no_bairro` | `character varying` | endereco |
| Endereco | `public.tb_bairro.no_bairro_filtro` | `character varying` | endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.ds_complemento` | `character varying` | endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.ds_ponto_referencia` | `character varying` | endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.no_bairro` | `character varying` | endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.no_logradouro` | `character varying` | endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.nu_cep` | `character varying` | endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.nu_domicilio` | `character varying` | endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.st_sem_numero` | `integer` | endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_cds_cad_domiciliar.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_cds_domicilio.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_cds_visita_domiciliar.nu_latitude` | `double precision` | endereco |
| Endereco | `public.tb_cds_visita_domiciliar.nu_longitude` | `double precision` | endereco |
| Endereco | `public.tb_cidadao.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_dim_tipo_logradouro.co_seq_dim_tipo_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_dim_tipo_logradouro.ds_tipo_logradouro` | `character varying` | endereco |
| Endereco | `public.tb_dim_unidade_saude.no_bairro` | `character varying` | endereco |
| Endereco | `public.tb_encaminhamento.ds_complemento` | `character varying` | endereco |
| Endereco | `public.tb_fat_avaliacao_elegibilidade.co_dim_tipo_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_fat_cad_domiciliar.co_dim_tipo_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_fat_visita_domiciliar.nu_latitude` | `double precision` | endereco |
| Endereco | `public.tb_fat_visita_domiciliar.nu_longitude` | `double precision` | endereco |
| Endereco | `public.tb_localidade.nu_cep` | `character varying` | endereco |
| Endereco | `public.tb_logradouro.co_bairro_dne` | `character varying` | endereco |
| Endereco | `public.tb_logradouro.co_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_logradouro.ds_letra_numero_complemento` | `character varying` | endereco |
| Endereco | `public.tb_logradouro.no_complemento` | `character varying` | endereco |
| Endereco | `public.tb_logradouro.no_logradouro` | `character varying` | endereco |
| Endereco | `public.tb_logradouro.no_logradouro_exibicao` | `character varying` | endereco |
| Endereco | `public.tb_logradouro.no_logradouro_filtro` | `character varying` | endereco |
| Endereco | `public.tb_logradouro.nu_cep` | `character varying` | endereco |
| Endereco | `public.tb_logradouro.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_prof.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_tipo_logradouro.co_tipo_logradouro` | `bigint` | endereco |
| Endereco | `public.tb_tipo_logradouro.co_tp_logradouro_cadsus` | `character varying` | endereco |
| Endereco | `public.tb_tipo_logradouro.no_tipo_logradouro` | `character varying` | endereco |
| Endereco | `public.tb_tipo_logradouro.no_tipo_logradouro_filtro` | `character varying` | endereco |
| Endereco | `public.tb_unidade_saude.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tl_bairro.co_bairro` | `bigint` | endereco |
| Endereco | `public.tl_bairro.no_bairro` | `character varying` | endereco |
| Endereco | `public.tl_bairro.no_bairro_filtro` | `character varying` | endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.ds_complemento` | `character varying` | endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.ds_ponto_referencia` | `character varying` | endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.no_bairro` | `character varying` | endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.no_logradouro` | `character varying` | endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.nu_cep` | `character varying` | endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.nu_domicilio` | `character varying` | endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.st_sem_numero` | `integer` | endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tl_cds_cad_domiciliar.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tl_cds_domicilio.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tl_cds_visita_domiciliar.nu_latitude` | `double precision` | endereco |
| Endereco | `public.tl_cds_visita_domiciliar.nu_longitude` | `double precision` | endereco |
| Endereco | `public.tl_cidadao.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tl_encaminhamento.ds_complemento` | `character varying` | endereco |
| Endereco | `public.tl_logradouro.co_bairro_dne` | `character varying` | endereco |
| Endereco | `public.tl_logradouro.co_logradouro` | `bigint` | endereco |
| Endereco | `public.tl_logradouro.ds_letra_numero_complemento` | `character varying` | endereco |
| Endereco | `public.tl_logradouro.no_complemento` | `character varying` | endereco |
| Endereco | `public.tl_logradouro.no_logradouro` | `character varying` | endereco |
| Endereco | `public.tl_logradouro.no_logradouro_exibicao` | `character varying` | endereco |
| Endereco | `public.tl_logradouro.no_logradouro_filtro` | `character varying` | endereco |
| Endereco | `public.tl_logradouro.nu_cep` | `character varying` | endereco |
| Endereco | `public.tl_logradouro.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tl_prof.tp_logradouro` | `bigint` | endereco |
| Endereco | `public.tl_unidade_saude.tp_logradouro` | `bigint` | endereco |
| Identificacao | `public.tb_dim_cidadao_pec_grupo.co_identificacao` | `character varying` | pode ser CPF/CNS/UUID; exige coluna de tipo |
| Identificacao mista | `public.ta_credencial_integracao.ds_cpf_cnpj` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.ta_sistema_externo.ds_cpf_cnpj` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_credencial_integracao.ds_cpf_cnpj` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_sistema_externo.ds_cpf_cnpj` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Log de acesso | `public.tb_ad_transmissao_sessao.co_unico_transmissao_sessao` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_ad_transmissao_sessao.ds_conteudo` | `bytea` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_ad_transmissao_sessao.ds_dado_usuario` | `bytea` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_ad_transmissao_sessao.dt_tempo_sessao` | `timestamp without time zone` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_evento.co_registro_afetado` | `text` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_evento.co_seq_auditoria_evento` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_evento.co_usuario` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_evento.ds_componente_gerador` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_evento.ds_detalhes` | `text` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_evento.dt_evento` | `timestamp with time zone` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_evento.tp_evento` | `integer` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_evento.tp_registro_afetado` | `integer` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_processo.co_seq_auditoria_processo` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_processo.co_usuario` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_processo.dt_fim` | `date` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_processo.dt_inicio` | `date` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_processo.dt_solicitacao` | `timestamp without time zone` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_processo.im_impressao` | `bytea` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_processo.st_csv` | `integer` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_auditoria_processo.st_processo` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_envio_log.co_seq_envio_log` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_envio_log.data` | `timestamp with time zone` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_envio_log.file_name` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_envio_log.mensagem` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_envio_log.st_status_envio` | `integer` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_historico_acesso.co_ip` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_historico_acesso.co_seq_hist_acesso` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_historico_acesso.co_usuario` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_historico_acesso.ds_cliente_acesso` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_historico_acesso.ds_local_acesso` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_historico_acesso.dt_acesso` | `timestamp with time zone` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_historico_acesso.st_sucesso` | `integer` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.co_origem` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.co_recebimento_lote` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.co_unico_aplicativo` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.co_unico_servidor` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.co_unico_sessao` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.co_usuario` | `bigint` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.dt_fim` | `date` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.dt_inicio` | `date` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.dt_ultima_sincronizacao` | `date` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Log de acesso | `public.tb_sessao_sincronizacao.nu_versao_cliente` | `character varying` | tabela inteira de auditoria/log/sessao - guideline pede exclusao |
| Nome cidadao | `public.tb_historico_dados_fai.no_nome_finalizador_obs` | `character varying` | nome de pessoa |
| Nome cidadao | `public.tb_historico_dados_fcc.no_nome_executante` | `character varying` | nome de pessoa |
| Nome cidadao | `public.tb_historico_dados_fcc.no_nome_solicitante` | `character varying` | nome de pessoa |
| Nome unidade de saude | `public.tb_dim_inep.no_estabelecimento` | `character varying` | nome da unidade |
| Nome unidade de saude | `public.tb_inep.no_estabelecimento` | `character varying` | nome da unidade |
| Obito/DO | `public.ta_ad_cidadao.co_unico_ad_cidadao_obito` | `bigint` | numero/documento de obito |
| Obito/DO | `public.ta_ad_cidadao.dt_reg_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.ta_ad_cidadao.nu_documento_obito` | `character varying` | numero/documento de obito |
| Obito/DO | `public.ta_antecedente.ds_obito_antes_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.ta_antecedente.ds_obito_apos_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.ta_cidadao.dt_obito` | `date` | numero/documento de obito |
| Obito/DO | `public.ta_cidadao.nu_documento_obito` | `character varying` | numero/documento de obito |
| Obito/DO | `public.ta_cidadao.st_dados_obito_cadsus` | `integer` | numero/documento de obito |
| Obito/DO | `public.ta_cidadao_vinculacao_equipe.st_saida_cadastro_obito` | `integer` | numero/documento de obito |
| Obito/DO | `public.tb_ad_cidadao.co_unico_ad_cidadao_obito` | `bigint` | numero/documento de obito |
| Obito/DO | `public.tb_ad_cidadao.dt_reg_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.tb_ad_cidadao.nu_documento_obito` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tb_antecedente.ds_obito_antes_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tb_antecedente.ds_obito_apos_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tb_cds_atend_domiciliar.st_inicio_acompanhamento_obito` | `integer` | numero/documento de obito |
| Obito/DO | `public.tb_cds_cad_individual.dt_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.tb_cidadao.dt_obito` | `date` | numero/documento de obito |
| Obito/DO | `public.tb_cidadao.nu_documento_obito` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tb_cidadao.st_dados_obito_cadsus` | `integer` | numero/documento de obito |
| Obito/DO | `public.tb_cidadao_vinculacao_equipe.st_saida_cadastro_obito` | `integer` | numero/documento de obito |
| Obito/DO | `public.tb_fat_cad_individual.dt_obito` | `date` | numero/documento de obito |
| Obito/DO | `public.tl_ad_cidadao.co_unico_ad_cidadao_obito` | `bigint` | numero/documento de obito |
| Obito/DO | `public.tl_ad_cidadao.dt_reg_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.tl_ad_cidadao.nu_documento_obito` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tl_antecedente.ds_obito_antes_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tl_antecedente.ds_obito_apos_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tl_cds_atend_domiciliar.st_inicio_acompanhamento_obito` | `integer` | numero/documento de obito |
| Obito/DO | `public.tl_cds_cad_individual.dt_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.tl_cidadao.dt_obito` | `date` | numero/documento de obito |
| Obito/DO | `public.tl_cidadao.nu_documento_obito` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tl_cidadao.st_dados_obito_cadsus` | `integer` | numero/documento de obito |
| Obito/DO | `public.tl_cidadao_vinculacao_equipe.st_saida_cadastro_obito` | `integer` | numero/documento de obito |
| Prontuario | `public.rl_antecedente_ciap.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.rl_cds_prontuario_unidade_saud.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_ad_cidadao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_agendado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_alergia.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_antecedente.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_antecedente_ciap.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_atend.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_atestado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_cidadao.st_compartilhamento_prontuario` | `integer` | identificador interno |
| Prontuario | `public.ta_cirurgias_internacoes.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_compartilhamento_prontuario.co_seq_compartilha_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_cuidado_compartilhado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_encaminhamento.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_evolucao_odonto.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_exame_requisitado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_guia_encaminhamento.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_ivcf.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_lembrete.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_medicamento_uso_continuo.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_neuro_alter_fenot.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_neuro_fator_risco.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_neuro_marco.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_odontograma.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_orientacao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_periograma_completo.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_periograma_simplificado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_pre_natal.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_problema.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_prontuario.co_prontuario_grupo` | `bigint` | identificador interno |
| Prontuario | `public.ta_prontuario.co_seq_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_prontuario.co_seq_taprontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_prontuario_grupo_historico.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_prontuario_grupo_historico.co_prontuario_grupo` | `bigint` | identificador interno |
| Prontuario | `public.ta_prontuario_grupo_historico.co_seq_prontuario_grpo_hstrco` | `bigint` | identificador interno |
| Prontuario | `public.ta_prontuario_grupo_historico.co_seq_taprontuariogrupohistrc` | `bigint` | identificador interno |
| Prontuario | `public.ta_prontuario_unidade_saude.co_seq_prontuario_unidade_saud` | `bigint` | identificador interno |
| Prontuario | `public.ta_prontuario_unidade_saude.co_seq_taprontuariounidadesaud` | `bigint` | identificador interno |
| Prontuario | `public.ta_retificacao_atend.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_risco.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_sinan_notificacao_evolucao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_tecido_mole.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_vacinacao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_ad_cidadao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_agendado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_alergia.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_antecedente.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_atend.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_atestado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_cds_atend_individual.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_cidadao.st_compartilhamento_prontuario` | `integer` | identificador interno |
| Prontuario | `public.tb_cirurgias_internacoes.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_cuidado_compartilhado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_encaminhamento.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_evolucao_odonto.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_exame_requisitado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_guia_encaminhamento.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_historico_cabecalho.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_ivcf.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_justificativa_prontuario.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_lembrete.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_mchat.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_medicamento_uso_continuo.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_neuro_alter_fenot.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_neuro_fator_risco.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_neuro_marco.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_odontograma.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_orientacao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_periograma_completo.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_periograma_simplificado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_pre_natal.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_problema.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_proced_solicitado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_prontuario.co_prontuario_grupo` | `bigint` | identificador interno |
| Prontuario | `public.tb_prontuario.co_seq_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_prontuario_grupo_historico.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_prontuario_grupo_historico.co_prontuario_grupo` | `bigint` | identificador interno |
| Prontuario | `public.tb_prontuario_grupo_historico.co_seq_prontuario_grpo_hstrco` | `bigint` | identificador interno |
| Prontuario | `public.tb_prontuario_unidade_saude.co_seq_prontuario_unidade_saud` | `bigint` | identificador interno |
| Prontuario | `public.tb_regulacao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_retificacao_atend.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_risco.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_sinan_notificacao_evolucao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_tecido_mole.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_vacinacao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_ad_cidadao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_agendado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_alergia.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_antecedente.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_antecedente_ciap.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_atend.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_atestado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_cds_atend_individual.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_cidadao.st_compartilhamento_prontuario` | `integer` | identificador interno |
| Prontuario | `public.tl_compartilhamento_prontuario.co_seq_compartilha_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_encaminhamento.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_evolucao_odonto.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_exame_requisitado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_justificativa_prontuario.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_lembrete.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_medicamento_uso_continuo.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_neuro_alter_fenot.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_neuro_fator_risco.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_neuro_marco.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_odontograma.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_orientacao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_pre_natal.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_problema.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_proced_solicitado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario.co_prontuario_grupo` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario.co_seq_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario_grupo_historico.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario_grupo_historico.co_prontuario_grupo` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario_grupo_historico.co_seq_prontuario_grpo_hstrco` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario_unidade_saude.co_seq_prontuario_unidade_saud` | `bigint` | identificador interno |
| Prontuario | `public.tl_regulacao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_sinan_notificacao_evolucao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_vacinacao.co_prontuario` | `bigint` | identificador interno |
| Registro profissional | `public.ta_atend.st_registro_tardio` | `integer` | registro/conselho profissional |
| Registro profissional | `public.ta_atend_prof.co_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.ta_atend_prof.co_uf_emissora_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.ta_atend_prof.st_registro_historico` | `integer` | registro/conselho profissional |
| Registro profissional | `public.ta_atividade_coletiva.st_registro_enviado` | `integer` | registro/conselho profissional |
| Registro profissional | `public.ta_cfg_agenda_online_detalhe.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.ta_cidadao.st_registro_cadsus` | `integer` | registro/conselho profissional |
| Registro profissional | `public.ta_config_agenda_fechamento.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.ta_prof.co_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.ta_prof.co_uf_emissora_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.ta_receita_medicamento.st_registro_manual` | `integer` | registro/conselho profissional |
| Registro profissional | `public.ta_registro_vacinacao.st_registro_anterior` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_aldeia.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_atend.st_registro_tardio` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_atend_prof.co_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.tb_atend_prof.co_uf_emissora_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.tb_atend_prof.st_registro_historico` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_atividade_coletiva.st_registro_enviado` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_cfg_agenda_online_detalhe.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_cidadao.st_registro_cadsus` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_config_agenda_fechamento.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_conselho_classe.co_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.tb_conselho_classe.no_conselho_classe` | `character varying` | registro/conselho profissional |
| Registro profissional | `public.tb_conselho_classe.no_conselho_classe_filtro` | `character varying` | registro/conselho profissional |
| Registro profissional | `public.tb_conselho_classe.sg_conselho_classe` | `character varying` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_aldeia.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_catmat.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_cbo.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_ciap.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_cid.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_dsei.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_equipe.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_especialidade.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_forma_farmaceutica.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_imunobiologico.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_inep.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_municipio.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_pais.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_polo_base.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_procedimento.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_profissional.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_unidade_saude.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dsei.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_fat_familia.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_fat_vacinacao_vacina.st_registro_anterior` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_polo_base.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_prof.co_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.tb_prof.co_uf_emissora_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.tb_receita_medicamento.st_registro_manual` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_registro_vacinacao.st_registro_anterior` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_tipo_area.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_tipo_terra.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tl_atend.st_registro_tardio` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tl_atend_prof.co_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.tl_atend_prof.co_uf_emissora_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.tl_atend_prof.st_registro_historico` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tl_cfg_agenda_online_detalhe.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tl_cidadao.st_registro_cadsus` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tl_config_agenda_fechamento.st_registro_ativo` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tl_prof.co_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.tl_prof.co_uf_emissora_conselho_classe` | `bigint` | registro/conselho profissional |
| Registro profissional | `public.tl_receita_medicamento.st_registro_manual` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tl_registro_vacinacao.st_registro_anterior` | `integer` | registro/conselho profissional |

## Coberto

| Categoria | Coluna | Tipo | Migration |
|---|---|---|---|
| Antropometria | `public.ta_medicao.nu_medicao_altura` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.ta_medicao.nu_medicao_altura_uterina` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.ta_medicao.nu_medicao_circunf_abdominal` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.ta_medicao.nu_medicao_imc` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.ta_medicao.nu_medicao_perimetro_cefalico` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.ta_medicao.nu_medicao_peso` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.ta_medicao.nu_perimetro_panturrilha` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tb_fat_atendimento_individual.nu_circ_abdominal` | `numeric` | 08_anon_antropometrico |
| Antropometria | `public.tb_fat_atendimento_individual.nu_perim_panturrilha` | `numeric` | 08_anon_antropometrico |
| Antropometria | `public.tb_fat_atendimento_odonto.nu_circ_abdominal` | `numeric` | 08_anon_antropometrico |
| Antropometria | `public.tb_fat_atendimento_odonto.nu_perim_panturrilha` | `numeric` | 08_anon_antropometrico |
| Antropometria | `public.tb_fat_proced_atend.nu_circ_abdominal` | `numeric` | 08_anon_antropometrico |
| Antropometria | `public.tb_fat_proced_atend.nu_perim_panturrilha` | `numeric` | 08_anon_antropometrico |
| Antropometria | `public.tb_medicao.nu_medicao_altura` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tb_medicao.nu_medicao_altura_uterina` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tb_medicao.nu_medicao_circunf_abdominal` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tb_medicao.nu_medicao_imc` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tb_medicao.nu_medicao_perimetro_cefalico` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tb_medicao.nu_medicao_peso` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tb_medicao.nu_perimetro_panturrilha` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tl_medicao.nu_medicao_altura` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tl_medicao.nu_medicao_altura_uterina` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tl_medicao.nu_medicao_circunf_abdominal` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tl_medicao.nu_medicao_imc` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tl_medicao.nu_medicao_perimetro_cefalico` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tl_medicao.nu_medicao_peso` | `character varying` | 08_anon_antropometrico |
| Antropometria | `public.tl_medicao.nu_perimetro_panturrilha` | `character varying` | 08_anon_antropometrico |
| CNES unidade | `public.ta_cds_domicilio.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.ta_cidadao_vinculacao_equipe.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.ta_equipe_unificacao_base.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.ta_unidade_saude.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.ta_unidade_saude_unif_base.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_cds_domicilio.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_cds_ficha_ativ_col.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_cds_prof.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_cidadao_nucleo_familiar.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_cidadao_vinculacao_equipe.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_dim_unidade_saude.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_equipe_unificacao_base.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_familia.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_grupo_ativ_col.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_prof_grupo_ativ_col.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_revisao.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_unidade_saude.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tb_unidade_saude_unif_base.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tl_cds_domicilio.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tl_cds_ficha_ativ_col.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tl_cds_prof.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tl_cidadao_nucleo_familiar.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tl_cidadao_vinculacao_equipe.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tl_familia.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tl_grupo_ativ_col.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tl_prof_grupo_ativ_col.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNES unidade | `public.tl_unidade_saude.nu_cnes` | `character varying` | 02_anon_unidade_saude |
| CNS | `public.ta_ativ_col_cidadao_particip.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.ta_cds_domicilio.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.ta_cds_domicilio.nu_cns_responsavel_tecnico` | `character varying` | 10_anon_cns |
| CNS | `public.ta_cidadao.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.ta_cidadao.nu_cns_cuidador` | `character varying` | 10_anon_cns |
| CNS | `public.ta_cidadao.nu_cns_responsavel` | `character varying` | 10_anon_cns |
| CNS | `public.ta_cidadao_grupo.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.ta_cidadao_unificacao_base.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.ta_prof.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.ta_prof_historico_cns.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_acomp_cidadaos_vinculados.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_atend_prof_ad.nu_cns_cuidador` | `character varying` | 10_anon_cns |
| CNS | `public.tb_ativ_col_cidadao_particip.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_aval_elegibilidade.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_aval_elegibilidade.nu_cns_cuidador` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_cad_domiciliar.nu_cns_responsavel_tecnico` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_cad_individual.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_domicilio.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_domicilio.nu_cns_responsavel_tecnico` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_ficha_consumo_alimentar.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_ficha_zika_microcefalia.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_ficha_zika_microcefalia.nu_cns_responsavel_familiar` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cds_prof.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cidadao.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cidadao.nu_cns_cuidador` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cidadao.nu_cns_responsavel` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cidadao_grupo.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cidadao_grupo_ativ_col.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cidadao_nucleo_familiar.nu_cns_profissional` | `character varying` | 10_anon_cns |
| CNS | `public.tb_cidadao_unificacao_base.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_dim_profissional.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_envio_rnds.nu_cns_prof` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_atd_ind_encaminhamentos.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_atd_ind_exames.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_atd_ind_medicamentos.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_atd_ind_problemas.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_atd_ind_procedimentos.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_atend_odonto_encaminham.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_atend_odonto_exames.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_atend_odonto_medicament.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_atend_odonto_problemas.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_atend_odonto_proced.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_atendimento_domiciliar.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_atendimento_individual.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_atendimento_odonto.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_atvdd_coletiva_part.nu_participante_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_avaliacao_elegibilidade.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_avaliacao_elegibilidade.nu_cns_cuidador` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_cad_dom_familia.nu_cns_responsavel` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_cad_individual.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_cad_individual.nu_cns_responsavel` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_cidadao.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_cidadao_pec.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_complementar.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_complementar.nu_cns_responsavel` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_cuidado_compartilhado.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_familia.nu_cns_responsavel` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_ivcf.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_marca_consumo_alimnt.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_proced_atend.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_proced_atend_proced.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_solicitacao_oci.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tb_fat_vacinacao.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_fat_visita_domiciliar.nu_cns` | `character` | 10_anon_cns |
| CNS | `public.tb_historico_cabecalho.nu_cns_prof` | `character varying` | 10_anon_cns |
| CNS | `public.tb_historico_dados_fai.nu_cns_finalizador_obs` | `character varying` | 10_anon_cns |
| CNS | `public.tb_historico_dados_fcc.nu_cns_executante` | `character varying` | 10_anon_cns |
| CNS | `public.tb_historico_dados_fcc.nu_cns_solicitante` | `character varying` | 10_anon_cns |
| CNS | `public.tb_prof.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_prof_grupo_ativ_col.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_prof_historico_cns.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tb_revisao.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tl_atend_prof_ad.nu_cns_cuidador` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cds_aval_elegibilidade.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cds_aval_elegibilidade.nu_cns_cuidador` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cds_cad_domiciliar.nu_cns_responsavel_tecnico` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cds_cad_individual.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cds_domicilio.nu_cns_responsavel_tecnico` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cds_ficha_consumo_alimentar.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cds_ficha_zika_microcefalia.nu_cns_cidadao` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cds_ficha_zika_microcefalia.nu_cns_responsavel_familiar` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cds_prof.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cidadao.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cidadao.nu_cns_cuidador` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cidadao.nu_cns_responsavel` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cidadao_grupo.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cidadao_grupo_ativ_col.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cidadao_nucleo_familiar.nu_cns_profissional` | `character varying` | 10_anon_cns |
| CNS | `public.tl_cns.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tl_prof.nu_cns` | `character varying` | 10_anon_cns |
| CNS | `public.tl_prof_grupo_ativ_col.nu_cns` | `character varying` | 10_anon_cns |
| CPF | `public.ta_ativ_col_cidadao_particip.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.ta_cidadao.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.ta_cidadao.nu_cpf_cuidador` | `character varying` | 01_anon_cpf |
| CPF | `public.ta_cidadao.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.ta_cidadao_grupo.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.ta_cidadao_unificacao_base.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.ta_prof.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_acomp_cidadaos_vinculados.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_atend_prof_ad.nu_cpf_cuidador` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_ativ_col_cidadao_particip.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_atend_domiciliar.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_atend_individual.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_atend_odonto.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_ativ_col_participante.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_aval_elegibilidade.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_aval_elegibilidade.nu_cpf_cuidador` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_cad_individual.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_cad_individual.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_domicilio_familia.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_ficha_consumo_alimentar.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_ficha_zika_microcefalia.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_ficha_zika_microcefalia.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_proced.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_vacinacao.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cds_visita_domiciliar.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cidadao.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cidadao.nu_cpf_cuidador` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cidadao.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cidadao_grupo.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cidadao_grupo_ativ_col.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_cidadao_unificacao_base.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_criador_reserva_unif_base.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_estagio_unificacao_base.nu_cpf_prof_supervisor` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atd_ind_encaminhamentos.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atd_ind_exames.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atd_ind_medicamentos.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atd_ind_problemas.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atd_ind_procedimentos.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atend_odonto_encaminham.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atend_odonto_exames.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atend_odonto_medicament.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atend_odonto_problemas.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atend_odonto_proced.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atendimento_domiciliar.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atendimento_individual.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atendimento_odonto.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_atvdd_coletiva_part.nu_cpf_participante` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_avaliacao_elegibilidade.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_avaliacao_elegibilidade.nu_cpf_cuidador` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_cad_dom_familia.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_cad_individual.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_cad_individual.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_cidadao.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_cidadao_pec.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_complementar.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_complementar.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_cuidado_compartilhado.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_familia.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_ivcf.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_marca_consumo_alimnt.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_proced_atend.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_proced_atend_proced.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_solicitacao_oci.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_vacinacao.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_fat_visita_domiciliar.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_historico_cabecalho.nu_cpf_estagiario` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_lotacao_env_unificacao_base.nu_cpf_prof` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_prof.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tb_prof_grupo_ativ_col.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_atend_prof_ad.nu_cpf_cuidador` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_atend_domiciliar.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_atend_individual.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_atend_odonto.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_ativ_col_participante.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_aval_elegibilidade.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_aval_elegibilidade.nu_cpf_cuidador` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_cad_individual.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_cad_individual.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_domicilio_familia.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_ficha_consumo_alimentar.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_ficha_zika_microcefalia.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_ficha_zika_microcefalia.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_proced.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_vacinacao.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cds_visita_domiciliar.nu_cpf_cidadao` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cidadao.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cidadao.nu_cpf_cuidador` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cidadao.nu_cpf_responsavel` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cidadao_grupo.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_cidadao_grupo_ativ_col.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_prof.nu_cpf` | `character varying` | 01_anon_cpf |
| CPF | `public.tl_prof_grupo_ativ_col.nu_cpf` | `character varying` | 01_anon_cpf |
| Data nascimento | `public.ta_ativ_col_cidadao_particip.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.ta_cidadao.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.ta_cidadao.dt_nascimento_cuidador` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.ta_cidadao.dt_nascimento_responsavel` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.ta_prof.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_acomp_cidadaos_vinculados.dt_nascimento_cidadao` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_atend_prof_ad.dt_nascimento_cuidador` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_ativ_col_cidadao_particip.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_atend_domiciliar.dt_nascimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_atend_individual.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_atend_odonto.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_ativ_col_participante.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_aval_elegibilidade.dt_nascimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_cad_individual.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_cad_individual.dt_nascimento_responsavel` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_domicilio_familia.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_ficha_consumo_alimentar.dt_nascimento_cidadao` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_proced.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_vacinacao.dt_nascimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cds_visita_domiciliar.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cidadao.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cidadao.dt_nascimento_cuidador` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cidadao.dt_nascimento_responsavel` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_cidadao_grupo_ativ_col.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_atendimento_domiciliar.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_atendimento_individual.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_atendimento_odonto.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_atvdd_coletiva_part.dt_participante_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_avaliacao_elegibilidade.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_cad_individual.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_cuidado_compartilhado.dt_nascimento_cidadao` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_marca_consumo_alimnt.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_proced_atend.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_proced_atend_proced.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_vacinacao.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_fat_visita_domiciliar.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tb_prof.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_atend_prof_ad.dt_nascimento_cuidador` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_atend_domiciliar.dt_nascimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_atend_individual.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_atend_odonto.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_ativ_col_participante.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_aval_elegibilidade.dt_nascimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_cad_individual.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_cad_individual.dt_nascimento_responsavel` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_domicilio_familia.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_ficha_consumo_alimentar.dt_nascimento_cidadao` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_proced.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_vacinacao.dt_nascimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cds_visita_domiciliar.dt_nascimento` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cidadao.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cidadao.dt_nascimento_cuidador` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cidadao.dt_nascimento_responsavel` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_cidadao_grupo_ativ_col.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Data nascimento | `public.tl_prof.dt_nascimento` | `date` | 04_anon_datas_cidadao |
| Documento/anexo | `public.ta_arquivo.no_arquivo` | `character varying` | 07_anon_documentos |
| Documento/anexo | `public.tb_arquivo.no_arquivo` | `character varying` | 07_anon_documentos |
| Documento/anexo | `public.tb_arquivo_temporario.bl_arquivo` | `bytea` | 07_anon_documentos |
| Documento/anexo | `public.tb_assinatura_eletronica_atend.bl_arquivo_assinado` | `bytea` | 07_anon_documentos |
| Documento/anexo | `public.tb_migracao_estrutura.no_arquivo_migracao` | `character varying` | 07_anon_documentos |
| Documento/anexo | `public.tb_recebimento_item.no_arquivo` | `character varying` | 07_anon_documentos |
| E-mail | `public.ta_agend_compartilhado.ds_email_prof_participante` | `character varying` | 03_anon_email |
| E-mail | `public.ta_cidadao.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.ta_prof.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.ta_unidade_saude.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_cds_aval_elegibilidade.ds_email_cidadao` | `character varying` | 03_anon_email |
| E-mail | `public.tb_cds_cad_individual.ds_email_cidadao` | `character varying` | 03_anon_email |
| E-mail | `public.tb_cidadao.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_dsei.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_dsei.ds_email_chefe` | `character varying` | 03_anon_email |
| E-mail | `public.tb_fat_avaliacao_elegibilidade.no_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_fat_cad_individual.no_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_polo_base.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_polo_base.ds_email_chefe` | `character varying` | 03_anon_email |
| E-mail | `public.tb_prof.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_unidade_saude.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tl_cds_aval_elegibilidade.ds_email_cidadao` | `character varying` | 03_anon_email |
| E-mail | `public.tl_cds_cad_individual.ds_email_cidadao` | `character varying` | 03_anon_email |
| E-mail | `public.tl_cidadao.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tl_prof.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tl_unidade_saude.ds_email` | `character varying` | 03_anon_email |
| Endereco | `public.ta_cds_domicilio.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.no_logradouro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.nu_domicilio` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.nu_latitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.nu_longitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.ta_cds_domicilio.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.nu_numero` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.ta_prof.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.nu_numero` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.nu_numero` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.ds_complemento_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.no_logradouro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.nu_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.nu_domicilio` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.nu_latitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.nu_longitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.no_logradouro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.nu_domicilio` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.nu_latitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.nu_longitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.nu_numero` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tb_dsei.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_dsei.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_dsei.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_dsei.nu_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_avaliacao_elegibilidade.no_bairro_residencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_avaliacao_elegibilidade.no_complemento_residencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_avaliacao_elegibilidade.no_logradouro_residencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_avaliacao_elegibilidade.nu_cep_residencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_avaliacao_elegibilidade.nu_num_logradouro_residencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_cad_domiciliar.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_cad_domiciliar.no_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_cad_domiciliar.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_cad_domiciliar.no_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_cad_domiciliar.nu_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_fat_cad_domiciliar.nu_latitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tb_fat_cad_domiciliar.nu_longitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tb_fat_cad_domiciliar.nu_num_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_polo_base.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_polo_base.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_polo_base.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_polo_base.nu_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_prof.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_prof.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_prof.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_prof.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_prof.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_prof.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_prof.nu_numero` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_prof.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.nu_numero` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.ds_complemento_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.no_logradouro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.nu_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.nu_domicilio` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.nu_latitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.nu_longitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.nu_domicilio` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.nu_latitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.nu_longitude` | `double precision` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.nu_numero` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tl_prof.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.nu_numero` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.st_sem_numero` | `integer` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.nu_numero` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.st_sem_numero` | `integer` | 06_anon_endereco |
| Identificacao mista | `public.tb_cidadao_nucleo_familiar.nu_cpf_cns_responsavel` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tb_familia.nu_cpf_cns_responsavel` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tb_historico_cabecalho.nu_cpf_cns_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tb_historico_dados_exames.nu_cpf_cns_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tb_historico_dados_fad.nu_cpf_cns_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tb_historico_dados_fai.nu_cpf_cns_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tb_historico_dados_fao.nu_cpf_cns_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tb_historico_dados_fcc.nu_cpf_cns_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tb_historico_dados_proced.nu_cpf_cns_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tb_historico_dados_vacina.nu_cpf_cns_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tl_cidadao_nucleo_familiar.nu_cpf_cns_responsavel` | `character varying` | 11_anon_identificadores_diversos |
| Identificacao mista | `public.tl_familia.nu_cpf_cns_responsavel` | `character varying` | 11_anon_identificadores_diversos |
| NIS | `public.ta_cidadao.nu_nis_pis_pasep` | `character varying` | 11_anon_identificadores_diversos |
| NIS | `public.tb_cds_aval_elegibilidade.nu_nis_pis_pasep` | `character varying` | 11_anon_identificadores_diversos |
| NIS | `public.tb_cidadao.nu_nis_pis_pasep` | `character varying` | 11_anon_identificadores_diversos |
| NIS | `public.tb_fat_avaliacao_elegibilidade.nu_nis` | `character varying` | 11_anon_identificadores_diversos |
| NIS | `public.tb_fat_cad_individual.nu_nis` | `character varying` | 11_anon_identificadores_diversos |
| NIS | `public.tl_cds_aval_elegibilidade.nu_nis_pis_pasep` | `character varying` | 11_anon_identificadores_diversos |
| NIS | `public.tl_cidadao.nu_nis_pis_pasep` | `character varying` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.ta_cidadao.dt_naturalizacao` | `timestamp with time zone` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.ta_cidadao.nu_portaria_naturalizacao` | `character varying` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_cds_aval_elegibilidade.ds_portaria_naturalizacao` | `character varying` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_cds_aval_elegibilidade.dt_naturalizacao` | `timestamp with time zone` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_cds_cad_individual.ds_portaria_naturalizacao` | `character varying` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_cds_cad_individual.dt_naturalizacao` | `timestamp with time zone` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_cidadao.dt_naturalizacao` | `timestamp with time zone` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_cidadao.nu_portaria_naturalizacao` | `character varying` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_fat_avaliacao_elegibilidade.dt_naturalizacao` | `date` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_fat_avaliacao_elegibilidade.nu_portaria_naturalizacao` | `character varying` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_fat_cad_individual.dt_naturalizacao` | `date` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tb_fat_cad_individual.nu_portaria_naturalizacao` | `character varying` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tl_cds_aval_elegibilidade.ds_portaria_naturalizacao` | `character varying` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tl_cds_aval_elegibilidade.dt_naturalizacao` | `timestamp with time zone` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tl_cds_cad_individual.ds_portaria_naturalizacao` | `character varying` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tl_cds_cad_individual.dt_naturalizacao` | `timestamp with time zone` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tl_cidadao.dt_naturalizacao` | `timestamp with time zone` | 11_anon_identificadores_diversos |
| Naturalizacao | `public.tl_cidadao.nu_portaria_naturalizacao` | `character varying` | 11_anon_identificadores_diversos |
| Nome cidadao | `public.ta_ativ_col_cidadao_particip.no_nome` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_ativ_col_cidadao_particip.no_nome` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_fat_avaliacao_elegibilidade.no_nome` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_fat_avaliacao_elegibilidade.no_nome_mae` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_fat_avaliacao_elegibilidade.no_nome_pai` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_fat_avaliacao_elegibilidade.no_nome_social` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_fat_cad_individual.no_nome` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_fat_cad_individual.no_nome_mae` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_fat_cad_individual.no_nome_pai` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_fat_cad_individual.no_nome_social` | `character varying` | 09_anon_nome_cidadao |
| Nome cidadao | `public.tb_fat_marca_consumo_alimnt.no_nome` | `character varying` | 09_anon_nome_cidadao |
| Nome profissional | `public.ta_prof.no_civil_profissional` | `character varying` | 05_anon_profissional |
| Nome profissional | `public.ta_prof.no_profissional` | `character varying` | 05_anon_profissional |
| Nome profissional | `public.ta_prof.no_profissional_filtro` | `character varying` | 05_anon_profissional |
| Nome profissional | `public.ta_prof.no_social_profissional` | `character varying` | 05_anon_profissional |
| Nome profissional | `public.tb_dim_profissional.no_profissional` | `character varying` | 05_anon_profissional |
| Nome profissional | `public.tb_lote_transp_historico_exprt.no_profissional` | `character varying` | 05_anon_profissional |
| Nome profissional | `public.tb_prof.no_civil_profissional` | `character varying` | 05_anon_profissional |
| Nome profissional | `public.tb_prof.no_profissional_filtro` | `character varying` | 05_anon_profissional |
| Nome profissional | `public.tb_prof.no_social_profissional` | `character varying` | 05_anon_profissional |
| Nome profissional | `public.tl_prof.no_profissional_filtro` | `character varying` | 05_anon_profissional |
| Nome unidade de saude | `public.ta_unidade_saude.no_unidade_saude` | `character varying` | 02_anon_unidade_saude |
| Nome unidade de saude | `public.tb_dim_unidade_saude.no_unidade_saude` | `character varying` | 02_anon_unidade_saude |
| Nome unidade de saude | `public.tb_unidade_saude.no_unidade_saude` | `character varying` | 02_anon_unidade_saude |
| Nome unidade de saude | `public.tl_unidade_saude.no_unidade_saude` | `character varying` | 02_anon_unidade_saude |
| Obito/DO | `public.tb_cds_cad_individual.nu_declaracao_obito` | `character varying` | 11_anon_identificadores_diversos |
| Obito/DO | `public.tb_fat_cad_individual.nu_obito_do` | `character varying` | 11_anon_identificadores_diversos |
| Obito/DO | `public.tl_cds_cad_individual.nu_declaracao_obito` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.rl_cds_prontuario_unidade_saud.nu_prontuario_interno` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.ta_cidadao.co_unico_cidadao_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.ta_cidadao.co_unico_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.ta_prontuario_unidade_saude.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_cds_atend_individual.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_cds_atend_odonto.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_cds_aval_elegibilidade.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_cds_domicilio_familia.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_cds_proced.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_cds_vacinacao.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_cds_visita_domiciliar.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_familia.nu_prontuario_familiar` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_fat_atendimento_individual.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_fat_atendimento_odonto.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_fat_cad_dom_familia.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_fat_familia_territorio.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_fat_proced_atend.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_fat_vacinacao.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_fat_visita_domiciliar.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tb_prontuario_unidade_saude.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_cds_atend_individual.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_cds_atend_odonto.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_cds_aval_elegibilidade.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_cds_domicilio_familia.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_cds_proced.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_cds_vacinacao.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_cds_visita_domiciliar.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_cidadao.co_unico_cidadao_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_cidadao.co_unico_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_familia.nu_prontuario_familiar` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_prontuario.co_unico_cidadao_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_prontuario.co_unico_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Prontuario | `public.tl_prontuario_unidade_saude.nu_prontuario` | `character varying` | 11_anon_identificadores_diversos |
| Registro profissional | `public.ta_atend_prof.nu_conselho_classe` | `character varying` | 05_anon_profissional |
| Registro profissional | `public.ta_prof.nu_conselho_classe` | `character varying` | 05_anon_profissional |
| Registro profissional | `public.tb_atend_prof.nu_conselho_classe` | `character varying` | 05_anon_profissional |
| Registro profissional | `public.tb_prof.nu_conselho_classe` | `character varying` | 05_anon_profissional |
| Registro profissional | `public.tl_atend_prof.nu_conselho_classe` | `character varying` | 05_anon_profissional |
| Registro profissional | `public.tl_prof.nu_conselho_classe` | `character varying` | 05_anon_profissional |
| Telefone | `public.ta_agend_compartilhado.nu_telefone_prof_participante` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.ta_cds_domicilio.nu_fone_referencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.ta_cds_domicilio.nu_fone_residencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.ta_cidadao.nu_telefone_celular` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.ta_cidadao.nu_telefone_contato` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.ta_cidadao.nu_telefone_residencial` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.ta_prof.nu_telefone` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.ta_unidade_saude.nu_telefone_comercial` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.ta_unidade_saude.nu_telefone_comercial2` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.ta_unidade_saude.nu_telefone_fax` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_acomp_cidadaos_vinculados.nu_fone_residencial` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_acomp_cidadaos_vinculados.nu_telefone_celular` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_acomp_cidadaos_vinculados.nu_telefone_contato` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cds_aval_elegibilidade.nu_fone_referencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cds_aval_elegibilidade.nu_fone_residencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cds_cad_domiciliar.nu_fone_referencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cds_cad_domiciliar.nu_fone_residencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cds_cad_domiciliar.nu_fone_responsavel_tecnico` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cds_cad_individual.nu_celular_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cds_domicilio.nu_fone_referencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cds_domicilio.nu_fone_residencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cidadao.nu_telefone_celular` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cidadao.nu_telefone_contato` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_cidadao.nu_telefone_residencial` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_dado_recebido_info_instalac.nu_telefone` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_dsei.nu_telefone1` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_dsei.nu_telefone2` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_fat_avaliacao_elegibilidade.nu_telefone_contato` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_fat_avaliacao_elegibilidade.nu_telefone_residencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_fat_cad_domiciliar.nu_instituicao_telefone` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_fat_cad_domiciliar.nu_telefone_contato` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_fat_cad_domiciliar.nu_telefone_residencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_fat_cad_individual.nu_celular` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_fat_cidadao_pec.nu_telefone_celular` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_polo_base.nu_telefone1` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_polo_base.nu_telefone2` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_prof.nu_telefone` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_unidade_saude.nu_telefone_comercial` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_unidade_saude.nu_telefone_comercial2` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tb_unidade_saude.nu_telefone_fax` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cds_aval_elegibilidade.nu_fone_referencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cds_aval_elegibilidade.nu_fone_residencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cds_cad_domiciliar.nu_fone_referencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cds_cad_domiciliar.nu_fone_residencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cds_cad_domiciliar.nu_fone_responsavel_tecnico` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cds_cad_individual.nu_celular_cidadao` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cds_domicilio.nu_fone_referencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cds_domicilio.nu_fone_residencia` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cidadao.nu_telefone_celular` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cidadao.nu_telefone_contato` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_cidadao.nu_telefone_residencial` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_prof.nu_telefone` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_unidade_saude.nu_telefone_comercial` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_unidade_saude.nu_telefone_comercial2` | `character varying` | 11_anon_identificadores_diversos |
| Telefone | `public.tl_unidade_saude.nu_telefone_fax` | `character varying` | 11_anon_identificadores_diversos |

## Declarado nas migrations, ausente no banco

Nenhuma coluna declarada ficou ausente.
