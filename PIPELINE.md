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
  02_anon_unidade_saude.py        # migration: nomes e CNES de unidades -> genéricos
  03_anon_email.py                # migration: e-mails -> termo genérico (pessoal/institucional)
  04_anon_datas_cidadao.py        # migration: dia de nascimento + datas de registro (auto-descoberta)
  05_anon_profissional.py         # migration: nomes/registros de profissionais
  06_anon_endereco.py             # migration: endereços -> outro do mesmo município
  07_anon_documentos.py           # migration: exclui conteúdo/nome de arquivos anexados
  08_anon_antropometrico.py       # migration: dado antropométrico -> hash provisório
  09_anon_nome_cidadao.py         # migration: nome do cidadão (próprio/mãe/pai/social)
  10_anon_cns.py                  # migration: CNS -> hash provisório
  11_anon_identificadores_diversos.py # migration: prontuário, telefone, NIS, naturalização, óbito/DO, identificação mista
  12_anon_ip_logs.py              # migration: exclui logs de acesso/auditoria e o IP
  audit_schema.py                 # ferramenta: reaudita o schema real (não é migration)
  pipeline_report.py              # relatório de auditoria antes/depois (não é migration)
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
    test_07_anon_documentos.py    # testes da migration 07
    test_08_anon_antropometrico.py # testes da migration 08
    test_09_anon_nome_cidadao.py  # testes da migration 09
    test_10_anon_cns.py           # testes da migration 10
    test_11_anon_identificadores_diversos.py # testes da migration 11
    test_12_anon_ip_logs.py       # testes da migration 12
    test_audit_schema.py          # testes da classificação em audit_schema.py (sem banco)
    test_pipeline_report.py       # testes do relatório de auditoria antes/depois
logs/                             # arquivos de log e relatórios de auditoria gerados a cada execução
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

## Relatório de auditoria (quantitativo e qualitativo)

Além do log de texto, cada execução gera um **relatório JSON**
(`logs/pipeline_<timestamp>_auditoria.json`, mesmo timestamp do log) via
`scripts/pipeline_report.py`. Diferente do log (que mostra contagens
migration por migration, em texto corrido), o relatório é estruturado e
comparável: pra cada coluna declarada em alguma migration, mostra se ela
existia antes/depois, quantas linhas tinha, quantos valores não-nulos, e
se o **conteúdo mudou de fato** — sem nunca gravar um valor real no
relatório.

Como funciona: antes de aplicar qualquer migration, o orquestrador tira
uma "foto" de cada coluna-alvo (linhas totais, não-nulos, e um checksum
agregado *order-independent* — soma de `md5(valor)` por linha, o mesmo
mecanismo já usado em `08_anon_antropometrico.py`/`10_anon_cns.py`, só que
aqui pra comparar, não pra substituir). Depois de rodar todas as
migrations (com sucesso ou não — o relatório é escrito mesmo se a pipeline
falhar no meio, documentando o que já tinha mudado até ali), tira a foto
de novo e compara: se os dois checksums diferem, o conteúdo mudou.

```json
{
  "resumo_por_migration": {
    "01_anon_cpf": {
      "colunas_declaradas": 92,
      "colunas_com_conteudo_alterado": 92,
      "colunas_inexistentes_no_banco": 0,
      "tabelas_declaradas": 0,
      "linhas_removidas_em_tabelas": 0
    }
  },
  "detalhe_por_migration": { "...": "uma entrada por coluna/tabela" }
}
```

Tabelas de `12_anon_ip_logs.py` (que deletam ou esvaziam linhas, não
colunas) entram no relatório por linhas removidas, não por checksum de
coluna.

**Custo**: é uma segunda varredura completa de cada coluna-alvo (antes +
depois) — em bases muito grandes, isso soma um tempo não trivial à
execução. Rode com esse custo em mente antes de aplicar num banco grande.

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

**Login continua funcionando de propósito.** O login do profissional usa
`tb_usuario.ds_login`, uma cópia do CPF gravada na criação da conta — nunca
recalculada a partir de `nu_cpf` (confirmado por comparação direta: 100%
de igualdade em todos os pares profissional+usuário do banco auditado).
Essa coluna nunca esteve em `CPF_COLUMNS` e está listada em
`PRESERVE_FOR_LOGIN` como guarda de segurança: `run()` recusa executar (com
`RuntimeError`) se qualquer coluna de `PRESERVE_FOR_LOGIN` aparecer em
`CPF_COLUMNS` — evita que alguém "complete" a anonimização de CPF
adicionando essa coluna sem perceber que quebraria o login de todos os
profissionais.

