# Pipeline de migrations

Pipeline que recebe uma base de dados (PostgreSQL / e-SUS) e aplica uma
série de migrations. **Cada migration é atômica**: roda por completo ou
faz rollback, deixando o banco em estado seguro.

Ver [`GUIDELINE.md`](GUIDELINE.md) para a diretriz de anonimização por dado
sensível e [`docs/mapeamento_colunas.tsv`](docs/mapeamento_colunas.tsv) para
o inventário de tabelas/colunas do Data Warehouse.

## Estrutura

```
pipeline.py                       # orquestrador: testa e roda as migrations em ordem
scripts/
  00_connect_db.py                # conexão compartilhada -> expõe `engine`
  01_anon_cpf.py                  # migration: anonimiza todos os CPFs
  02_anon_unidade_saude.py        # migration: nomes de unidades -> genéricos
  03_anon_email.py                # migration: e-mails -> termo genérico
  04_anon_datas_cidadao.py        # migration: dia de nascimento + datas de registro
  05_anon_profissional.py         # migration: nomes/registros de profissionais
  06_anon_endereco.py             # migration: endereços -> outro do mesmo município
  pipeline_logging.py             # logging centralizado (arquivo + console)
  tests/
    conftest.py                   # fixture `pg_engine`: Postgres efêmero
    _helpers.py                   # loader de migrations para os testes
    test_01_anon_cpf.py           # testes da migration 01
    test_02_anon_unidade_saude.py # testes da migration 02
    test_03_anon_email.py         # testes da migration 03
    test_04_anon_datas_cidadao.py # testes da migration 04
    test_05_anon_profissional.py  # testes da migration 05
    test_06_anon_endereco.py      # testes da migration 06
logs/                             # arquivos de log gerados a cada execução
```

### Convenções

- `scripts/00_connect_db.py` é o módulo de conexão e expõe `engine`
  (SQLAlchemy). A URL é montada com `URL.create`, então senhas com
  caracteres especiais funcionam.
- Cada migration `scripts/NN_*.py` (NN ≥ 01) expõe uma função
  `run(engine)` e cuida da própria atomicidade abrindo a transação com
  `with engine.begin() as conn:` — commit no sucesso, rollback no erro.
- Cada migration tem um teste em `scripts/tests/test_<stem>.py`.
- A pipeline executa as migrations em ordem numérica e **para na
  primeira falha**. Como cada migration é atômica, o banco nunca fica
  num estado parcial.

### Metodologia: testar antes de aplicar

Para **cada** migration, o orquestrador:

1. roda o teste correspondente (`scripts/tests/test_NN_*.py`) contra um
   PostgreSQL **efêmero** — criado num diretório temporário e destruído
   ao fim, isolado do banco real (fixture `pg_engine`);
2. **só aplica a migration no banco real se o teste passar.**

Migration sem teste é tratada como falha e aborta a pipeline. Usamos um
Postgres efêmero (via `testing.postgresql`) em vez de SQLite/H2 porque as
migrations usam SQL específico do Postgres (`information_schema`,
`TEMP TABLE ... ON COMMIT DROP`, `UPDATE ... FROM`, casts `::text`); um
banco de outro dialeto daria resultados de teste enganosos.

Rodar os testes isoladamente (sem aplicar nada):

```bash
pytest scripts/tests
```

## Configuração

Copie `.env.example` para `.env` e preencha:

