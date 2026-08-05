# Guideline de Anonimização — e-SUS APS/PEC

Diretrizes de anonimização definidas para o projeto, por dado sensível e por
perfil de ciclo de vida. O inventário de tabelas/colunas correspondente está
em [`docs/mapeamento_colunas.tsv`](docs/mapeamento_colunas.tsv). Ver
[`PIPELINE.md`](PIPELINE.md) para a implementação das migrations.

A coluna **Status** indica se a orientação já está coberta pelas migrations
em `scripts/`, e aponta lacunas conhecidas.

## Dados sensíveis

| Dado sensível | Orientação para o algoritmo | Status na pipeline |
|---|---|---|
| Nome da unidade de saúde | Substituída pela denominação genérica `Unidade de Saúde 1`, `Unidade de Saúde 2`, ... | Implementado em `02_anon_unidade_saude.py` para schema operacional e DW (`tb_dim_unidade_saude.no_unidade_saude`). A mesma migration também troca o CNES por um código fictício de 7 dígitos — sem isso, o CNES sozinho reidentificava a unidade mesmo com o nome genérico. |
| Endereço IP das máquinas que acessaram | Será excluído. | Implementado em `12_anon_ip_logs.py` (`tb_historico_acesso.co_ip`, tabela removida por completo). |
| Vinculação da unidade de saúde com profissionais de saúde e cidadãos do território | Deve ser preservada, a despeito do nome fictício genérico da Unidade de Saúde. | Preservada por construção: as migrations substituem apenas a coluna de nome/rótulo e não tocam chaves substitutas (`co_dim_unidade_saude`, `nu_cnes_vinc_equipe` etc.) usadas nos joins. Validar com teste de integridade referencial dedicado. |
| Vinculação da unidade de saúde a equipe multiprofissional | Deve ser preservada, a despeito do nome fictício genérico da Unidade de Saúde. | Mesma observação acima. |
| Categoria e registro profissional | Categoria e registros de saúde preservados. Nome fictício com sobrenome "Teste", escolhido entre nomes representativos de diversos gêneros (evitar viés psicodemográfico). Registro profissional substituído por `99999`. | Implementado em `05_anon_profissional.py` (`no_profissional`/`no_civil_profissional`/`no_social_profissional` e `nu_conselho_classe` em `tb_prof` **e** em `tb_atend_prof`, o "retrato" do profissional no momento do atendimento — as duas cópias do registro confirmadas na auditoria real). Nomes ficam alternados por gênero na ordenação alfabética, não pelo gênero real de cada profissional — `ta_prof`/`tb_prof.no_sexo` (e `tl_prof.co_sexo`) existem de fato e não são considerados, podendo gerar incoerência (nome feminino com sexo=M) — ainda não corrigido. CNS (`nu_cns`) tratado à parte, ver linha própria abaixo. |
| CPF do profissional de saúde | Substituído por CPF fictício, válido, gerado aleatoriamente. | Implementado em `01_anon_cpf.py` (`tb_prof.nu_cpf`, confirmado na auditoria real). |
| CPF do cidadão | Substituído por CPF fictício, válido, gerado aleatoriamente. | Implementado em `01_anon_cpf.py` — 92 colunas confirmadas na auditoria real (`docs/auditoria_schema.md`), cobrindo schema operacional e DW. |
| Nome do cidadão | *(Não coberto pela guideline original.)* | Implementado em `09_anon_nome_cidadao.py` — 11 colunas confirmadas na auditoria (`no_nome`, `no_nome_mae`, `no_nome_pai`, `no_nome_social`). Nome fictício comum, sem sobrenome fixo (essa regra é só para profissional). Fechado porque CPF e e-mail já eram anonimizados mas o nome completo sobrevivia em texto claro. |
| CNS (Cartão Nacional de Saúde) — cidadão e profissional | *(Não coberto pela guideline original.)* | **Medida provisória** em `10_anon_cns.py`: hash determinístico salgado (~92 colunas), igual ao dado antropométrico — decisão explícita de não implementar gerador de CNS válido nesta fase, por não haver biblioteca pronta (diferente do CPF) e o esforço de implementar o dígito verificador do zero não ser prioridade agora. |
| Data de nascimento / idade do cidadão | O dia de nascimento substituído por número aleatório de 1 a 30/31. Mês e ano preservados. A data de cada atendimento deve ser redimensionada para preservar o número de dias entre nascimento e atendimento. | Implementado em `04_anon_datas_cidadao.py`. As colunas de registro/atendimento agora são **descobertas em tempo de execução** (não mais uma lista curada à mão) — a versão anterior só sincronizava 5 de ~53 tabelas declaradas, o que quebrava esta própria garantia. 9 tabelas de detalhe sem `dt_nascimento` própria (`tb_fat_atd_ind_*`, `tb_fat_atend_odonto_*`) recebem o delta via join com `tb_cidadao` (`SATELLITE_TABLES`). |
| Sexo do cidadão | Não será modificado, para manter coerência com condições clínicas específicas (gravidez, ciclos menstruais, menopausa, câncer de próstata, hemofilia, daltonismo, distrofia muscular de Duchenne, agamaglobulinemia ligada ao X, entre outras). | Não se aplica — nenhuma migration deve tocar esse campo. |
| E-mail do cidadão | Substituído pelo termo genérico `cidadao@teste.br`. | Implementado em `03_anon_email.py` (`PERSONAL_EMAIL_COLUMNS`). E-mail institucional (unidade/DSEI/polo base) foi separado para `GENERIC_INSTITUTIONAL_EMAIL` — usar o placeholder de cidadão num contato institucional era uma inconsistência, não anonimização. |
| Endereço do cidadão | Substituído por outro endereço válido do mesmo município, obtido aleatoriamente entre os endereços existentes na base. | Implementado em `06_anon_endereco.py`, incluindo número da casa (`nu_numero`/`nu_domicilio` + `st_sem_numero`) e coordenadas (`nu_latitude`/`nu_longitude` nas tabelas de domicílio) no mesmo conjunto atômico trocado — confirmados na auditoria real; antes ficavam de fora e sobreviviam com o valor original junto ao endereço novo. A migration só atua quando encontra coluna de município na tabela, para não misturar municípios. |
| Dados antropométricos extremos | Em investigação: microagregação, truncamento (ex.: limitar altura máxima) ou ruído controlado (Differential Privacy). | **Medida provisória** em `08_anon_antropometrico.py`: todo o campo (não só os extremos) recebe um hash determinístico até o DP ser definido. Não é proteção robusta — campo numérico de baixa cardinalidade é vulnerável a força bruta sobre o hash. DP propriamente dito fica para a fase 2. |
| Doenças raras, dados genéticos | Substituídos por conjunto de dados artificiais que preserva propriedades estatísticas e correlações sintoma × doença da base real, sem corresponder a pacientes reais. | **Decisão explícita: fase 2.** Exige geração sintética correlacionada (pesquisa própria), não uma migration de substituição de coluna — mesmo grupo do NER e do DP real. |
| Documentos em PDF (receitas, atestados, orientações, encaminhamentos) | Excluídos. | Implementado em `07_anon_documentos.py` (conteúdo binário e nome de arquivo colocados em `NULL`). |
| Documentos clínicos anexados em SOAP / Objetivo (exames, imagens, PDF/JPEG/JPG/PNG/DICOM) | Excluídos. | Implementado em `07_anon_documentos.py`, mesma migration acima. |
| Textos livres | Anonimização por reconhecimento de entidades nomeadas (NER). | **Decisão explícita: fase 2.** A auditoria real encontrou 106 colunas candidatas no schema operacional (`ds_observacao`, `ds_justificativa` etc.) — confirma que texto livre clínico vive no operacional, não no DW. |
| Data-hora dos registros de saúde | Sincronizada com as modificações na data de nascimento do cidadão. A temporalidade entre registros longitudinais de um mesmo cidadão deve ser preservada para manter a coerência da evolução clínica. | Implementado em `04_anon_datas_cidadao.py` — ver nota na linha "Data de nascimento" acima sobre a correção da descoberta automática. |
| Logs de acesso (data/hora, relatórios visualizados) | Excluídos. | Implementado em `12_anon_ip_logs.py`: `tb_auditoria_processo`, `tb_envio_log`, `tb_historico_acesso`, `tb_sessao_sincronizacao`, `tb_ad_transmissao_sessao` removidas por completo; `tb_auditoria_evento` só tem as colunas zeradas (preserva a linha) porque uma FK de `tb_retificacao_atend` aponta para ela. |
| *(sem categoria na guideline original)* Prontuário, telefone, NIS, naturalização, número de documento de óbito, identificação mista (CPF/CNS no mesmo campo) | *(Campos pessoais encontrados na auditoria real sem ação definida na guideline.)* | Implementado em `11_anon_identificadores_diversos.py`: hash determinístico para prontuário/NIS/naturalização/óbito/identificação mista, Faker para telefone, e a data de naturalização reduzida a 1º de janeiro do ano. Identificação mista não garante bater com o valor fictício já usado em `01`/`10` para a mesma pessoa (simplificação aceita nesta fase). |