## Migration 02 — Nomes e CNES de Unidades de Saúde

Substitui o nome de cada unidade por uma denominação genérica
(`Unidade de Saúde 1`, `Unidade de Saúde 2`, ...) e o código CNES por um
código fictício de 7 dígitos — o CNES é público e, sozinho, permite
reidentificar a unidade mesmo com o nome genérico.

- **Consistente entre tabelas**: o mesmo nome (ou CNES) original recebe
  sempre o mesmo valor fictício em todas as colunas.
- **Numeração determinística**: nomes ordenados alfabeticamente; CNES
  derivado por hash do valor original — ambos reprodutíveis entre execuções.
- **Atômica**: tabela temporária de mapeamento (uma para nome, outra para
  CNES) + `UPDATE ... FROM` por join.

Colunas declaradas em `NAME_COLUMNS` e `CNES_COLUMNS` no topo de
`scripts/02_anon_unidade_saude.py` (ajuste para o schema da sua base). O
texto base está na constante `GENERIC_TEMPLATE = "Unidade de Saúde {n}"`.

`CNES_COLUMNS` inclui, além das 4 tabelas "mestras", **23 tabelas de
referência** (`tb_familia`, `tb_cidadao_nucleo_familiar`, `tb_revisao`
etc.) que guardam o CNES como valor copiado — não uma FK opaca. Confirmado
contra o schema real: sem essas 23, o CNES original sobreviveria ali e
permitiria religar a unidade fictícia à real via join.

## Migration 03 — E-mails

Substitui e-mail de cidadão/profissional pela constante `GENERIC_EMAIL`
(`cidadao@teste.br`) e e-mail institucional (unidade, DSEI, polo base) por
`GENERIC_INSTITUTIONAL_EMAIL` (`unidade@teste.br`) — são categorias
diferentes e não compartilham o mesmo placeholder. Não há mapeamento por
valor — todos os e-mails de uma categoria viram a mesma constante. Nulos e
strings vazias são preservados.

- **Atômica**: uma única transação, `UPDATE` por coluna.

Colunas declaradas em `PERSONAL_EMAIL_COLUMNS` e
`INSTITUTIONAL_EMAIL_COLUMNS` no topo de `scripts/03_anon_email.py`
(ajuste para o schema da sua base). Colunas de infraestrutura (SMTP,
integração de sistemas) são deixadas de fora de propósito — não são dado
pessoal nem institucional de saúde.

## Migration 04 — Datas de nascimento e registros

Substitui o dia da data de nascimento por um dia válido do mesmo mês/ano,
determinístico por cidadão (`nu_cpf_cidadao`). As demais colunas de
data/timestamp da mesma tabela são **descobertas em tempo de execução**
via `information_schema` (exceto um denylist de padrões que não são
evento clínico, ex. `%atualizacao%`) e deslocadas pelo mesmo delta em
dias, preservando o intervalo entre nascimento e atendimento. Isso evita
depender de uma lista curada à mão por tabela — a versão anterior só
sincronizava datas de registro em 5 das ~53 tabelas declaradas.

Linhas sem CPF ou sem data de nascimento são preservadas. As tabelas são
declaradas em `DATE_TABLES` no topo de `scripts/04_anon_datas_cidadao.py`.

**Tabelas satélite** (`SATELLITE_TABLES`): 9 tabelas de detalhe
(`tb_fat_atd_ind_exames`/`medicamentos`/`problemas`/`procedimentos`,
`tb_fat_atend_odonto_encaminham`/`exames`/`medicament`/`problemas`/`proced`)
têm `nu_cpf_cidadao` mas não têm `dt_nascimento` própria — confirmado
contra o schema real. Para essas, o delta vem de um `UPDATE ... FROM` join
com `tb_cidadao` (`REFERENCE_TABLE`), processado **antes** do loop
principal, enquanto `tb_cidadao.dt_nascimento` ainda está no valor
original.

## Migration 05 — Profissionais

Substitui nomes de profissionais por nomes fictícios com sobrenome `Teste` e
registros profissionais por `99999`, preservando categoria profissional e
demais chaves/códigos. O CNS profissional (`nu_cns`) segue pendente porque
exige uma regra própria de geração/validação de CNS, diferente de CPF.

