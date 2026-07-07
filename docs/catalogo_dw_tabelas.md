# Catálogo de tabelas do Data Warehouse Relatórios e-SUS APS PEC

Lista oficial de domínios de Fato e Dimensão do DW, publicada em
<https://integracao.esusaps.bridge.ufsc.tech/dw/index.html> (prefixos
`tb_fat_` e `tb_dim_`, documentação pública). Cruzada com
[`mapeamento_colunas.tsv`](mapeamento_colunas.tsv) para indicar quais
domínios já tiveram colunas sensíveis identificadas e quais ainda não foram
revisados.

**Decisão de escopo:** a anonimização vale para as duas camadas: schema
operacional e DW, já que a instância de treinamento reúne toda a base do
e-SUS. Como a estrutura do DW é documentação pública, a proteção não vem de
esconder nomes de tabela/coluna, e sim de garantir que nenhum valor de
célula sobreviva sem tratamento; por isso a cobertura completa deste
catálogo importa mais do que a princípio pareceria.

## Fatos (`tb_fat_*`)

| Domínio (fonte oficial) | Tabela(s) já identificada(s) | Revisado? |
|---|---|---|
| Cadastro individual | `tb_fat_cad_individual` | Sim — CPF, e-mail, nome (cidadão/mãe/pai/social), endereço não encontrado nesta tabela (está em `tb_fat_cad_domiciliar`), texto livre e campos sem categoria na guideline (telefone, NIS, DO, naturalização). |
| Cadastro domiciliar | `tb_fat_cad_domiciliar`, `tb_fat_cad_dom_familia` | Sim — endereço completo e campos sem categoria na guideline (telefone, dados de instituição, prontuário). |
| Atendimento individual | `tb_fat_atendimento_individual`, `tb_fat_atd_ind_exames`, `tb_fat_atd_ind_medicamentos`, `tb_fat_atd_ind_problemas`, `tb_fat_atd_ind_procedimentos`, `tb_fat_consolidado_cidadao_fai` | Sim (CPF, data de nascimento, antropometria, data-hora de registro). |
| Atendimento odontológico | `tb_fat_atendimento_odonto`, `tb_fat_atend_odonto_encaminham`, `tb_fat_atend_odonto_exames`, `tb_fat_atend_odonto_medicament`, `tb_fat_atend_odonto_problemas`, `tb_fat_atend_odonto_proced`, `tb_fat_consolidado_cidadao_fao` | Sim (CPF, data de nascimento, antropometria, data-hora de registro, prontuário). |
| Atividade coletiva | `tb_fat_atividade_coletiva` e afins | Revisado — nenhuma coluna sensível encontrada além de referência de unidade (só flags de participação). |
| Procedimentos | `tb_fat_proced_atend`, `tb_fat_proced_atend_proced`, `tb_fat_procedimento`, `tb_fat_consolidado_cidadao_fp` | Sim (CPF, data de nascimento, antropometria, data-hora, prontuário). `tb_fat_procedimento` em si segue só com contadores, sem CPF direto. |
| Visita domiciliar | `tb_fat_visita_domiciliar` | Revisado — sem coluna sensível nova além de `nu_prontuario` (sem categoria na guideline). |
| Marcadores de consumo alimentar | `tb_fat_marca_consumo_alimnt` | Sim (CPF, data de nascimento). |
| Avaliação de elegibilidade | `tb_fat_avaliacao_elegibilidade` | Sim — e-mail, nome (cidadão/mãe/pai/social), endereço completo, campos sem categoria na guideline (telefone, NIS, naturalização). |
| Atendimento domiciliar | `tb_fat_atendimento_domiciliar`, `tb_fat_atend_dom_condicao_aval`, `tb_fat_atend_dom_proced` | Revisado — sem coluna sensível nova (só flags de condição avaliada). |
| Síndrome neurológica por Zika / Microcefalia | `ficha_complementar.html` | **Bloqueado.** A página não tem seção de estrutura de colunas do DW, só aponta para o dicionário LEDI externo (nomenclatura diferente, camelCase). Nome real da(s) tabela(s) `tb_fat_*` e colunas não confirmados — requer revisão manual adicional. |
| Vacinação | `vacinacao.html` | **Bloqueado.** Mesma limitação: sem seção de estrutura no DW, só link para dicionário LEDI (`headerTransport`, `lote`, etc.). Provavelmente contém CPF/data de nascimento/dados de profissional, mas os nomes de coluna DW não puderam ser confirmados. |
| Cuidado compartilhado | `tb_fat_cuidado_compartilhado` | Sim (CPF, data de nascimento, datas de evolução). |
| IVCF-20 | `tb_fat_ivcf` | Sim (CPF, data-hora de resultado). |