## Ciclo de vida / perfis

Restrições de plausibilidade biológica e epidemiológica a respeitar ao gerar
ou ajustar dados sintéticos por perfil de cidadão. Ainda não implementadas —
relevantes para as etapas de NER/DP e para uma eventual geração de população
sintética.

| Perfil | Especificidades / orientações para o algoritmo |
|---|---|
| Criança | Dados de crescimento e desenvolvimento infantil devem ter temporalidade preservada, em sintonia com os ajustes no dia do mês de nascimento e entre os registros de uma mesma criança ao longo do tempo. |
| Adolescente | Puberdade (menarca, telarca, pubarca) deve ter idades biologicamente plausíveis (ex.: menarca entre 9–15 anos) e associada ao sexo genético. |
| Adulto | (1) Doenças crônicas não transmissíveis com prevalência crescente com a idade. (2) Correlação epidemiológica entre doenças (ex.: obesidade e hipertensão). (3) Doenças relacionadas a sexo e idade (ex.: hiperplasia prostática em homens acima de 40 anos). |
| Gestante | Dados de gestação (motivo de consulta, diagnósticos, exames específicos, testes de gravidez, ultrassom obstétrico) só podem ocorrer em cidadão com sexo genético feminino e idade entre 10 e 55 anos. Intervalo entre gestações consecutivas não pode ser menor que 9 meses (parto) ou 3 meses (aborto). Pode ocorrer com identidade de gênero mulher cisgênero, homem transgênero, travesti, não-binário ou outras, desde que o sexo genético seja feminino. |
| Climatério feminino | Dados de menopausa (motivo de consulta, diagnóstico) só podem ocorrer em cidadão com sexo genético feminino e idade entre 40 e 55 anos. Pode ocorrer com identidade de gênero mulher cisgênero, homem transgênero, travesti, não-binário ou outras, desde que o sexo genético seja feminino. |

