# Auditoria do schema real

O script le apenas metadados de tabelas/colunas; nao le valores de celulas.

- Tabelas inspecionadas: 1154
- Colunas inspecionadas: 10033
- Achados cobertos: 301
- Achados suspeitos nao cobertos: 698
- Colunas declaradas em migrations mas ausentes no banco: 0

## Resumo por categoria

| Status | Categoria | Quantidade |
|---|---|---|
| Coberto | CPF | 92 |
| Coberto | Data nascimento | 55 |
| Coberto | Data registro | 11 |
| Coberto | E-mail | 27 |
| Coberto | Endereco | 106 |
| Coberto | Nome profissional | 10 |
| Suspeito nao coberto | CNS | 92 |
| Suspeito nao coberto | Data nascimento | 15 |
| Suspeito nao coberto | Data registro | 36 |
| Suspeito nao coberto | Documento/anexo | 33 |
| Suspeito nao coberto | E-mail | 6 |
| Suspeito nao coberto | Endereco | 107 |
| Suspeito nao coberto | Identificacao | 1 |
| Suspeito nao coberto | Identificacao mista | 16 |
| Suspeito nao coberto | NIS | 12 |
| Suspeito nao coberto | Naturalizacao | 18 |
| Suspeito nao coberto | Nome cidadao | 11 |
| Suspeito nao coberto | Obito/DO | 29 |
| Suspeito nao coberto | Prontuario | 157 |
| Suspeito nao coberto | Registro profissional | 4 |
| Suspeito nao coberto | Telefone | 55 |
| Suspeito nao coberto | Texto livre | 106 |

## Suspeito nao coberto