```
DB_HOST=localhost
DB_PORT=5433
DB_USER=postgres
DB_PASSWORD=...
DB_NAME=esus
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Execução

```bash
python pipeline.py
```

## Logging

Cada execução grava **um arquivo de texto** em `logs/`, com nome
`pipeline_AAAAMMDD_HHMMSS.log` (a saída também aparece no console). O log
registra tudo o que é possível da execução:

- início/fim da pipeline e migrations descobertas;
- para cada migration: invocação dos testes e a **saída completa do
  pytest**, resultado (OK/falha), aplicação no banco real;
- mensagens internas de cada migration (contagens de colunas, valores
  distintos, linhas atualizadas);
- **tracebacks completos** de qualquer falha (conexão, teste, aplicação).

A infraestrutura fica em `scripts/pipeline_logging.py`. Migrations obtêm
o logger com `get_logger("<nome>")`; como todos os loggers ficam sob
`pipeline.*`, um único handler de arquivo captura tudo por propagação.

> **Privacidade:** o log registra apenas **contagens** (quantos CPFs,
> quantas linhas) — nunca os valores de CPF. O echo de SQL do SQLAlchemy
> fica desligado de propósito para não vazar dados sensíveis no arquivo.

Os arquivos `*.log` são ignorados pelo Git (`.gitignore`).

## Migration 01 — Anonimização de CPFs

Substitui todos os CPFs reais por CPFs **aleatórios e válidos**.

- **Determinística**: o mesmo CPF original vira sempre o mesmo CPF falso
  em todas as tabelas, preservando vínculos entre tabelas que referenciam
  o mesmo cidadão.
- **Preserva o formato**: pontuação (`000.000.000-00`) e zeros à esquerda
  do valor original são mantidos no valor anonimizado.
- **Atômica**: tudo numa única transação, com tabela temporária de
  mapeamento (`ON COMMIT DROP`) e `UPDATE ... FROM` por join.

As colunas a anonimizar são declaradas explicitamente na constante
`CPF_COLUMNS` no topo de `scripts/01_anon_cpf.py`. Ela vem pré-populada
com colunas conhecidas do e-SUS APS/PEC — **ajuste para o schema da sua
base**. Colunas inexistentes são apenas puladas com aviso, sem abortar.
```python
CPF_COLUMNS = [
    CpfColumn("public", "tb_cidadao", "nu_cpf"),
    CpfColumn("public", "tb_cidadao", "nu_cpf_responsavel"),
    ...
]
```

## Migration 02 — Nomes de Unidades de Saúde

Substitui o nome de cada unidade por uma denominação genérica
(`Unidade de Saúde 1`, `Unidade de Saúde 2`, ...).

- **Consistente entre tabelas**: o mesmo nome original recebe sempre o
  mesmo rótulo em todas as colunas.
- **Numeração determinística**: nomes ordenados alfabeticamente, então o
  mapeamento é reprodutível.
- **Atômica**: tabela temporária de mapeamento + `UPDATE ... FROM` por join.

Colunas declaradas em `NAME_COLUMNS` no topo de
`scripts/02_anon_unidade_saude.py` (ajuste para o schema da sua base). O
texto base está na constante `GENERIC_TEMPLATE = "Unidade de Saúde {n}"`.

## Migration 03 — E-mails de cidadãos

Substitui todos os e-mails pela constante `GENERIC_EMAIL`
(`cidadao@teste.br`). Não há mapeamento — todos viram o mesmo valor.
Nulos e strings vazias são preservados.

- **Atômica**: uma única transação, `UPDATE` por coluna.

Colunas declaradas em `EMAIL_COLUMNS` no topo de
`scripts/03_anon_email.py` (ajuste para o schema da sua base).

## Migration 04 — Datas de nascimento e registros

Substitui o dia da data de nascimento por um dia válido do mesmo mês/ano,
determinístico por cidadão (`nu_cpf_cidadao`). As datas de atendimento ou
registro listadas na mesma tabela são deslocadas pelo mesmo delta em dias,
preservando o intervalo entre nascimento e atendimento.

Linhas sem CPF ou sem data de nascimento são preservadas. As tabelas/colunas
são declaradas em `DATE_TABLES` no topo de
`scripts/04_anon_datas_cidadao.py`.

## Migration 05 — Profissionais

Substitui nomes de profissionais por nomes fictícios com sobrenome `Teste` e
registros profissionais por `99999`, preservando categoria profissional e
demais chaves/códigos. O CNS profissional (`nu_cns`) segue pendente porque
exige uma regra própria de geração/validação de CNS, diferente de CPF.

Colunas declaradas em `NAME_COLUMNS` e `REGISTRATION_COLUMNS` no topo de
`scripts/05_anon_profissional.py`.

## Migration 06 — Endereços de cidadãos

Substitui o endereço completo por outro endereço já existente na mesma tabela
e no mesmo município. A migration troca o conjunto de campos de uma vez
(bairro, complemento, logradouro, referência, CEP e número), evitando montar
endereços artificiais. Tabelas sem coluna de município reconhecida são
puladas com aviso.

Tabelas/colunas declaradas em `ADDRESS_TABLES` no topo de
`scripts/06_anon_endereco.py`.

## Lacunas ainda não automatizadas

Alguns itens do guideline continuam sem migration porque exigem regra de
anonimização ainda não definida ou inventário concreto de tabelas/colunas:
IPs, documentos/anexos/PDFs, logs de acesso, textos livres via NER, dados
antropométricos extremos, doenças raras/genéticas e campos classificados no
TSV como "Sem categoria na guideline".
