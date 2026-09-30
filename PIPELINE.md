# Pipeline de migrations

Pipeline que recebe uma base de dados (PostgreSQL / e-SUS) e aplica uma
série de migrations. **Cada migration é atômica**: roda por completo ou
faz rollback, deixando o banco em estado seguro.

Ver [`GUIDELINE.md`](GUIDELINE.md) para a diretriz de anonimização por dado
sensível e [`docs/mapeamento_colunas.tsv`](docs/mapeamento_colunas.tsv) para
o inventário de tabelas/colunas do Data Warehouse.

## Estrutura

```
pipeline.py                       # orquestrador: testa e roda as migrations em ordem, uma versão da base por migration
scripts/
  00_connect_db.py                # conexão compartilhada -> expõe `engine` e `create_db_engine(banco)`
  versionamento.py                # dumps, restauração e procedência das versões da base (não é migration)
  01_anon_cpf.py                  # migration: anonimiza todos os CPFs
  02_anon_unidade_saude.py        # migration: nomes e CNES de unidades -> genéricos
  03_anon_email.py                # migration: e-mails -> termo genérico (pessoal/institucional)
  04_anon_datas_cidadao.py        # migration: dia de nascimento + datas de registro (auto-descoberta)
  05_anon_profissional.py         # migration: nomes/registros de profissionais
  06_anon_endereco.py             # migration: endereço suprimido + tercil de distância derivado
  07_anon_documentos.py           # migration: exclui conteúdo/nome de arquivos anexados
  08_anon_antropometrico.py       # migration: dado antropométrico -> hash provisório
  09_anon_nome_cidadao.py         # migration: nome do cidadão (próprio/mãe/pai/social)
  10_anon_cns.py                  # migration: CNS -> hash provisório
  11_anon_identificadores_diversos.py # migration: prontuário, telefone, NIS, naturalização, óbito/DO, identificação mista
  12_anon_ip_logs.py              # migration: exclui logs de acesso/auditoria e o IP
  13_anon_ine.py                  # migration: INE de equipe -> código fictício
  14_anon_territorio.py           # migration: coordenada de visita e micro-área -> suprimidas
  audit_schema.py                 # ferramenta: reaudita o schema real (não é migration)
  pipeline_report.py              # relatório de auditoria antes/depois (não é migration)
  pipeline_logging.py             # logging centralizado (arquivo + console)
  plots/                          # ferramentas de plotagem (não são migrations)
    _common.py                    # estilo visual, conexão e helpers de consulta compartilhados
    antropometrico.py             # distribuição + cardinalidade dos campos antropométricos
    condicoes_medicas.py          # distribuição + cardinalidade de colunas candidatas a condição/diagnóstico
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
    test_13_anon_ine.py           # testes da migration 13
    test_14_anon_territorio.py    # testes da migration 14
    test_audit_schema.py          # testes da classificação em audit_schema.py (sem banco)
    test_pipeline_report.py       # testes do relatório de auditoria antes/depois
logs/                             # arquivos de log e relatórios de auditoria gerados a cada execução
plots/                             # figuras (.pdf + .png); scripts/plots/ cria um subdiretório por execução (banco + timestamp)
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
2. **só aplica a migration se o teste passar** — na cópia que vira a
   próxima versão, nunca na base original (ver "Versões incrementais").

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

Opcionais: `VERSAO_BANCO_TRABALHO` (padrão `esus_anon_trabalho`), o banco
do servidor onde as migrations rodam; `VERSOES_DIR` (padrão `versoes/`),
onde ficam os dumps. É preciso `pg_dump`/`pg_restore` na máquina que roda a
pipeline (a versão do cliente pode ser mais nova que a do servidor).

## Execução

```bash
python pipeline.py                     # cria/retoma a cadeia de versões
python pipeline.py --a-partir-de 6     # refaz a versão 06 e as seguintes
python pipeline.py --listar            # versões gravadas e estado do banco de trabalho
python pipeline.py --restaurar 5       # restaura a v05 no banco de trabalho (para o PEC)
python pipeline.py --restaurar 5 --banco esus_v05   # ... ou num banco à parte
```

## Versões incrementais da base

A pipeline **nunca escreve no banco `DB_NAME`**, que é tratado como a
base original. As migrations rodam em sequência num único **banco de
trabalho** no servidor, e depois de cada uma a pipeline grava um dump da
versão na máquina local:

```
DB_NAME (original, intocado)
  └─ pg_dump ─> versoes/v00_original.dump
                 └─ restore no banco de trabalho
                      + 01 ─> versoes/v01_cpf.dump
                      + 02 ─> versoes/v02_unidade_saude.dump
                      ...
                      + 14 ─> versoes/v14_territorio.dump