## Mapeamento de tabelas/colunas

O inventário detalhado de tabelas e colunas identificadas na documentação do
Data Warehouse Relatórios e-SUS APS PEC está em
[`docs/mapeamento_colunas.tsv`](docs/mapeamento_colunas.tsv) (categoria,
tabela, coluna, descrição, ação sugerida, fonte, observação).

**Decisão de escopo (resolvida):** a anonimização vale para as duas
camadas — schema operacional e Data Warehouse — já que a instância é de
treinamento e todo o banco compõe o e-SUS. Todas as migrations em
`scripts/` hoje cobrem ambas as camadas, com as listas de colunas
confirmadas contra o schema físico real em
[`docs/auditoria_schema.md`](docs/auditoria_schema.md) (gerado por
`scripts/audit_schema.py`) — não mais só contra a documentação pública do
DW. Esse arquivo tem precedência sobre `mapeamento_colunas.tsv` (que
documentava só o DW, via documentação pública) quando os dois divergirem.

O catálogo completo de domínios de Fato/Dimensão do DW está em
[`docs/catalogo_dw_tabelas.md`](docs/catalogo_dw_tabelas.md). Como a
estrutura do DW é documentação pública, a proteção não depende de esconder
nomes de tabela/coluna — depende de nenhum valor de célula sobreviver sem
tratamento.

A categoria "Referência unidade de saúde" no TSV marca colunas que são
apenas chaves substitutas (`co_dim_unidade_saude`, `nu_cnes_vinc_equipe`
etc.), não o nome da unidade — não devem ser alteradas, só usadas para
confirmar que o join com `tb_dim_unidade_saude` continua íntegro após a
anonimização do nome. O mesmo raciocínio vale para as ~124 colunas
`bigint`/flag da categoria "Prontuario" na auditoria real — só as 33
colunas `character varying` (`nu_prontuario` e variantes) guardam o
identificador de fato, e são as únicas tratadas em
`11_anon_identificadores_diversos.py`.