Colunas declaradas em `NAME_COLUMNS` e `REGISTRATION_COLUMNS` no topo de
`scripts/05_anon_profissional.py`. `REGISTRATION_COLUMNS` inclui
`ta_/tb_/tl_atend_prof.nu_conselho_classe` — essa tabela é um "retrato" do
profissional no momento do atendimento, com sua própria cópia do registro,
separada de `tb_prof` (confirmado no schema real).

**Ponto em aberto (não corrigido ainda)**: `ta_prof`/`tb_prof` têm uma
coluna real de sexo (`no_sexo`/`co_sexo`, confirmada no schema), que esta
migration não toca. O nome fictício é escolhido alternando gênero pela
ordenação alfabética do nome original, não pelo sexo real registrado — 
pode gerar um registro como "Maria Teste" com `no_sexo = 'M'`. Não é
vazamento de privacidade, mas é uma incoerência que ainda não foi
corrigida.

## Migration 06 — Endereços de cidadãos

Substitui o endereço completo por outro endereço já existente na mesma tabela
e no mesmo município. A migration troca o conjunto de campos de uma vez
(bairro, complemento, logradouro, referência, CEP, número e, quando existem,
coordenadas de latitude/longitude), evitando montar endereços artificiais.
Tabelas sem coluna de município reconhecida são puladas com aviso.

Tabelas/colunas declaradas em `ADDRESS_TABLES` no topo de
`scripts/06_anon_endereco.py`. O número da casa (`nu_numero`/`nu_domicilio`
+ `st_sem_numero`) e, nas tabelas de domicílio, `nu_latitude`/`nu_longitude`
foram confirmados no schema real e adicionados ao mesmo conjunto atômico —
antes ficavam de fora, o que deixava o número (e as coordenadas) da casa
original sobrevivendo junto com a rua/bairro de outro endereço.

## Migration 07 — Documentos e anexos

Cobre a orientação de "excluir" documentos em PDF e anexos clínicos:
coloca em `NULL` o conteúdo binário (`bytea`) e o nome de arquivos
anexados. Colunas puramente estruturais (chave substituta `bigint`,
vocabulário de categoria de arquivo) não são tocadas — preservam vínculo.

Colunas declaradas em `DOCUMENT_COLUMNS` no topo de
`scripts/07_anon_documentos.py`, filtradas manualmente a partir da
categoria "Documento/anexo" de `docs/auditoria_schema.md` (que mistura FK,
conteúdo, metadado e flag de status).

## Migration 08 — Dado antropométrico (hash provisório)

O tratamento definitivo (microagregação/truncamento/differential privacy)
ainda não foi definido. Como medida provisória, substitui peso, altura,
perímetro cefálico e circunferência abdominal por um hash determinístico
do valor original (`md5(valor || sal)`), preservando o tipo da coluna
(numérico vira outro número, texto vira string hexadecimal truncada).

**Isto não é uma proteção robusta**: por serem campos numéricos de baixa
cardinalidade, o hash não impede um ataque de força bruta que pré-calcule
o hash de todo o range plausível — serve só como contenção temporária até
o DP entrar. A lista de colunas em `ANTHRO_COLUMNS`
(`scripts/08_anon_antropometrico.py`) já foi confirmada contra o schema
físico real (`docs/auditoria_schema.md`, categoria "Antropometria") — a
primeira versão, baseada só na documentação do DW, tinha dois nomes de
coluna errados e não cobria `ta_/tb_/tl_medicao`, a tabela que concentra
os sinais vitais de cada atendimento (peso, altura, perímetro cefálico,
circunferência abdominal, perímetro de panturrilha, IMC, altura uterina).

## Migration 09 — Nome do cidadão

A guideline original não definia regra para o nome do próprio cidadão (só
para profissional e unidade). Substitui nome próprio, da mãe, do pai e
nome social por nome fictício comum (sem sobrenome fixo — essa regra é só
para profissional), com o mesmo mecanismo de mapa determinístico de
`05_anon_profissional.py`.

Colunas declaradas em `NAME_COLUMNS` no topo de
`scripts/09_anon_nome_cidadao.py`.

## Migration 10 — CNS (hash provisório)

O CNS aparece ao lado do CPF em ~92 colunas, mas a guideline não definiu
regra para ele e não existe biblioteca pronta para gerar CNS válido (o
dígito verificador segue algoritmo próprio). Decisão explícita: tratar
como o dado antropométrico — hash determinístico salgado, sem gerar um
CNS com formato válido. Respeita o tamanho real da coluna
(`character_maximum_length`) para nunca estourar um `varchar(15)`.