```

Assim o servidor só precisa de espaço para **um** banco além da original
(o disco de dados tinha 26 GB livres para uma base de 10 GB), e cada
versão ocupa na máquina local só o dump comprimido, sem índices. Para o PEC
gerar os relatórios do próprio sistema sobre uma versão, restaure-a
(`--restaurar NN`) e aponte o PEC para o banco restaurado. O código fica em
`scripts/versionamento.py`; `versoes/` está no `.gitignore` (é dado real).

**Procedência.** Cada dump tem um `.json` ao lado com número e nome da
versão, versão de origem, a **cadeia** de migrations que a gerou (nome e
SHA-256 de cada arquivo, em ordem), commit/branch do git (e se havia
alteração não commitada), data e o relatório de auditoria da etapa. O banco
de trabalho guarda o mesmo JSON no `COMMENT ON DATABASE`, para a pipeline
saber em que versão ele está. Nenhuma tabela é criada dentro da base.

**Reaproveitamento.** Numa nova execução, a pipeline retoma da última
versão cuja cadeia bate com os arquivos atuais: se a migration NN mudou,
as versões NN em diante são apagadas e refeitas, a partir do dump NN-1.
`--a-partir-de NN` força o mesmo sem mudar arquivo.

**Reprodutibilidade.** O banco de trabalho é sempre recriado a partir de
um dump, nunca copiando a original viva (o PEC continua escrevendo nela),
então cada versão deriva exatamente da anterior gravada. As migrations são
determinísticas — inclusive a 01, com a semente `CPF_SEED` —, então uma
versão refeita sai igual à anterior.

**Conexões abertas.** O `pg_dump` da original funciona com o PEC
conectado. Já recriar o banco de trabalho exige que ninguém esteja
conectado a ele; se houver alguém (o PEC, um DBeaver), a pipeline aborta e
lista as conexões — nunca as derruba. Feche e rode de novo.

**Falha.** Se o teste ou a migration falhar, a migration é revertida e o
banco de trabalho continua na versão anterior; a próxima execução retoma
dali.

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

`logs/` e `plots/` são ignorados pelo Git (`.gitignore`) — conteúdo
gerado a cada execução, nunca commitado.

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

## Migration 06 — Endereço: supressão + tercil de distância

Substitui a versão anterior (permutação de endereços dentro do município),
que o diagnóstico de set/2026 mostrou ser **inerte** onde o município tinha
um só endereço candidato, **reversível** onde tinha dois e **destrutiva da
associação** pessoa↔lugar onde tinha muitos (ver
`docs/relatorio_migrations.md`, achado A2). Implementa o desenho aprovado,
com os parâmetros fechados em `experimentos/geografia/`:

1. **Suprime** (NULL) o endereço fino de cidadão, profissional e
   domicílio — logradouro, número, complemento, ponto de referência, CEP,
   **bairro** e coordenadas do domicílio — em `tb_`, `ta_`, `tl_` e DW
   (`ADDRESS_TABLES`). O bairro sai porque o eixo publicado é a equipe, e
   publicar as duas partições juntas refinaria a localização.
2. **Generaliza** para a equipe (INE), que continua na base e recebe código
   fictício na 13. A micro-área é suprimida pela 14.
3. **Deriva**, antes de suprimir, o **tercil de distância** do domicílio
   até a sua unidade (`tb_cds_domicilio.nu_cnes`), com os cortes calculados
   dentro de cada equipe — mesma regra do experimento 06. Classes
   (equipe, tercil) com menos de `K_MIN = 20` domicílios não recebem tercil.
   O valor é gravado em `tb_cds_domicilio.ds_ponto_referencia` (a coluna
   suprimida no passo 1), no formato `TERCIL_TEMPLATE`
   ("faixa de distancia ate a unidade: tercil N de 3 da equipe"). Só a
   tabela mestra do domicílio recebe o tercil.
4. **Não toca** o endereço de unidade de saúde, DSEI e polo base
   (`PRESERVED_TABLES`): institucional e público. A migration recusa rodar
   se alguma delas entrar em `ADDRESS_TABLES`.

As coordenadas das unidades vêm de
`experimentos/geografia/unidades_coordenadas.csv`. Como a 02 roda antes e
troca o CNES, o CSV é casado pelo CNES real e pelo fictício que a 02 gera
para ele (`_fake_cnes`, determinístico). Sem o CSV, a migration só suprime
e avisa no log.

Na base real (set/2026): 1.914 dos 3.554 domicílios têm coordenada válida
e recebem tercil; equipes de 220 a 661 domicílios; menor classe publicada
com 72 — acima de k = 20.

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

**Cobertura ampliada (set/2026).** A primeira versão só tratava as 11
colunas `no_nome*` do DW e de atividade coletiva; a tabela mestra
(`tb_cidadao` e cópias `ta_`/`tl_`), o cadastro individual CDS, o
`tb_fat_cidadao_pec`, o Bolsa Família e o cache de acompanhamento ficavam
com o nome real — mais de um milhão de células. Agora são 60 colunas,
tiradas de uma varredura do schema real.

**Mesma pessoa, mesmo fictício.** A chave do mapa é o nome normalizado (sem
acento, minúsculo, espaço simples), então grafias diferentes do mesmo nome
em tabelas diferentes viram o mesmo fictício, que sai no estilo de caixa do
original.

**Colunas de busca.** `*_filtro` (`FILTER_COLUMNS`) são recalculadas a
partir dos nomes já trocados, no formato observado no banco: nome social +
nome, minúsculo e sem acento. Sem isso elas guardariam o nome real e a
busca por nome no PEC deixaria de achar o cidadão.

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

## Migration 13 — INE (Identificador Nacional de Equipe)

Substitui o INE por um código fictício determinístico e consistente entre
tabelas, nas **29 colunas** confirmadas por enumeração do schema real
(inclui as variantes de papel: `nu_ine_vinc_equipe`, `nu_ine_executante`,
`nu_ine_solicitante`, `nu_ine_finalizador_obs`, `nu_ine_dado_serializado`).

Mesma justificativa da migration 02 para o CNES, aplicada um nível abaixo:
o INE é **público**, e a cadeia `INE → equipe → CNES → unidade → endereço
real` desfaz o trabalho da 02 por um caminho lateral. Como os extratos
públicos do cadastro nacional trazem a composição de profissionais por
equipe, também enfraquece a 05.

É migration nova em vez de extensão da 02 porque a 02 já foi aplicada em
bases reais e a pipeline não é idempotente — re-rodar re-hashearia CNES já
fictício.

O valor fictício tem a **mesma quantidade de dígitos do original**, o que
garante que cabe em qualquer coluna onde o original já cabia sem clampar
por coluna (o que quebraria a consistência do mapa). Foi exatamente o
descuido oposto que derrubou a migration 11 no banco real.

`co_equipe`/`co_dim_equipe` não são tocadas: chaves substitutas opacas
preservam o vínculo sem revelar a equipe real.

## Migration 14 — Coordenada de visita e micro-área

Suprime as duas representações de localização que sobreviviam à migration
06 por estarem em colunas que ela não declara.

- **Coordenada da visita domiciliar** (6 colunas em 3 tabelas): GPS
  capturado pelo agente na porta da casa. No banco real, 105.317 visitas
  geolocalizadas com 102.380 pontos distintos e dispersão mediana de
  15,2 m por cidadão — 41% da base localizável a menos de 50 m. Como a
  chave que liga visita a cidadão sobrevive à anonimização, a troca de
  endereço da 06 era contornável por join, e para 1.842 cidadãos a
  coordenada permitia **inverter a própria troca**.
- **Micro-área** (21 colunas): território do agente comunitário, ~240 a
  ~475 pessoas — provavelmente mais fina que o setor censitário.

Colunas anuláveis viram `NULL`; coluna de texto `NOT NULL` recebe string
vazia; coluna `NOT NULL` **não textual** (coordenada obrigatória) é pulada
com aviso em vez de receber zero — zerar criaria uma coordenada fictícia
plausível, o que é pior que não tratar, e o aviso deixa a auditoria
sinalizar.

`st_microarea_polo_base` fica **fora de propósito**: não é identificador
geográfico, é marcador de origem étnica — dado sensível pela LGPD, que
pertence à análise de atributo sensível da fase 2. A auditoria passou a
categorizá-lo como "Território indígena" para não voltar a passar
despercebido.

## Auditoria do schema (`scripts/audit_schema.py`)

Ferramenta (não é migration — não roda pela pipeline) que consulta
`information_schema` do banco real, classifica colunas por padrão de nome
(`CATEGORY_PATTERNS`) e cruza contra as colunas declaradas em todas as
migrations, gerando `docs/auditoria_schema.md`. Rode de novo sempre que o
schema mudar ou uma migration nova for cogitada:

```bash
python scripts/audit_schema.py
```

## Plots de distribuição e cardinalidade (`scripts/plots/`)

Ferramentas de plotagem (não são migrations, não fazem parte da pipeline
de anonimização) para inspecionar a base real — em particular para
comparar visualmente a base de treino/teste contra a base real antes de
fechar a guideline final de tratamento de um dado. Mesmo estilo visual
"LaTeX" de `scripts/plot_report.py` (serif + mathtext, figuras em
`.pdf`+`.png` dentro de `plots/`).

- `scripts/plots/_common.py`: estilo visual, conexão com o banco
  (reaproveita `00_connect_db.py`) e helpers genéricos de consulta
  (série numérica, cardinalidade, top-N de valores, raridade).
- `scripts/plots/antropometrico.py`: reaproveita `ANTHRO_COLUMNS` de
  `08_anon_antropometrico.py`, agrupa por campo semântico (peso, altura,
  IMC, perímetro cefálico, circunferência abdominal, perímetro de
  panturrilha, altura uterina) e gera, por campo, histograma + ECDF da
  distribuição e um gráfico de cardinalidade relativa
  (distintos/não-nulos). Esse número dá corpo à fragilidade já apontada
  no docstring da migration 08: campo numérico de baixa cardinalidade,
  hash (mesmo com sal) não resiste a um ataque de força bruta que
  pré-calcule o range plausível inteiro.
- `scripts/plots/condicoes_medicas.py`: descobre colunas candidatas a
  condição/diagnóstico de saúde (CIAP, CID, "outra condição") via
  `information_schema`, por padrão de nome — nenhuma migration cobre esse
  dado ainda (ver "Lacunas" abaixo). Classifica pelo prefixo já usado no
  schema (`co_`/`tp_`/`st_` = código → plota distribuição top-N de
  valores e % de linhas com valor raro; `ds_`/`no_` = texto livre →
  **nunca plota conteúdo**, só metadados de preenchimento/cardinalidade,
  pra não vazar string sensível numa figura). Os padrões de nome
  (`_NAME_PATTERNS`) são ponto de partida — confirme contra o schema real
  antes de confiar no resultado, na mesma lógica de `CATEGORY_PATTERNS`
  em `audit_schema.py`.

```bash
python scripts/plots/antropometrico.py
python scripts/plots/condicoes_medicas.py

