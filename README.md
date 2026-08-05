# anon-esus

Pipeline de anonimização operacional para dados do e-SUS APS/PEC, usada
para produzir uma instância de treinamento anonimizada a partir da base
real, no contexto do projeto de população sintética do e-SUS.

## Objetivo

Transformar uma base e-SUS (schema operacional + Data Warehouse de
relatórios) numa base equivalente sem dado identificável, preservando o
que for necessário para a base continuar útil para pesquisa: vínculos
entre tabelas, coerência temporal entre registros de um mesmo cidadão, e
plausibilidade clínica/epidemiológica por perfil (criança, gestante,
idoso etc.).

## Metodologia

1. **Ingestão e seleção de dados**: revisão humana da documentação do
   e-SUS (schema operacional e Data Warehouse) para identificar qual
   tabela/coluna guarda cada tipo de dado sensível, e definição da regra
   de tratamento para cada um. Ver [`GUIDELINE.md`](GUIDELINE.md) e
   [`docs/`](docs/).
2. **Pipeline de anonimização**: um orquestrador roda uma série de
   migrations, cada uma testada contra um Postgres efêmero antes de ser
   aplicada na base real; a pipeline para na primeira falha, deixando o
   banco em estado seguro. Ver [`PIPELINE.md`](PIPELINE.md).

## Onde encontrar cada coisa

| Arquivo | Conteúdo |
|---|---|
| [`PIPELINE.md`](PIPELINE.md) | Arquitetura do orquestrador e das migrations, convenções de código, como configurar e rodar a pipeline, como funciona o teste-antes-de-aplicar. |
| [`GUIDELINE.md`](GUIDELINE.md) | Guideline de anonimização: o que fazer com cada tipo de dado sensível (CPF, nome, endereço, data de nascimento, dado antropométrico, texto livre etc.) e restrições de plausibilidade por perfil de ciclo de vida (criança, adolescente, gestante, climatério). |
| [`docs/mapeamento_colunas.tsv`](docs/mapeamento_colunas.tsv) | Inventário linha a linha de qual tabela/coluna do e-SUS guarda cada dado sensível, com a ação sugerida e a fonte na documentação oficial. |
| [`docs/catalogo_dw_tabelas.md`](docs/catalogo_dw_tabelas.md) | Catálogo de todos os domínios de Fato/Dimensão do Data Warehouse, cruzado com o mapeamento acima: o que já foi revisado, o que falta, e lacunas conhecidas (ex.: nome do cidadão e CNS ainda sem ação definida na guideline; texto livre clínico ainda não inventariado). |

## Estado atual

- 11 migrations implementadas (`scripts/01_anon_cpf.py` até
  `11_anon_identificadores_diversos.py`), cobrindo schema operacional e
  Data Warehouse: CPF, CNS (hash provisório), nome (cidadão e
  profissional), unidade de saúde (nome e CNES), e-mail (pessoal e
  institucional), endereço, data de nascimento/registro, dado
  antropométrico (hash provisório), documentos/anexos, e identificadores
  diversos (prontuário, telefone, NIS, naturalização, óbito/DO,
  identificação mista). A lista de colunas de cada migration é conferida
  contra o schema físico real via `scripts/audit_schema.py`
  (`docs/auditoria_schema.md`).
- **Fase 2, ainda fora do escopo desta pipeline** (decisão explícita):
  texto livre via NER, differential privacy real para dado antropométrico
  extremo, geração sintética de doenças raras/dados genéticos, e as
  regras de ciclo de vida/perfis (população sintética).
- **Pendente de scoping**: IP e log de acesso — a auditoria real ainda
  não tem categoria própria para essas colunas.