Colunas declaradas em `CNS_COLUMNS` no topo de `scripts/10_anon_cns.py`.

## Migration 11 — Identificadores diversos

Consolida seis categorias pequenas sem ação definida na guideline
original: prontuário, telefone, NIS, naturalização, número de documento de
óbito e identificação mista (campo único que guarda CPF **ou** CNS).
Prontuário/NIS/naturalização/óbito usam hash determinístico salgado;
telefone usa Faker (mapa determinístico por valor, como em `09`); a data
de naturalização preserva só o ano; identificação mista detecta o formato
pelo número de dígitos (11 → CPF, 15 → CNS) e aplica o hash correspondente
— sem garantia de bater com o valor fictício já usado em `01`/`10` para a
mesma pessoa (simplificação aceita para a fase 1).

Colunas declaradas em `PRONTUARIO_COLUMNS`, `PHONE_COLUMNS`,
`NIS_COLUMNS`, `NATURALIZACAO_NUMBER_COLUMNS`,
`NATURALIZACAO_DATE_COLUMNS`, `OBITO_COLUMNS` e `MIXED_ID_COLUMNS` no
topo de `scripts/11_anon_identificadores_diversos.py`.

## Migration 12 — Logs de acesso/auditoria e IP

Cobre "Endereço IP das máquinas que acessaram: será excluído" e "Logs de
dados... serão excluídos". Tabelas identificadas por **nome de tabela**
contra o schema real (`tb_historico_acesso`, `tb_auditoria_evento`,
`tb_auditoria_processo`, `tb_envio_log`, `tb_sessao_sincronizacao`,
`tb_ad_transmissao_sessao`) — colunas de log têm nomes genéricos
(`dt_acesso`, `co_usuario`) que só fazem sentido como log no contexto da
tabela. `tl_acesso` foi conferida e excluída de propósito: é controle de
permissão (RBAC), não log de acesso.

- **Única migration do projeto que usa `DELETE`, não `UPDATE`**: as
  tabelas em `DELETE_TABLES` são removidas por completo (`tb_historico_acesso`
  guarda o IP na coluna `co_ip`).
- **Exceção**: `tb_auditoria_evento` tem uma FK apontando para ela
  (`tb_retificacao_atend.co_auditoria_evento_retificado`, `NO ACTION` on
  delete) — um `DELETE` quebraria a integridade referencial. Em vez
  disso, todas as colunas exceto a chave primária são zeradas.
- Antes de deletar qualquer tabela de `DELETE_TABLES`, o script confere de
  novo se apareceu alguma FK apontando para ela; se sim, pula com aviso em
  vez de arriscar uma falha de integridade referencial.

## Auditoria do schema (`scripts/audit_schema.py`)

Ferramenta (não é migration — não roda pela pipeline) que consulta
`information_schema` do banco real, classifica colunas por padrão de nome
(`CATEGORY_PATTERNS`) e cruza contra as colunas declaradas em todas as
migrations, gerando `docs/auditoria_schema.md`. Rode de novo sempre que o
schema mudar ou uma migration nova for cogitada:

```bash
python scripts/audit_schema.py
```

## Lacunas ainda não automatizadas

Itens que ficam para uma próxima fase, por exigirem pesquisa/metodologia
própria em vez de substituição determinística de coluna: textos livres via
NER, dados antropométricos extremos via differential privacy real (hoje só
o hash provisório da migration 08), doenças raras/dados genéticos (geração
sintética correlacionada), e regras de ciclo de vida/perfis (pertencem à
futura geração de população sintética, não a esta pipeline).

## Pontos abertos encontrados na auditoria contra o schema real

Não bloqueiam a fase 1, mas ainda não têm migration:

- **Nome fictício de profissional vs. sexo real** (ver nota na Migration
  05) — `no_sexo`/`co_sexo` existe em `ta_prof`/`tb_prof` e não é
  considerado ao escolher o gênero do nome fictício.
- **`Log de acesso` e `Endereco`** ainda têm itens "suspeito não coberto"
  em `docs/auditoria_schema.md` além do que a migration 12/06 cobrem
  (tabelas de vocabulário/lookup misturadas com achados reais) — vale uma
  triagem futura.
- **`Identificação mista`** (migration 11) não garante o mesmo valor
  fictício já usado em `01`/`10` para a mesma pessoa — simplificação
  aceita para a fase 1.