# --label é opcional, só pra marcar a intenção da execução além do timestamp
python scripts/plots/antropometrico.py --label antes   # antes da pipeline de anonimização
python scripts/plots/antropometrico.py --label depois  # depois, mesmo banco
```

**Cada execução escreve num diretório próprio** —
`plots/<banco>_<timestamp>[_<label>]/` (`_common.run_output_dir`) — nunca
sobrescreve uma execução anterior. O nome do banco vem da própria conexão
(`engine.url.database`), não de configuração separada, então rodar contra
a base de teste e depois contra a real já cai em pastas diferentes sem
precisar de nenhum argumento; `--label antes`/`--label depois` só ajuda a
marcar a intenção quando é o **mesmo** banco nos dois momentos (a pipeline
anonimiza em lugar, não gera uma cópia).

## Lacunas ainda não automatizadas

Itens que ficam para uma próxima fase, por exigirem pesquisa/metodologia
própria em vez de substituição determinística de coluna: textos livres via
NER, dados antropométricos extremos via differential privacy real (hoje só
o hash provisório da migration 08), doenças raras/dados genéticos (geração
sintética correlacionada — `scripts/plots/condicoes_medicas.py` já mede o
risco de reidentificação por raridade de código nessas colunas, mas ainda
não implementa nenhum tratamento), e regras de ciclo de vida/perfis
(pertencem à futura geração de população sintética, não a esta pipeline).

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