Restam **2 domínios bloqueados** por limitação da própria documentação (Zika/
Microcefalia e Vacinação — ver observação acima), não por falta de revisão.
Todos os demais 12 domínios de fato foram revisados.

## Dimensões (`tb_dim_*`)

A documentação oficial lista ~40 dimensões (aleitamento materno, CATMAT,
CBO, CIAP-2, CID-10, classificação de risco, condutas AD, condutas cuidado
compartilhado, cuidador, desfecho de visitas, periodicidade/dose de
imunobiológico, unidade de medida de tratamento, equipes, especialidades,
estratégia de vacinação, etnia, faixa etária, forma farmacêutica, frequência
de alimentação, graus IVCF-20, grupo de atendimento, identidade de gênero,
imunobiológico, estabelecimentos INEP, local de atendimento, modalidade AD,
município, nacionalidade, país, práticas integrativas, povo/comunidade
tradicional, prioridade cuidado compartilhado, procedências AD,
procedimentos, **profissionais**, raça e cor, racionalidade em saúde, sexo,
unidade de saúde). A maioria é tabela de referência/lookup (CID-10, CBO,
município etc.) e não deve conter dado identificável por si — o risco está
nas dimensões que descrevem **pessoas**.

| Domínio | Tabela já identificada | Revisado? |
|---|---|---|
| Unidade de saúde | `tb_dim_unidade_saude` | Sim (nome, CNES). |
| Profissionais | `tb_dim_profissional` | Revisado — tem `no_profissional` (nome) e `nu_cns` (CNS, não CPF); **não** tem CPF nem registro de conselho documentados no DW. A orientação "Categoria e registro profissional" da guideline pode não ser aplicável nesta camada — confirmar se esses dados só existem no schema operacional. |
| Cuidador | `tb_dim_cuidador` | Revisado — armazena só o **grau de relacionamento** (mãe, pai, cônjuge...), não identificação de uma pessoa cuidadora. Sem dado sensível. |
| Equipes | `tb_dim_equipe` | Revisado — `no_equipe` é nome da equipe de saúde (CNES), não nome de pessoa. Sem dado sensível. |
| Demais ~40 dimensões (lookup/taxonomia: CBO, CID-10, CATMAT, sexo, raça/cor, país, município etc.) | — | Revisadas (42 de 44 páginas de dimensão auditadas) — nenhuma continha dado de pessoa; são vocabulário controlado. |

Duas tabelas aparecem no `mapeamento_colunas.tsv` sem corresponder a nenhum
domínio da lista oficial acima: `tb_dim_cidacao_pec_grupo` e
`tb_dim_agrupador_filtro`. Provavelmente dimensões internas/auxiliares do DW
não descritas na página pública de domínios — vale confirmar diretamente no
schema físico.

## Achados da revisão completa (2026-07-07)

Todas as tabelas de Fato (exceto as duas bloqueadas) e todas as 44
dimensões foram revisadas. Resultado consolidado em
[`mapeamento_colunas.tsv`](mapeamento_colunas.tsv) (144 linhas). Três
achados relevantes que não estavam previstos:

1. **Nome do cidadão não é coberto pela guideline.** `tb_fat_cad_individual`
   e `tb_fat_avaliacao_elegibilidade` guardam `no_nome`, `no_nome_mae`,
   `no_nome_pai` e `no_nome_social` do cidadão. A guideline atual só define
   regra para nome de profissional e de unidade de saúde. Falta decidir a
   ação para nome do cidadão (categoria `Nome cidadão` no TSV).
