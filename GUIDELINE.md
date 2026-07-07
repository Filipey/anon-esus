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
| Nome da unidade de saúde | Substituída pela denominação genérica `Unidade de Saúde 1`, `Unidade de Saúde 2`, ... | Implementado em `02_anon_unidade_saude.py`, mas hoje aponta para `tb_unidade_saude`/`tb_estabelecimento` (schema operacional). O mapeamento em `docs/mapeamento_colunas.tsv` referencia `tb_dim_unidade_saude` (schema do Data Warehouse) — **schemas diferentes, reconciliar**. |
| Endereço IP das máquinas que acessaram | Será excluído. | Pendente. |
| Vinculação da unidade de saúde com profissionais de saúde e cidadãos do território | Deve ser preservada, a despeito do nome fictício genérico da Unidade de Saúde. | Preservada por construção: as migrations substituem apenas a coluna de nome/rótulo e não tocam chaves substitutas (`co_dim_unidade_saude`, `nu_cnes_vinc_equipe` etc.) usadas nos joins. Validar com teste de integridade referencial dedicado. |
| Vinculação da unidade de saúde a equipe multiprofissional | Deve ser preservada, a despeito do nome fictício genérico da Unidade de Saúde. | Mesma observação acima. |
| Categoria e registro profissional | Categoria e registros de saúde preservados. Nome fictício com sobrenome "Teste", escolhido entre nomes representativos de diversos gêneros (evitar viés psicodemográfico). Registro profissional substituído por `99999`. | Pendente. |
| CPF do profissional de saúde | Substituído por CPF fictício, válido, gerado aleatoriamente. | Implementado em `01_anon_cpf.py` (`tb_prof.nu_cpf`, schema operacional). As colunas de CPF do DW (`nu_cpf_cidadao` em 19 tabelas `tb_fat_*`/`tb_dim_*`, ver TSV) ainda não estão cobertas. |
| CPF do cidadão | Substituído por CPF fictício, válido, gerado aleatoriamente. | Implementado em `01_anon_cpf.py` (`tb_cidadao.nu_cpf`, `tb_cidadao.nu_cpf_responsavel`, `tb_pessoa_fisica.nu_cpf`, schema operacional). Mesma lacuna do DW acima. |
| Data de nascimento / idade do cidadão | O dia de nascimento substituído por número aleatório de 1 a 30/31. Mês e ano preservados. A data de cada atendimento deve ser redimensionada para preservar o número de dias entre nascimento e atendimento. | Pendente. Exige sincronização com todas as datas de atendimento do mesmo cidadão (ver também "Data-hora dos registros de saúde" abaixo). |
| Sexo do cidadão | Não será modificado, para manter coerência com condições clínicas específicas (gravidez, ciclos menstruais, menopausa, câncer de próstata, hemofilia, daltonismo, distrofia muscular de Duchenne, agamaglobulinemia ligada ao X, entre outras). | Não se aplica — nenhuma migration deve tocar esse campo. |
| E-mail do cidadão | Substituído pelo termo genérico `cidadao@teste.br`. | Implementado em `03_anon_email.py` (`tb_cidadao.no_email`, `tb_pessoa_fisica.no_email`, schema operacional). As colunas de e-mail do DW (`tb_fat_avaliacao_elegibilidade.no_email`, `tb_fat_cad_individual.no_email`) ainda não estão cobertas. |
| Endereço do cidadão | Substituído por outro endereço válido do mesmo município, obtido aleatoriamente entre os endereços existentes na base. | Pendente. |
| Dados antropométricos extremos | Em investigação: microagregação, truncamento (ex.: limitar altura máxima) ou ruído controlado (Differential Privacy). | Pendente — próximo passo de pesquisa. |
| Doenças raras, dados genéticos | Substituídos por conjunto de dados artificiais que preserva propriedades estatísticas e correlações sintoma × doença da base real, sem corresponder a pacientes reais. | Pendente. |
| Documentos em PDF (receitas, atestados, orientações, encaminhamentos) | Excluídos. | Pendente. |
| Documentos clínicos anexados em SOAP / Objetivo (exames, imagens, PDF/JPEG/JPG/PNG/DICOM) | Excluídos. | Pendente. |
| Textos livres | Anonimização por reconhecimento de entidades nomeadas (NER). | Pendente — próximo passo de pesquisa, ver `PIPELINE.md`. |
| Data-hora dos registros de saúde | Sincronizada com as modificações na data de nascimento do cidadão. A temporalidade entre registros longitudinais de um mesmo cidadão deve ser preservada para manter a coerência da evolução clínica. | Pendente. |
| Logs de acesso (data/hora, relatórios visualizados) | Excluídos. | Pendente. |

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

**Decisão de escopo:** esse mapeamento documenta o schema do **Data
Warehouse** (`tb_fat_*`, `tb_dim_*`, `tb_acomp_*`), enquanto as migrations
implementadas hoje (`01_anon_cpf.py`, `02_anon_unidade_saude.py`,
`03_anon_email.py`) têm suas listas de colunas (`CPF_COLUMNS`,
`NAME_COLUMNS`, `EMAIL_COLUMNS`) apontando para o schema **operacional**
(`tb_cidadao`, `tb_prof`, `tb_pessoa_fisica`, `tb_unidade_saude`,
`tb_estabelecimento`). Nenhuma das 60 linhas do TSV corresponde às colunas
hoje hardcoded. A anonimização deve valer para **as duas camadas**: a
instância é de treinamento e todo o banco compõe o e-SUS, então as listas
`*_COLUMNS` de cada migration precisam ser expandidas para cobrir também as
tabelas do DW — não é uma escolha entre uma camada ou outra.

O catálogo completo de domínios de Fato/Dimensão do DW e o que já foi
revisado está em
[`docs/catalogo_dw_tabelas.md`](docs/catalogo_dw_tabelas.md). Como a
estrutura do DW é documentação pública, a proteção não depende de esconder
nomes de tabela/coluna — depende de nenhum valor de célula sobreviver sem
tratamento, então fechar a cobertura desse catálogo é prioridade antes de
considerar a pipeline completa.

A categoria "Referência unidade de saúde" (35 linhas) marca colunas que são
apenas chaves substitutas (`co_dim_unidade_saude`, `nu_cnes_vinc_equipe`
etc.), não o nome da unidade — não devem ser alteradas, só usadas para
confirmar que o join com `tb_dim_unidade_saude` continua íntegro após a
anonimização do nome.