| Categoria | Coluna | Tipo | Detalhe |
|---|---|---|---|
| CNS | `public.ta_ativ_col_cidadao_particip.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.ta_cds_domicilio.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.ta_cds_domicilio.nu_cns_responsavel_tecnico` | `character varying` | identificador nacional de saude |
| CNS | `public.ta_cidadao.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.ta_cidadao.nu_cns_cuidador` | `character varying` | identificador nacional de saude |
| CNS | `public.ta_cidadao.nu_cns_responsavel` | `character varying` | identificador nacional de saude |
| CNS | `public.ta_cidadao_grupo.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.ta_cidadao_unificacao_base.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.ta_prof.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.ta_prof_historico_cns.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_acomp_cidadaos_vinculados.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_atend_prof_ad.nu_cns_cuidador` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_ativ_col_cidadao_particip.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_aval_elegibilidade.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_aval_elegibilidade.nu_cns_cuidador` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_cad_domiciliar.nu_cns_responsavel_tecnico` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_cad_individual.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_domicilio.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_domicilio.nu_cns_responsavel_tecnico` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_ficha_consumo_alimentar.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_ficha_zika_microcefalia.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_ficha_zika_microcefalia.nu_cns_responsavel_familiar` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cds_prof.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cidadao.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cidadao.nu_cns_cuidador` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cidadao.nu_cns_responsavel` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cidadao_grupo.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cidadao_grupo_ativ_col.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cidadao_nucleo_familiar.nu_cns_profissional` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_cidadao_unificacao_base.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_dim_profissional.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_envio_rnds.nu_cns_prof` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_atd_ind_encaminhamentos.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_atd_ind_exames.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_atd_ind_medicamentos.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_atd_ind_problemas.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_atd_ind_procedimentos.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_atend_odonto_encaminham.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_atend_odonto_exames.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_atend_odonto_medicament.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_atend_odonto_problemas.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_atend_odonto_proced.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_atendimento_domiciliar.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_atendimento_individual.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_atendimento_odonto.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_atvdd_coletiva_part.nu_participante_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_avaliacao_elegibilidade.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_avaliacao_elegibilidade.nu_cns_cuidador` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_cad_dom_familia.nu_cns_responsavel` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_cad_domiciliar.nu_instituicao_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_cad_individual.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_cad_individual.nu_cns_responsavel` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_cidadao.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_cidadao_pec.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_complementar.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_complementar.nu_cns_responsavel` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_cuidado_compartilhado.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_familia.nu_cns_responsavel` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_ivcf.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_marca_consumo_alimnt.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_proced_atend.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_proced_atend_proced.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_solicitacao_oci.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_fat_vacinacao.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_fat_visita_domiciliar.nu_cns` | `character` | identificador nacional de saude |
| CNS | `public.tb_historico_cabecalho.nu_cns_prof` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_historico_dados_fai.nu_cns_finalizador_obs` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_historico_dados_fcc.nu_cns_executante` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_historico_dados_fcc.nu_cns_solicitante` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_prof.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_prof_grupo_ativ_col.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_prof_historico_cns.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tb_revisao.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_atend_prof_ad.nu_cns_cuidador` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cds_aval_elegibilidade.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cds_aval_elegibilidade.nu_cns_cuidador` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cds_cad_domiciliar.nu_cns_responsavel_tecnico` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cds_cad_individual.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cds_domicilio.nu_cns_responsavel_tecnico` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cds_ficha_consumo_alimentar.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cds_ficha_zika_microcefalia.nu_cns_cidadao` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cds_ficha_zika_microcefalia.nu_cns_responsavel_familiar` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cds_prof.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cidadao.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cidadao.nu_cns_cuidador` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cidadao.nu_cns_responsavel` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cidadao_grupo.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cidadao_grupo_ativ_col.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cidadao_nucleo_familiar.nu_cns_profissional` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_cns.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_prof.nu_cns` | `character varying` | identificador nacional de saude |
| CNS | `public.tl_prof_grupo_ativ_col.nu_cns` | `character varying` | identificador nacional de saude |
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
| Data registro | `public.ta_agendado.dt_criacao` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.ta_arquivo.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.ta_atend.dt_criacao_registro` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.ta_credencial_integracao.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.ta_cuidado_compartilhado.dt_ultima_evolucao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.ta_cuidado_compartilhado_evol.dt_evolucao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.ta_exame_requisitado.dt_resultado` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.ta_ivcf.dt_resultado` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.ta_sistema_externo.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_agendado.dt_criacao` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.tb_arquivo.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_atend.dt_criacao_registro` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.tb_credencial_integracao.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_cuidado_compartilhado.dt_ultima_evolucao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_cuidado_compartilhado_evol.dt_evolucao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_exame_requisitado.dt_resultado` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_fat_atd_ind_exames.dt_resultado` | `date` | data/hora longitudinal |
| Data registro | `public.tb_fat_atd_ind_exames.dt_resultado_data` | `date` | data/hora longitudinal |
| Data registro | `public.tb_fat_atd_ind_procedimentos.dt_inicial_atendimento` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.tb_fat_atend_odonto_exames.dt_inicial_atendimento` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.tb_fat_atend_odonto_exames.dt_resultado` | `date` | data/hora longitudinal |
| Data registro | `public.tb_fat_atend_odonto_exames.dt_resultado_data` | `date` | data/hora longitudinal |
| Data registro | `public.tb_fat_atend_odonto_proced.dt_inicial_atendimento` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.tb_fat_ivcf.dt_resultado` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_historico_cabecalho.dt_atendimento` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.tb_ivcf.dt_resultado` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_lote_transp.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_notificacao_status.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_refresh_token.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_regulacao_evolucao.dt_evolucao_regulacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_sistema_externo.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tb_topico_notificacao.dt_criacao` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tl_agendado.dt_criacao` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.tl_atend.dt_criacao_registro` | `timestamp with time zone` | data/hora longitudinal |
| Data registro | `public.tl_exame_requisitado.dt_resultado` | `timestamp without time zone` | data/hora longitudinal |
| Data registro | `public.tl_regulacao_evolucao.dt_evolucao_regulacao` | `timestamp without time zone` | data/hora longitudinal |
| Documento/anexo | `public.rl_arquivo_atendprof.co_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.rl_arquivo_atendprof.co_seq_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_ad_cidadao.nu_documento_obito` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo.co_seq_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo.co_seq_taarquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo.no_arquivo` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo_atendprof.co_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo_atendprof.co_seq_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_arquivo_atendprof.co_seq_taarquivoatendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_cidadao.nu_documento_obito` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_cidadao_unificacao_base.st_documentos_cidadao` | `integer` | arquivo ou documento anexado |
| Documento/anexo | `public.ta_exame_requisitado.co_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_ad_cidadao.nu_documento_obito` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_arquivo.co_seq_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_arquivo.no_arquivo` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_arquivo_temporario.bl_arquivo` | `bytea` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_arquivo_temporario.co_seq_arquivo_temporario` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_arquivo_temporario.st_arquivo` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_assinatura_eletronica_atend.bl_arquivo_assinado` | `bytea` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_categoria_arquivo_atendprof.co_categoria_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_categoria_arquivo_atendprof.no_categoria_arquivo_atendprof` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_cidadao.nu_documento_obito` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_cidadao_bolsa_familia.nu_documento` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_cidadao_bolsa_familia.nu_posicao_arquivo` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_cidadao_bolsa_familia.tp_documento` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_cidadao_unificacao_base.st_documentos_cidadao` | `integer` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_exame_requisitado.co_arquivo_atendprof` | `bigint` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_historico_dados_tags.st_anexo_arquivo` | `integer` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_importacao_bolsa_familia.ds_hash_arquivo` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_migracao_estrutura.no_arquivo_migracao` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tb_recebimento_item.no_arquivo` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tl_ad_cidadao.nu_documento_obito` | `character varying` | arquivo ou documento anexado |
| Documento/anexo | `public.tl_cidadao.nu_documento_obito` | `character varying` | arquivo ou documento anexado |
| E-mail | `public.ta_agendado.st_enviou_email_cidadao` | `integer` | contato pessoal |
| E-mail | `public.ta_servidor_smtp.st_usuario_email` | `integer` | contato pessoal |
| E-mail | `public.ta_usuario.dt_envio_email_recuperar_senha` | `timestamp without time zone` | contato pessoal |
| E-mail | `public.tb_agendado.st_enviou_email_cidadao` | `integer` | contato pessoal |
| E-mail | `public.tb_servidor_smtp.st_usuario_email` | `integer` | contato pessoal |
| E-mail | `public.tb_usuario.dt_envio_email_recuperar_senha` | `timestamp without time zone` | contato pessoal |
| Endereco | `public.ta_atend.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.ta_cds_domicilio.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.ta_cds_domicilio.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.ta_cidadao.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.ta_condicoes_saude_auto.maternidade_referencia` | `character varying` | campo de endereco |
| Endereco | `public.ta_encaminhamento.ds_complemento` | `character varying` | campo de endereco |
| Endereco | `public.ta_equipe.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.ta_ivcf.st_sg_percepcao_saude` | `integer` | campo de endereco |
| Endereco | `public.ta_perfil.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.ta_prof.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.ta_prontuario.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.ta_situacao_rua.st_possui_referencia_familiar` | `integer` | campo de endereco |
| Endereco | `public.ta_unidade_saude.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.ta_vinculacao_servico.co_estabelecimento_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_cep_domicilio` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_cep_tb_cidadao` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_complemento_domicilio` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_complemento_tb_cidadao` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_logradouro_domicilio` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_logradouro_domicilio_filtro` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_logradouro_tb_cidadao` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.ds_logradouro_tb_cidadao_filtr` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_bairro_domicilio` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_bairro_domicilio_filtro` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_bairro_tb_cidadao` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_bairro_tb_cidadao_filtro` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_tipo_logradouro_domicilio` | `character varying` | campo de endereco |
| Endereco | `public.tb_acomp_cidadaos_vinculados.no_tipo_logradouro_tb_cidadao` | `character varying` | campo de endereco |
| Endereco | `public.tb_aldeia.nu_cep` | `character varying` | campo de endereco |
| Endereco | `public.tb_atend.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tb_bairro.co_bairro` | `bigint` | campo de endereco |
| Endereco | `public.tb_bairro.no_bairro` | `character varying` | campo de endereco |
| Endereco | `public.tb_bairro.no_bairro_filtro` | `character varying` | campo de endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.ds_complemento` | `character varying` | campo de endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.ds_ponto_referencia` | `character varying` | campo de endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.no_bairro` | `character varying` | campo de endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.no_logradouro` | `character varying` | campo de endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.nu_cep` | `character varying` | campo de endereco |
| Endereco | `public.tb_cds_aval_elegibilidade.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_cds_cad_domiciliar.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_cds_domicilio.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tb_cds_domicilio.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_cidadao.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_condicoes_saude_auto.maternidade_referencia` | `character varying` | campo de endereco |
| Endereco | `public.tb_dim_tipo_logradouro.co_seq_dim_tipo_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_dim_tipo_logradouro.ds_tipo_logradouro` | `character varying` | campo de endereco |
| Endereco | `public.tb_dim_unidade_saude.no_bairro` | `character varying` | campo de endereco |
| Endereco | `public.tb_encaminhamento.ds_complemento` | `character varying` | campo de endereco |
| Endereco | `public.tb_equipe.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tb_fat_avaliacao_elegibilidade.co_dim_tipo_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_fat_avaliacao_elegibilidade.no_referencia_residencia` | `character varying` | campo de endereco |
| Endereco | `public.tb_fat_cad_domiciliar.co_dim_tipo_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_fat_cad_individual.no_maternidade_referencia` | `character varying` | campo de endereco |
| Endereco | `public.tb_fat_cad_individual.st_referencia_familiar` | `integer` | campo de endereco |
| Endereco | `public.tb_fat_ivcf.st_sg_percepcao_saude` | `integer` | campo de endereco |
| Endereco | `public.tb_ivcf.st_sg_percepcao_saude` | `integer` | campo de endereco |
| Endereco | `public.tb_localidade.nu_cep` | `character varying` | campo de endereco |
| Endereco | `public.tb_logradouro.co_bairro_dne` | `character varying` | campo de endereco |
| Endereco | `public.tb_logradouro.co_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_logradouro.ds_letra_numero_complemento` | `character varying` | campo de endereco |
| Endereco | `public.tb_logradouro.no_complemento` | `character varying` | campo de endereco |
| Endereco | `public.tb_logradouro.no_logradouro` | `character varying` | campo de endereco |
| Endereco | `public.tb_logradouro.no_logradouro_exibicao` | `character varying` | campo de endereco |
| Endereco | `public.tb_logradouro.no_logradouro_filtro` | `character varying` | campo de endereco |
| Endereco | `public.tb_logradouro.nu_cep` | `character varying` | campo de endereco |
| Endereco | `public.tb_logradouro.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_perfil.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tb_prof.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_prontuario.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tb_situacao_rua.st_possui_referencia_familiar` | `integer` | campo de endereco |
| Endereco | `public.tb_tipo_logradouro.co_tipo_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_tipo_logradouro.co_tp_logradouro_cadsus` | `character varying` | campo de endereco |
| Endereco | `public.tb_tipo_logradouro.no_tipo_logradouro` | `character varying` | campo de endereco |
| Endereco | `public.tb_tipo_logradouro.no_tipo_logradouro_filtro` | `character varying` | campo de endereco |
| Endereco | `public.tb_unidade_saude.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tb_vinculacao_servico.co_estabelecimento_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tl_ad_cidadao.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tl_atend.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tl_ator_papel.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tl_bairro.co_bairro` | `bigint` | campo de endereco |
| Endereco | `public.tl_bairro.no_bairro` | `character varying` | campo de endereco |
| Endereco | `public.tl_bairro.no_bairro_filtro` | `character varying` | campo de endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.ds_complemento` | `character varying` | campo de endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.ds_ponto_referencia` | `character varying` | campo de endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.no_bairro` | `character varying` | campo de endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.no_logradouro` | `character varying` | campo de endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.nu_cep` | `character varying` | campo de endereco |
| Endereco | `public.tl_cds_aval_elegibilidade.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tl_cds_cad_domiciliar.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tl_cds_domicilio.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tl_cds_domicilio.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tl_cidadao.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tl_encaminhamento.ds_complemento` | `character varying` | campo de endereco |
| Endereco | `public.tl_equipe.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tl_logradouro.co_bairro_dne` | `character varying` | campo de endereco |
| Endereco | `public.tl_logradouro.co_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tl_logradouro.ds_letra_numero_complemento` | `character varying` | campo de endereco |
| Endereco | `public.tl_logradouro.no_complemento` | `character varying` | campo de endereco |
| Endereco | `public.tl_logradouro.no_logradouro` | `character varying` | campo de endereco |
| Endereco | `public.tl_logradouro.no_logradouro_exibicao` | `character varying` | campo de endereco |
| Endereco | `public.tl_logradouro.no_logradouro_filtro` | `character varying` | campo de endereco |
| Endereco | `public.tl_logradouro.nu_cep` | `character varying` | campo de endereco |
| Endereco | `public.tl_logradouro.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tl_perfil.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tl_prof.tp_logradouro` | `bigint` | campo de endereco |
| Endereco | `public.tl_prontuario.qt_referencia` | `bigint` | campo de endereco |
| Endereco | `public.tl_unidade_saude.tp_logradouro` | `bigint` | campo de endereco |
| Identificacao | `public.tb_dim_cidadao_pec_grupo.co_identificacao` | `character varying` | pode ser CPF/CNS/UUID; exige coluna de tipo |
| Identificacao mista | `public.ta_credencial_integracao.ds_cpf_cnpj` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.ta_sistema_externo.ds_cpf_cnpj` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_cidadao_nucleo_familiar.nu_cpf_cns_responsavel` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_credencial_integracao.ds_cpf_cnpj` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_familia.nu_cpf_cns_responsavel` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_historico_cabecalho.nu_cpf_cns_cidadao` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_historico_dados_exames.nu_cpf_cns_cidadao` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_historico_dados_fad.nu_cpf_cns_cidadao` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_historico_dados_fai.nu_cpf_cns_cidadao` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_historico_dados_fao.nu_cpf_cns_cidadao` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_historico_dados_fcc.nu_cpf_cns_cidadao` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_historico_dados_proced.nu_cpf_cns_cidadao` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_historico_dados_vacina.nu_cpf_cns_cidadao` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tb_sistema_externo.ds_cpf_cnpj` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tl_cidadao_nucleo_familiar.nu_cpf_cns_responsavel` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| Identificacao mista | `public.tl_familia.nu_cpf_cns_responsavel` | `character varying` | pode ser CPF/CNS ou CPF/CNPJ; exige regra propria |
| NIS | `public.ta_cidadao.nu_nis_pis_pasep` | `character varying` | identificador social |
| NIS | `public.tb_cds_aval_elegibilidade.nu_nis_pis_pasep` | `character varying` | identificador social |
| NIS | `public.tb_cidadao.nu_nis_pis_pasep` | `character varying` | identificador social |
| NIS | `public.tb_dim_via_administracao.co_seq_dim_via_administracao` | `bigint` | identificador social |
| NIS | `public.tb_dim_via_administracao.no_via_administracao` | `character varying` | identificador social |
| NIS | `public.tb_dim_via_administracao.no_via_administracao_filtro` | `character varying` | identificador social |
| NIS | `public.tb_fat_atd_ind_medicamentos.co_dim_via_administracao` | `bigint` | identificador social |
| NIS | `public.tb_fat_atend_odonto_medicament.co_dim_via_administracao` | `bigint` | identificador social |
| NIS | `public.tb_fat_avaliacao_elegibilidade.nu_nis` | `character varying` | identificador social |
| NIS | `public.tb_fat_cad_individual.nu_nis` | `character varying` | identificador social |
| NIS | `public.tl_cds_aval_elegibilidade.nu_nis_pis_pasep` | `character varying` | identificador social |
| NIS | `public.tl_cidadao.nu_nis_pis_pasep` | `character varying` | identificador social |
| Naturalizacao | `public.ta_cidadao.dt_naturalizacao` | `timestamp with time zone` | documento de naturalizacao |
| Naturalizacao | `public.ta_cidadao.nu_portaria_naturalizacao` | `character varying` | documento de naturalizacao |
| Naturalizacao | `public.tb_cds_aval_elegibilidade.ds_portaria_naturalizacao` | `character varying` | documento de naturalizacao |
| Naturalizacao | `public.tb_cds_aval_elegibilidade.dt_naturalizacao` | `timestamp with time zone` | documento de naturalizacao |
| Naturalizacao | `public.tb_cds_cad_individual.ds_portaria_naturalizacao` | `character varying` | documento de naturalizacao |
| Naturalizacao | `public.tb_cds_cad_individual.dt_naturalizacao` | `timestamp with time zone` | documento de naturalizacao |
| Naturalizacao | `public.tb_cidadao.dt_naturalizacao` | `timestamp with time zone` | documento de naturalizacao |
| Naturalizacao | `public.tb_cidadao.nu_portaria_naturalizacao` | `character varying` | documento de naturalizacao |
| Naturalizacao | `public.tb_fat_avaliacao_elegibilidade.dt_naturalizacao` | `date` | documento de naturalizacao |
| Naturalizacao | `public.tb_fat_avaliacao_elegibilidade.nu_portaria_naturalizacao` | `character varying` | documento de naturalizacao |
| Naturalizacao | `public.tb_fat_cad_individual.dt_naturalizacao` | `date` | documento de naturalizacao |
| Naturalizacao | `public.tb_fat_cad_individual.nu_portaria_naturalizacao` | `character varying` | documento de naturalizacao |
| Naturalizacao | `public.tl_cds_aval_elegibilidade.ds_portaria_naturalizacao` | `character varying` | documento de naturalizacao |
| Naturalizacao | `public.tl_cds_aval_elegibilidade.dt_naturalizacao` | `timestamp with time zone` | documento de naturalizacao |
| Naturalizacao | `public.tl_cds_cad_individual.ds_portaria_naturalizacao` | `character varying` | documento de naturalizacao |
| Naturalizacao | `public.tl_cds_cad_individual.dt_naturalizacao` | `timestamp with time zone` | documento de naturalizacao |
| Naturalizacao | `public.tl_cidadao.dt_naturalizacao` | `timestamp with time zone` | documento de naturalizacao |
| Naturalizacao | `public.tl_cidadao.nu_portaria_naturalizacao` | `character varying` | documento de naturalizacao |
| Nome cidadao | `public.ta_ativ_col_cidadao_particip.no_nome` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_ativ_col_cidadao_particip.no_nome` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_fat_avaliacao_elegibilidade.no_nome` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_fat_avaliacao_elegibilidade.no_nome_mae` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_fat_avaliacao_elegibilidade.no_nome_pai` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_fat_avaliacao_elegibilidade.no_nome_social` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_fat_cad_individual.no_nome` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_fat_cad_individual.no_nome_mae` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_fat_cad_individual.no_nome_pai` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_fat_cad_individual.no_nome_social` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Nome cidadao | `public.tb_fat_marca_consumo_alimnt.no_nome` | `character varying` | nome de pessoa nao coberto pela guideline atual |
| Obito/DO | `public.ta_ad_cidadao.co_unico_ad_cidadao_obito` | `bigint` | numero/documento de obito |
| Obito/DO | `public.ta_ad_cidadao.dt_reg_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.ta_antecedente.ds_obito_antes_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.ta_antecedente.ds_obito_apos_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.ta_cidadao.dt_obito` | `date` | numero/documento de obito |
| Obito/DO | `public.ta_cidadao.st_dados_obito_cadsus` | `integer` | numero/documento de obito |
| Obito/DO | `public.ta_cidadao_vinculacao_equipe.st_saida_cadastro_obito` | `integer` | numero/documento de obito |
| Obito/DO | `public.tb_ad_cidadao.co_unico_ad_cidadao_obito` | `bigint` | numero/documento de obito |
| Obito/DO | `public.tb_ad_cidadao.dt_reg_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.tb_antecedente.ds_obito_antes_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tb_antecedente.ds_obito_apos_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tb_cds_atend_domiciliar.st_inicio_acompanhamento_obito` | `integer` | numero/documento de obito |
| Obito/DO | `public.tb_cds_cad_individual.dt_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.tb_cds_cad_individual.nu_declaracao_obito` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tb_cidadao.dt_obito` | `date` | numero/documento de obito |
| Obito/DO | `public.tb_cidadao.st_dados_obito_cadsus` | `integer` | numero/documento de obito |
| Obito/DO | `public.tb_cidadao_vinculacao_equipe.st_saida_cadastro_obito` | `integer` | numero/documento de obito |
| Obito/DO | `public.tb_fat_cad_individual.dt_obito` | `date` | numero/documento de obito |
| Obito/DO | `public.tb_fat_cad_individual.nu_obito_do` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tl_ad_cidadao.co_unico_ad_cidadao_obito` | `bigint` | numero/documento de obito |
| Obito/DO | `public.tl_ad_cidadao.dt_reg_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.tl_antecedente.ds_obito_antes_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tl_antecedente.ds_obito_apos_primeira_semana` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tl_cds_atend_domiciliar.st_inicio_acompanhamento_obito` | `integer` | numero/documento de obito |
| Obito/DO | `public.tl_cds_cad_individual.dt_obito` | `timestamp with time zone` | numero/documento de obito |
| Obito/DO | `public.tl_cds_cad_individual.nu_declaracao_obito` | `character varying` | numero/documento de obito |
| Obito/DO | `public.tl_cidadao.dt_obito` | `date` | numero/documento de obito |
| Obito/DO | `public.tl_cidadao.st_dados_obito_cadsus` | `integer` | numero/documento de obito |
| Obito/DO | `public.tl_cidadao_vinculacao_equipe.st_saida_cadastro_obito` | `integer` | numero/documento de obito |
| Prontuario | `public.rl_antecedente_ciap.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.rl_cds_prontuario_unidade_saud.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.rl_cds_prontuario_unidade_saud.nu_prontuario_interno` | `character varying` | identificador interno |
| Prontuario | `public.ta_ad_cidadao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_agendado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_alergia.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_antecedente.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_antecedente_ciap.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_atend.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_atestado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.ta_cidadao.co_unico_cidadao_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.ta_cidadao.co_unico_prontuario` | `character varying` | identificador interno |
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
| Prontuario | `public.ta_lembrete_evolucao.dt_prontuario_lembrete` | `timestamp without time zone` | identificador interno |
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
| Prontuario | `public.ta_prontuario_unidade_saude.nu_prontuario` | `character varying` | identificador interno |
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
| Prontuario | `public.tb_cds_atend_individual.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_cds_atend_odonto.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_cds_aval_elegibilidade.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_cds_domicilio_familia.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_cds_proced.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_cds_vacinacao.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_cds_visita_domiciliar.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_cidadao.st_compartilhamento_prontuario` | `integer` | identificador interno |
| Prontuario | `public.tb_cirurgias_internacoes.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_cuidado_compartilhado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_encaminhamento.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_evolucao_odonto.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_exame_requisitado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_familia.nu_prontuario_familiar` | `character varying` | identificador interno |
| Prontuario | `public.tb_fat_atendimento_individual.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_fat_atendimento_odonto.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_fat_cad_dom_familia.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_fat_familia_territorio.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_fat_proced_atend.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_fat_vacinacao.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_fat_visita_domiciliar.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tb_guia_encaminhamento.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_historico_cabecalho.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_ivcf.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_justificativa_prontuario.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_justificativa_prontuario.dt_acesso_prontuario` | `timestamp with time zone` | identificador interno |
| Prontuario | `public.tb_lembrete.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tb_lembrete_evolucao.dt_prontuario_lembrete` | `timestamp without time zone` | identificador interno |
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
| Prontuario | `public.tb_prontuario_unidade_saude.nu_prontuario` | `character varying` | identificador interno |
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
| Prontuario | `public.tl_cds_atend_individual.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_cds_atend_odonto.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_cds_aval_elegibilidade.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_cds_domicilio_familia.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_cds_proced.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_cds_vacinacao.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_cds_visita_domiciliar.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_cidadao.co_unico_cidadao_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_cidadao.co_unico_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_cidadao.st_compartilhamento_prontuario` | `integer` | identificador interno |
| Prontuario | `public.tl_compartilhamento_prontuario.co_seq_compartilha_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_encaminhamento.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_evolucao_odonto.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_exame_requisitado.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_familia.nu_prontuario_familiar` | `character varying` | identificador interno |
| Prontuario | `public.tl_justificativa_prontuario.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_justificativa_prontuario.dt_acesso_prontuario` | `timestamp with time zone` | identificador interno |
| Prontuario | `public.tl_lembrete.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_lembrete.dt_prontuario_lembrete` | `timestamp without time zone` | identificador interno |
| Prontuario | `public.tl_lembrete_evolucao.dt_prontuario_lembrete` | `timestamp without time zone` | identificador interno |
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
| Prontuario | `public.tl_prontuario.co_unico_cidadao_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_prontuario.co_unico_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_prontuario_grupo_historico.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario_grupo_historico.co_prontuario_grupo` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario_grupo_historico.co_seq_prontuario_grpo_hstrco` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario_unidade_saude.co_seq_prontuario_unidade_saud` | `bigint` | identificador interno |
| Prontuario | `public.tl_prontuario_unidade_saude.nu_prontuario` | `character varying` | identificador interno |
| Prontuario | `public.tl_regulacao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_sinan_notificacao_evolucao.co_prontuario` | `bigint` | identificador interno |
| Prontuario | `public.tl_vacinacao.co_prontuario` | `bigint` | identificador interno |
| Registro profissional | `public.ta_atend_prof.st_registro_historico` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_atend_prof.st_registro_historico` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tb_dim_profissional.st_registro_valido` | `integer` | registro/conselho profissional |
| Registro profissional | `public.tl_atend_prof.st_registro_historico` | `integer` | registro/conselho profissional |
| Telefone | `public.ta_agend_compartilhado.nu_telefone_prof_participante` | `character varying` | contato pessoal |
| Telefone | `public.ta_cds_domicilio.nu_fone_referencia` | `character varying` | contato pessoal |
| Telefone | `public.ta_cds_domicilio.nu_fone_residencia` | `character varying` | contato pessoal |
| Telefone | `public.ta_cidadao.nu_telefone_celular` | `character varying` | contato pessoal |
| Telefone | `public.ta_cidadao.nu_telefone_contato` | `character varying` | contato pessoal |
| Telefone | `public.ta_cidadao.nu_telefone_residencial` | `character varying` | contato pessoal |
| Telefone | `public.ta_prof.nu_telefone` | `character varying` | contato pessoal |
| Telefone | `public.ta_unidade_saude.nu_telefone_comercial` | `character varying` | contato pessoal |
| Telefone | `public.ta_unidade_saude.nu_telefone_comercial2` | `character varying` | contato pessoal |
| Telefone | `public.ta_unidade_saude.nu_telefone_fax` | `character varying` | contato pessoal |
| Telefone | `public.tb_acomp_cidadaos_vinculados.nu_fone_residencial` | `character varying` | contato pessoal |
| Telefone | `public.tb_acomp_cidadaos_vinculados.nu_telefone_celular` | `character varying` | contato pessoal |
| Telefone | `public.tb_acomp_cidadaos_vinculados.nu_telefone_contato` | `character varying` | contato pessoal |
| Telefone | `public.tb_cds_aval_elegibilidade.nu_fone_referencia` | `character varying` | contato pessoal |
| Telefone | `public.tb_cds_aval_elegibilidade.nu_fone_residencia` | `character varying` | contato pessoal |
| Telefone | `public.tb_cds_cad_domiciliar.nu_fone_referencia` | `character varying` | contato pessoal |
| Telefone | `public.tb_cds_cad_domiciliar.nu_fone_residencia` | `character varying` | contato pessoal |
| Telefone | `public.tb_cds_cad_domiciliar.nu_fone_responsavel_tecnico` | `character varying` | contato pessoal |
| Telefone | `public.tb_cds_cad_individual.nu_celular_cidadao` | `character varying` | contato pessoal |
| Telefone | `public.tb_cds_domicilio.nu_fone_referencia` | `character varying` | contato pessoal |
| Telefone | `public.tb_cds_domicilio.nu_fone_residencia` | `character varying` | contato pessoal |
| Telefone | `public.tb_cidadao.nu_telefone_celular` | `character varying` | contato pessoal |
| Telefone | `public.tb_cidadao.nu_telefone_contato` | `character varying` | contato pessoal |
| Telefone | `public.tb_cidadao.nu_telefone_residencial` | `character varying` | contato pessoal |
| Telefone | `public.tb_dado_recebido_info_instalac.nu_telefone` | `character varying` | contato pessoal |
| Telefone | `public.tb_dsei.nu_telefone1` | `character varying` | contato pessoal |
| Telefone | `public.tb_dsei.nu_telefone2` | `character varying` | contato pessoal |
| Telefone | `public.tb_fat_avaliacao_elegibilidade.nu_telefone_contato` | `character varying` | contato pessoal |
| Telefone | `public.tb_fat_avaliacao_elegibilidade.nu_telefone_residencia` | `character varying` | contato pessoal |
| Telefone | `public.tb_fat_cad_domiciliar.nu_instituicao_telefone` | `character varying` | contato pessoal |
| Telefone | `public.tb_fat_cad_domiciliar.nu_telefone_contato` | `character varying` | contato pessoal |
| Telefone | `public.tb_fat_cad_domiciliar.nu_telefone_residencia` | `character varying` | contato pessoal |
| Telefone | `public.tb_fat_cad_individual.nu_celular` | `character varying` | contato pessoal |
| Telefone | `public.tb_fat_cidadao_pec.nu_telefone_celular` | `character varying` | contato pessoal |
| Telefone | `public.tb_polo_base.nu_telefone1` | `character varying` | contato pessoal |
| Telefone | `public.tb_polo_base.nu_telefone2` | `character varying` | contato pessoal |
| Telefone | `public.tb_prof.nu_telefone` | `character varying` | contato pessoal |
| Telefone | `public.tb_unidade_saude.nu_telefone_comercial` | `character varying` | contato pessoal |
| Telefone | `public.tb_unidade_saude.nu_telefone_comercial2` | `character varying` | contato pessoal |
| Telefone | `public.tb_unidade_saude.nu_telefone_fax` | `character varying` | contato pessoal |
| Telefone | `public.tl_cds_aval_elegibilidade.nu_fone_referencia` | `character varying` | contato pessoal |
| Telefone | `public.tl_cds_aval_elegibilidade.nu_fone_residencia` | `character varying` | contato pessoal |
| Telefone | `public.tl_cds_cad_domiciliar.nu_fone_referencia` | `character varying` | contato pessoal |
| Telefone | `public.tl_cds_cad_domiciliar.nu_fone_residencia` | `character varying` | contato pessoal |
| Telefone | `public.tl_cds_cad_domiciliar.nu_fone_responsavel_tecnico` | `character varying` | contato pessoal |
| Telefone | `public.tl_cds_cad_individual.nu_celular_cidadao` | `character varying` | contato pessoal |
| Telefone | `public.tl_cds_domicilio.nu_fone_referencia` | `character varying` | contato pessoal |
| Telefone | `public.tl_cds_domicilio.nu_fone_residencia` | `character varying` | contato pessoal |
| Telefone | `public.tl_cidadao.nu_telefone_celular` | `character varying` | contato pessoal |
| Telefone | `public.tl_cidadao.nu_telefone_contato` | `character varying` | contato pessoal |
| Telefone | `public.tl_cidadao.nu_telefone_residencial` | `character varying` | contato pessoal |
| Telefone | `public.tl_prof.nu_telefone` | `character varying` | contato pessoal |
| Telefone | `public.tl_unidade_saude.nu_telefone_comercial` | `character varying` | contato pessoal |
| Telefone | `public.tl_unidade_saude.nu_telefone_comercial2` | `character varying` | contato pessoal |
| Telefone | `public.tl_unidade_saude.nu_telefone_fax` | `character varying` | contato pessoal |
| Texto livre | `public.rl_antecedente_ciap.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.rl_arquivo_atendprof.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.rl_atend_obs_responsavel.co_atend_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.rl_atend_obs_responsavel.co_seq_atend_obs_responsavel` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_agendado.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_agendado.ds_outro_motivo_reserva` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_alergia_evolucao.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_antecedente.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_antecedente_ciap.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_arquivo_atendprof.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_atend_obs.co_seq_atend_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_atend_obs_plano_cuidado.co_atend_prof_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_atend_obs_plano_cuidado.co_seq_atend_obs_plano_cuidado` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_atend_obs_responsavel.co_atend_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_atend_obs_responsavel.co_seq_atend_obs_responsavel` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_atend_prof_obs.co_atend_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_atend_prof_obs.co_atend_prof_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_atend_prof_odonto.ds_observacao_rpc` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_ativ_col_observacao_cidadao.co_seq_ativ_col_obs_cidadao` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_ativ_col_observacao_cidadao.co_seq_taativcolobservacaocidd` | `bigint` | possivel texto livre |
| Texto livre | `public.ta_ativ_col_observacao_cidadao.ds_observacao` | `text` | possivel texto livre |
| Texto livre | `public.ta_atividade_coletiva.ds_outra_localidade` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_cirurgias_internacoes.ds_observacoes` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_encaminhamento.ds_observacao` | `text` | possivel texto livre |
| Texto livre | `public.ta_evolucao_odonto.ds_outro` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_exame_requisitado.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_justificativa_agenda.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_justificativa_status_ciddao.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_lista_espera.ds_observacao_saida` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_periograma_simplificado.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_problema.ds_outro` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_problema_evolucao.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_receita_medicamento.ds_observacao_interrupcao` | `text` | possivel texto livre |
| Texto livre | `public.ta_registro_vacinacao.ds_observacoes` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_requisicao_exame.ds_justificativa_procedimento` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_requisicao_exame.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_retificacao_atend.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_situacao_rua.no_outra_institucao_acompanha` | `character varying` | possivel texto livre |
| Texto livre | `public.ta_tecido_mole.ds_outro_sintomatologia` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_agendado.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_agendado.ds_outro_motivo_reserva` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_alergia_evolucao.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_antecedente.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_atend_obs.co_seq_atend_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_atend_obs_plano_cuidado.co_atend_prof_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_atend_obs_plano_cuidado.co_seq_atend_obs_plano_cuidado` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_atend_prof_obs.co_atend_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_atend_prof_obs.co_atend_prof_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_atend_prof_odonto.ds_observacao_rpc` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_ativ_col_observacao_cidadao.co_seq_ativ_col_obs_cidadao` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_ativ_col_observacao_cidadao.ds_observacao` | `text` | possivel texto livre |
| Texto livre | `public.tb_atividade_coletiva.ds_outra_localidade` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_cds_atend_individual.st_ficou_observacao` | `integer` | possivel texto livre |
| Texto livre | `public.tb_cirurgias_internacoes.ds_observacoes` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_encaminhamento.ds_observacao` | `text` | possivel texto livre |
| Texto livre | `public.tb_exame_requisitado.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_fat_atendimento_individual.co_dim_cbo_finalizador_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_fat_atendimento_individual.co_dim_equipe_finalizador_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_fat_atendimento_individual.co_dim_prof_finalizador_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_fat_atendimento_individual.co_dim_ubs_finalizador_obs` | `bigint` | possivel texto livre |
| Texto livre | `public.tb_fat_atendimento_individual.st_conduta_manter_observacao` | `integer` | possivel texto livre |
| Texto livre | `public.tb_fat_atendimento_individual.st_ficou_em_observacao` | `integer` | possivel texto livre |
| Texto livre | `public.tb_fat_atividade_coletiva.ds_outra_localidade` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_fat_cad_individual.no_outra_condicao1` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_fat_cad_individual.no_outra_condicao2` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_fat_cad_individual.no_outra_condicao3` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_historico_dados_fai.no_cbo_2002_finalizador_obs` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_historico_dados_fai.no_nome_finalizador_obs` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_historico_dados_fai.nu_cnes_finalizador_obs` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_historico_dados_fai.nu_ine_finalizador_obs` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_historico_dados_fai.st_ficou_em_observacao` | `integer` | possivel texto livre |
| Texto livre | `public.tb_justificativa_agenda.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_justificativa_prontuario.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_justificativa_status_ciddao.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_lista_espera.ds_observacao_saida` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_mchat_pergunta_outros.ds_outros` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_periograma_simplificado.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_problema.ds_outro` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_problema_evolucao.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_proced_solicitado.ds_observacao_execucao` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_receita_medicamento.ds_observacao_interrupcao` | `text` | possivel texto livre |
| Texto livre | `public.tb_registro_vacinacao.ds_observacoes` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_regulacao_evolucao.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_requisicao_exame.ds_justificativa_procedimento` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_requisicao_exame.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_retificacao_atend.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_situacao_rua.no_outra_institucao_acompanha` | `character varying` | possivel texto livre |
| Texto livre | `public.tb_tecido_mole.ds_outro_sintomatologia` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_agendado.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_agendado.ds_outro_motivo_reserva` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_antecedente.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_atend_prof_odonto.ds_observacao_rpc` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_cds_atend_individual.st_ficou_observacao` | `integer` | possivel texto livre |
| Texto livre | `public.tl_encaminhamento.ds_observacao` | `text` | possivel texto livre |
| Texto livre | `public.tl_evolucao_odonto.ds_outro` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_exame_requisitado.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_justificativa_agenda.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_justificativa_prontuario.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_justificativa_status_ciddao.ds_justificativa` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_problema.ds_outro` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_problema_evolucao.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_proced_solicitado.ds_observacao_execucao` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_registro_vacinacao.ds_observacoes` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_regulacao_evolucao.ds_observacao` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_requisicao_exame.ds_justificativa_procedimento` | `character varying` | possivel texto livre |
| Texto livre | `public.tl_requisicao_exame.ds_observacao` | `character varying` | possivel texto livre |

## Coberto

| Categoria | Coluna | Tipo | Detalhe |
|---|---|---|---|
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
| Data registro | `public.tb_fat_atendimento_individual.dt_final_atendimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_atendimento_individual.dt_inicial_atendimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_atendimento_odonto.dt_final_atendimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_atendimento_odonto.dt_inicial_atendimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_cuidado_compartilhado.dt_criacao_cuidado` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_cuidado_compartilhado.dt_evolucao` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_cuidado_compartilhado.dt_evolucao_anterior` | `timestamp without time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_proced_atend.dt_final_atendimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_proced_atend.dt_inicial_atendimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_vacinacao.dt_final_atendimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| Data registro | `public.tb_fat_vacinacao.dt_inicial_atendimento` | `timestamp with time zone` | 04_anon_datas_cidadao |
| E-mail | `public.ta_agend_compartilhado.ds_email_prof_participante` | `character varying` | 03_anon_email |
| E-mail | `public.ta_cidadao.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.ta_credencial_integracao.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.ta_prof.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.ta_servidor_smtp.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.ta_sistema_externo.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.ta_unidade_saude.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_cds_aval_elegibilidade.ds_email_cidadao` | `character varying` | 03_anon_email |
| E-mail | `public.tb_cds_cad_individual.ds_email_cidadao` | `character varying` | 03_anon_email |
| E-mail | `public.tb_cidadao.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_credencial_integracao.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_dado_recebido_info_instalac.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_dsei.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_dsei.ds_email_chefe` | `character varying` | 03_anon_email |
| E-mail | `public.tb_fat_avaliacao_elegibilidade.no_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_fat_cad_individual.no_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_polo_base.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_polo_base.ds_email_chefe` | `character varying` | 03_anon_email |
| E-mail | `public.tb_prof.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_servidor_smtp.ds_email` | `character varying` | 03_anon_email |
| E-mail | `public.tb_sistema_externo.ds_email` | `character varying` | 03_anon_email |
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
| Endereco | `public.ta_cidadao.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_cidadao.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_prof.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.ta_unidade_saude.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.ds_complemento_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.no_logradouro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_cad_domiciliar.nu_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cds_domicilio.no_logradouro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_cidadao.no_bairro_filtro` | `character varying` | 06_anon_endereco |
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
| Endereco | `public.tb_unidade_saude.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tb_unidade_saude.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.ds_complemento_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.no_logradouro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_cad_domiciliar.nu_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cds_domicilio.no_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_cidadao.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_prof.no_bairro_filtro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.ds_cep` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.ds_complemento` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.ds_logradouro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.ds_ponto_referencia` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.no_bairro` | `character varying` | 06_anon_endereco |
| Endereco | `public.tl_unidade_saude.no_bairro_filtro` | `character varying` | 06_anon_endereco |
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

## Declarado nas migrations, ausente no banco

Nenhuma coluna declarada ficou ausente.

## Historico de declarados ausentes removidos

Colunas que ja estiveram declaradas nas migrations, mas nao existiam no banco auditado.
Foram mantidas aqui apenas como historico de reconciliacao do schema.

| Migration | Coluna |
|---|---|
| 03_anon_email | `public.tb_cidadao.no_email` |
| 01_anon_cpf | `public.tb_dim_cidacao_pec_grupo.co_identificacao` |
| 05_anon_profissional | `public.tb_dim_profissional.nu_registro` |
| 05_anon_profissional | `public.tb_dim_profissional.nu_registro_conselho` |
| 05_anon_profissional | `public.tb_dim_profissional.nu_registro_profissional` |
| 02_anon_unidade_saude | `public.tb_estabelecimento.no_estabelecimento` |
| 04_anon_datas_cidadao | `public.tb_fat_atd_ind_procedimentos.dt_nascimento` |
| 04_anon_datas_cidadao | `public.tb_fat_atend_odonto_exames.dt_nascimento` |
| 04_anon_datas_cidadao | `public.tb_fat_atend_odonto_proced.dt_nascimento` |
| 04_anon_datas_cidadao | `public.tb_fat_ivcf.dt_nascimento` |
| 03_anon_email | `public.tb_pessoa_fisica.no_email` |
| 01_anon_cpf | `public.tb_pessoa_fisica.nu_cpf` |
| 05_anon_profissional | `public.tb_prof.no_profissional` |
| 05_anon_profissional | `public.tb_prof.nu_registro` |
| 05_anon_profissional | `public.tb_prof.nu_registro_conselho` |
| 05_anon_profissional | `public.tb_prof.nu_registro_profissional` |