2. **CNS aparece ao lado do CPF em praticamente todas as tabelas**, mas a
   guideline só fala de CPF. Como CNS é outro identificador nacional único
   (formato e dígito verificador próprios, diferente de CPF), substituí-lo
   corretamente exige um gerador de CNS válido, hoje não documentado nem
   implementado. Não enumerado coluna a coluna no TSV (ocorrência ampla
   demais para uma revisão pontual); precisa de um passe dedicado.
3. **Vacinação e Zika/Microcefalia (`ficha_complementar`) não têm página de
   estrutura no formato do DW**, só linkam para o dicionário LEDI externo
   (nomenclatura camelCase diferente). Prováveis candidatas a CPF/data de
   nascimento/dados de profissional, mas não confirmadas.

21 colunas adicionais (telefone, NIS, número de óbito/DO, portaria de
naturalização, dados de instituição de acolhimento, número de prontuário)
foram registradas no TSV sob a categoria `Sem categoria na guideline`, mas
são claramente dado pessoal, mas a guideline hoje não define uma ação para
elas.

## Cobertura de texto livre

Esta revisão (Fatos + Dimensões) mirou **dados estruturados**: colunas
tabulares que batem 1:1 com uma categoria da guideline (CPF, e-mail,
endereço, data etc.). Ela **não é** um censo de campos de texto livre, a
orientação "Textos livres → anonimização por NER" do `GUIDELINE.md` é uma
frente à parte, ainda não sistematicamente inventariada.

O que se sabe até aqui:

- Os únicos campos de texto livre encontrados incidentalmente foram 5
  colunas de `tb_fat_cad_individual` (`no_causa_internacao12`,
  `no_outra_condicao1/2/3`, `no_plantas_medicinais` — já registradas no TSV
  sob a categoria `Texto livre`).
- As tabelas de encontro clínico revisadas em detalhe (`tb_fat_atendimento_
  individual`, `tb_fat_atendimento_odonto`, `tb_fat_atd_ind_*`,
  `tb_fat_atend_odonto_*`) **não expuseram nenhuma coluna de narrativa
  clínica** (evolução, anamnese, queixa, SOAP) na estrutura documentada do
  DW — só campos codificados/numéricos e as datas/antropometria já
  registradas.
- Isso sugere (mas não confirma) que o texto livre clínico — evolução
  SOAP, anamnese, queixa principal — pode existir **apenas no schema
  operacional** (PEC), sem ser replicado para o DW de relatórios, já que o
  DW é otimizado para agregação, não para narrativa. Se for esse o caso, o
  trabalho de NER precisa mirar o banco operacional, não o DW.

**Ainda não feito:** um levantamento dedicado de texto livre precisa (1)
confirmar no schema físico se colunas de narrativa clínica existem no
operacional e quais tabelas as guardam, e (2) revisar se o DW replica
algum campo de observação/texto em outros domínios não cobertos aqui (ex.:
campos de observação em `tb_fat_visita_domiciliar`, `tb_fat_atendimento_
domiciliar`, `tb_fat_cuidado_compartilhado`, cujas páginas foram revisadas
para PII estruturado mas não teve uma varredura dedicada a texto livre).
Esse levantamento é pré-requisito para a etapa de NER mencionada no
`PIPELINE.md`.

## Próximo passo sugerido

1. Decidir a ação para as categorias novas (`Nome cidadão`, `Sem categoria
   na guideline`) e atualizar o `GUIDELINE.md`.
2. Decidir o tratamento do CNS (gerador dedicado, ou reaproveitar o
   crosswalk do CPF) e então mapear sua ocorrência nas demais tabelas.
3. Revisar manualmente `vacinacao.html` e `ficha_complementar.html` (via
   dicionário LEDI) para confirmar nomes de tabela/coluna reais.
4. Com o mapeamento fechado, expandir `CPF_COLUMNS`/`NAME_COLUMNS`/
   `EMAIL_COLUMNS` (e novas migrations) em `scripts/` para cobrir também o
   schema do DW.
