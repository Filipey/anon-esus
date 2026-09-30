# Relatório das migrations de anonimização

Levantamento de **o que** cada migration anonimiza, **como** (técnica),
**quantas tabelas/colunas** declara, e **quantos registros reais** foram
afetados na última execução completa registrada contra o banco real.

## Fontes e metodologia

- **Tabelas/colunas declaradas**: lidas diretamente do código de cada
  migration em `scripts/`, e cruzadas com o resumo por categoria em
  [`docs/auditoria_schema.md`](auditoria_schema.md) (que audita o schema
  físico real: 1.154 tabelas, 10.033 colunas inspecionadas).
- **Registros afetados**: extraídos de `logs/pipeline_20260805_170423.log`
  e `pipeline_20260805_170423_auditoria.json` — a última execução completa
  registrada da pipeline contra o banco configurado em `.env`, em
  2026-08-05. Esses arquivos não são versionados (`logs/` está no
  `.gitignore`), então este relatório é o único registro persistente
  desses números.
- **Limitação importante**: o banco local (`localhost:5433`) não está
  acessível no momento em que este relatório foi gerado (conexão
  recusada), então os números abaixo **não foram confirmados de novo** —
  são os da última execução disponível. Se a base mudou desde então
  (nova carga, schema diferente), os valores reais podem ter mudado.

## Estado da última execução real (2026-08-05)

| Migration | Resultado |
|---|---|
| 01–10 | Aplicadas com sucesso e commitadas (cada migration é uma transação própria) |
| 11 | **Falhou e foi revertida por completo** (rollback) — ver observação abaixo |
| 12 | **Nunca foi alcançada** — a pipeline para na primeira falha |

A migration 11 quebrou em `tb_dsei.nu_telefone1` (`varchar(10)`): o
telefone fictício gerado pelo Faker tem 11 dígitos e estourou o tamanho da
coluna (`StringDataRightTruncation`). Como cada migration roda dentro de
uma única transação (`engine.begin()`), **toda** a migration 11 foi
revertida — inclusive as atualizações de prontuário que já tinham
rodado antes do telefone quebrar. O efeito líquido no banco é zero. Não há
commit posterior no histórico do Git corrigindo esse bug especificamente
em `scripts/11_anon_identificadores_diversos.py` (só o commit original que
adicionou o arquivo) — ele provavelmente continua presente no estado atual
do código.

## Resumo por migration

| # | Migration | Dado tratado | Tabelas declaradas | Colunas declaradas | Registros reais afetados |
|---|---|---|---|---|---|
| 01 | `01_anon_cpf.py` | CPF (cidadão e profissional) | 77 | 92 | 2.130 CPFs distintos → 36.045 linhas |
| 02 | `02_anon_unidade_saude.py` | Nome + CNES da unidade de saúde | 4 (nome) / 27 (CNES) | 31 | 22.732 linhas (nome) + 24.596 linhas (CNES) |
| 03 | `03_anon_email.py` | E-mail pessoal e institucional | 13 (pessoal) / 5 (institucional) | 20 | 33.869 (pessoal) + 407 (institucional) |
| 04 | `04_anon_datas_cidadao.py` | Data de nascimento + datas de registro | 47 (+9 satélite) | 55 | 3.765 linhas (61 em tabelas satélite) |
| 05 | `05_anon_profissional.py` | Nome + registro profissional | 5 (nome) / 6 (registro) | 16 | 70.331 nomes + 75 registros |
| 06 | `06_anon_endereco.py` | Endereço (cidadão, profissional, unidade, DSEI, polo base, domicílio) | 18 | 146 | 26.753 endereços |
| 07 | `07_anon_documentos.py` | Documentos/anexos (PDF, imagens, DICOM) | 6 | 6 | 3.007 valores excluídos |
| 08 | `08_anon_antropometrico.py` | Peso, altura, perímetros, IMC, altura uterina | 7 | 40 | 1.791 valores hasheados |
| 09 | `09_anon_nome_cidadao.py` | Nome do cidadão / mãe / pai / social | 5 | 11 | 49 nomes distintos → 53 linhas |
| 10 | `10_anon_cns.py` | CNS (cidadão e profissional) | 75 | 91 | 47.466 valores hasheados |
| 11 | `11_anon_identificadores_diversos.py` | Prontuário, telefone, NIS, naturalização, óbito/DO, identificação mista | 63 | 128 | **0 (revertido — ver acima)** |
| 12 | `12_anon_ip_logs.py` | Logs de acesso/auditoria, IP | 6 (5 delete + 1 scrub) | — | **Nunca executada** |

**Total (01–10, único bloco efetivamente commitado nessa execução):**
508 colunas declaradas (636 somando a migration 11, que foi revertida),
com sobreposição de tabelas entre migrations — várias tocam
`ta_cidadao`/`tb_cidadao`/`tb_prof`. **270.890 linhas** efetivamente
atualizadas ou excluídas.

## Detalhamento por migration

### 01 — CPF (`01_anon_cpf.py`)

- **O quê**: CPF de cidadão (titular, cuidador, responsável) e de
  profissional de saúde.
- **Como**: mapeamento determinístico 1:1 — coleta todos os valores
  distintos de todas as 92 colunas declaradas, gera um CPF fictício válido
  (dígito verificador correto, via lib `cpf_generator`) para cada valor
  único, e aplica o **mesmo mapa** a todas as colunas via
  `UPDATE ... FROM` com tabela temporária. Isso garante que o mesmo CPF
  real vira o mesmo CPF falso em toda a base — preserva vínculos entre
  tabelas.
- **Exclusão deliberada**: `ds_login` (guarda cópia do CPF usada pra
  autenticação) nunca entra na lista — mexer nela quebraria login sem
  necessidade.
- **Números**: 2.130 CPFs distintos anonimizados, 36.045 linhas
  atualizadas em 77 tabelas.

### 02 — Unidade de saúde (`02_anon_unidade_saude.py`)

- **O quê**: nome e código CNES da unidade de saúde.
- **Como**: nome vira rótulo genérico numerado (`Unidade de Saúde 1`, `2`,
  ...) por ordem alfabética; CNES vira hash determinístico → código
  fictício de 7 dígitos. Ambos com o mesmo mecanismo de mapa 1:1 de 01.
  Trocar só o nome não bastaria: o CNES é público e sozinho reidentifica a
  unidade.
- **Números**: 22.732 linhas de nome + 24.596 linhas de CNES atualizadas.

### 03 — E-mail (`03_anon_email.py`)

- **O quê**: e-mail pessoal (cidadão/profissional) e institucional
  (unidade/DSEI/polo base).
- **Como**: **não é mapeamento por valor** — todo e-mail pessoal vira a
  mesma constante `cidadao@teste.br`; todo e-mail institucional vira
  `unidade@teste.br`. Categorias separadas de propósito (usar o
  placeholder de cidadão num contato institucional seria inconsistente).
  E-mail de infraestrutura (SMTP, integração de sistema) é deixado de
  fora.
- **Números**: 33.869 e-mails pessoais + 407 institucionais.

### 04 — Datas de nascimento e registro (`04_anon_datas_cidadao.py`)

- **O quê**: dia de nascimento (mês/ano preservados) e todas as datas de
  atendimento/registro longitudinal da mesma pessoa.
- **Como**: o novo dia de nascimento é determinístico (seed = hash do
  CPF), válido para o mês/ano original. O delta em dias entre o
  nascimento original e o novo é aplicado a **todas** as colunas
  date/timestamp clínicas da pessoa, descobertas em tempo de execução via
  `information_schema` (não uma lista curada à mão) — preserva o
  espaçamento temporal exato entre os registros de uma mesma pessoa.
  Tabelas sem `dt_nascimento` própria recebem o delta via join com
  `tb_cidadao` (tabelas satélite), processadas primeiro para não usar uma
  data já deslocada como referência.
- **Números**: 3.765 linhas com data anonimizada (61 em tabelas satélite).

### 05 — Profissional (`05_anon_profissional.py`)

- **O quê**: nome e número de registro profissional (conselho de classe).
- **Como**: nome fictício via Faker com seed fixo, sobrenome fixo
  "Teste", mapa 1:1 determinístico (mesmo mecanismo de 01/02). O gênero do
  nome alterna pela ordenação alfabética do nome original — **não** pelo
  sexo real registrado (`no_sexo`), o que pode gerar incoerência (nome
  feminino com sexo=M), ainda não corrigida. Registro profissional vira
  constante fixa `99999`.
- **Números**: 70.331 nomes + 75 registros atualizados.

### 06 — Endereço (`06_anon_endereco.py`)

- **O quê**: endereço completo (CEP, logradouro, bairro, complemento,
  referência, número, e — em tabelas de domicílio — latitude/longitude)
  de cidadão, profissional, unidade de saúde, DSEI, polo base e
  domicílio/família.
- **Como**: *record swapping* — troca o conjunto atômico de campos de
  endereço de uma linha por outro conjunto de campos **já existente na
  mesma tabela**, restrito ao **mesmo município**. O endereço substituto é
  escolhido por um deslocamento pseudoaleatório determinístico
  (`md5(ctid)` módulo `candidatos - 1`), garantindo que nunca seja igual
  ao original. Nunca recombina pedaços de endereços diferentes (não
  "monta" endereço artificial). Tabelas sem coluna de município
  reconhecida são puladas.
- **Números**: 26.753 endereços trocados no total — a maior fatia é
  `ta_unidade_saude` (24.108), seguida de `ta_cidadao` (902) e
  `tb_unidade_saude` (1.494); a maioria das outras tabelas teve poucas
  dezenas de linhas ou zero.
- **Ver a seção de quase-identificadores abaixo** para uma análise crítica
  desta técnica.

### 07 — Documentos/anexos (`07_anon_documentos.py`)

- **O quê**: conteúdo binário (`bytea`) e nome de arquivos anexados (PDF,
  imagens, DICOM).
- **Como**: `NULL` quando a coluna aceita; `''::bytea` para `bytea`
  `NOT NULL`; placeholder de texto (`arquivo_removido`) para nome de
  arquivo `NOT NULL`.
- **Números**: 3.007 valores excluídos.

### 08 — Dado antropométrico (`08_anon_antropometrico.py`)

- **O quê**: peso, altura, perímetro cefálico, circunferência abdominal,
  perímetro de panturrilha, IMC, altura uterina.
- **Como**: **medida provisória** — hash determinístico salgado por
  valor, respeitando o tamanho/precisão real da coluna. O próprio código
  documenta a fraqueza: são campos numéricos de baixa cardinalidade
  (poucos milhares de valores plausíveis), então um hash — mesmo salgado —
  não impede força bruta sobre todo o range plausível. O plano é
  substituir por differential privacy real na fase 2.
- **Números**: 1.791 valores hasheados.

### 09 — Nome do cidadão (`09_anon_nome_cidadao.py`)

- **O quê**: nome do próprio cidadão, da mãe, do pai, nome social.
- **Como**: mapa 1:1 determinístico via Faker (nome completo comum, sem
  sobrenome fixo — diferente da regra de profissional).
- **Números**: 49 nomes distintos → 53 linhas atualizadas.

### 10 — CNS (`10_anon_cns.py`)

- **O quê**: Cartão Nacional de Saúde de cidadão e profissional.
- **Como**: **medida provisória**, igual à de dado antropométrico — hash
  determinístico salgado. Diferente do CPF, não há biblioteca pronta pra
  gerar CNS fictício com dígito verificador válido; gerar um fica pra
  fase 2.
- **Números**: 47.466 valores hasheados em 75 tabelas.

### 11 — Identificadores diversos (`11_anon_identificadores_diversos.py`)

- **O quê**: prontuário, telefone, NIS/PIS/PASEP, número de portaria de
  naturalização (+ data, reduzida a 1º de janeiro do ano), número de
  óbito/DO, identificação mista (campo que guarda CPF **ou** CNS no mesmo
  valor).
- **Como**: prontuário/NIS/naturalização(número)/óbito/mista → hash
  determinístico salgado; telefone → mapa 1:1 via Faker (inclui telefone
  institucional, já que um número fictício não "rotula" a unidade como
  cidadão do jeito que o placeholder de e-mail rotulava). Identificação
  mista detecta CPF vs. CNS pela quantidade de dígitos (11 vs. 15) — sem
  garantia de bater com o valor fictício já usado em 01/10 para a mesma
  pessoa (simplificação aceita).
- **Números**: **falhou e foi revertida** nesta execução (ver "Estado da
  última execução real"). Antes de quebrar, chegou a processar ~51
  valores de prontuário (também revertidos).

### 12 — Logs de acesso e IP (`12_anon_ip_logs.py`)

- **O quê**: logs de acesso, auditoria, sincronização, e o IP de quem
  acessou.
- **Como**: `DELETE` completo em 5 tabelas (incluindo
  `tb_historico_acesso`, que guarda o IP). Uma tabela
  (`tb_auditoria_evento`) tem FK apontando pra ela
  (`tb_retificacao_atend`, `NO ACTION` on delete) — em vez de deletar, zera
  todas as colunas exceto a chave primária. Antes de deletar qualquer
  tabela, reconfirma se surgiu FK nova apontando pra ela.
- **Números**: não executada nesta rodada (pipeline parou em 11).

---

## Achados do diagnóstico direto na base (setembro/2026)

Consultas de agregado e de metadado executadas contra a base real **antes**
de qualquer migration ser aplicada (instância `esus-standalone`, um único
município: 11.604 cidadãos, 5.827 famílias, 3.554 domicílios, 12 unidades
de saúde, 11 equipes, 182 profissionais). Nenhum valor identificável saiu
das consultas — só contagens, quantis e nomes de coluna.

### A1 — Coordenada de GPS da residência, em texto claro

As três tabelas de visita domiciliar carregam `nu_latitude`/`nu_longitude`
capturados pelo ACS no momento da visita. São 105.317 visitas
geolocalizadas com **102.380 pontos distintos** — praticamente um ponto
único por visita, mediana de 11 pontos por pessoa.

Agrupando por cidadão e medindo a distância mediana ao centro robusto do
aglomerado: **mediana de 15,2 m** (p25 = 7,3 m; p75 = 145,4 m). Isso é
ruído de sensor, não dispersão real — o centro estima a casa com erro da
ordem de 5 m, contra uma testada de lote urbano de 10–12 m.

- **4.813 cidadãos** localizáveis a menos de 50 m — **41% de toda a base**.
- 5.846 a menos de 200 m.
- 1.842 têm simultaneamente coordenada de visita e endereço no escopo da
  migration 06, o que permite **inverter a troca de endereço** (o endereço
  real é o mais próximo do centro do aglomerado).

Nenhuma migration toca essas colunas, e a chave que liga visita a cidadão
sobrevive à anonimização porque a substituição de identificadores é
determinística e consistente entre tabelas.

### A2 — A troca de endereço é inerte para parte da base

Reproduzindo a lógica de partição da migration 06 sobre os dados reais:
em `tb_cidadao` há 153 municípios de origem, com **mediana de 1 endereço
candidato** por município e p75 = 2.

- **87 de 153 municípios têm um único endereço distinto.** O SQL cai no
  ramo `candidate_count <= 1`, o candidato escolhido é o próprio original,
  e o filtro final descarta a linha: **nenhum UPDATE**, endereço real
  preservado, sem aviso no log.
- Com exatamente 2 candidatos, `offset = (hash % 1) + 1 = 1` anula o hash
  e a operação vira uma **transposição determinística** — os dois
  endereços trocam de lugar, 100% reversível.
- Somando `linhas_pool_1`: **~743 registros mantêm o endereço real**
  (~508 de pessoas, ~235 de instituições).

Propriedade formal: o conjunto de endereços distintos por município é
**invariante** sob a operação. Ela permuta, não cria diversidade — o k
depois é idêntico ao k antes.

Complemento: apenas 3.282 dos 11.604 cidadãos (28%) têm endereço na
tabela de cidadão. Nenhum escapa por município nulo (verificado: 0). O
endereço da maioria vive no domicílio.

### A3 — Território: INE e micro-área, 50 colunas sem tratamento

Nem "INE", nem "equipe", nem "micro-área" existem como categoria em
`audit_schema.py`, então essa lacuna nunca teve como aparecer na
auditoria. Enumerando o schema real:

| Categoria | Colunas | Tipo | Situação |
|---|---|---|---|
| INE (`nu_ine`, `nu_ine_vinc_equipe`, `nu_ine_executante`, `nu_ine_solicitante`, `nu_ine_finalizador_obs`) | **29** | `character varying` | Nenhuma migration |
| Micro-área (`nu_micro_area`, `nu_micro_area_domicilio`, `nu_micro_area_tb_cidadao`) | **21** | `character varying` | Nenhuma migration |
| `st_microarea_polo_base` | 4 | `integer` | Nenhuma migration — flag de território indígena, dado sensível por origem étnica |

**O INE é público, exatamente como o CNES.** A migration 02 substitui o
CNES com a justificativa escrita no próprio módulo: "o CNES é público e,
sozinho, permite reidentificar a unidade mesmo depois do nome ser trocado
pelo rótulo genérico". O mesmo argumento vale literalmente para o INE, e a
pipeline não o aplica. A cadeia é: **INE → equipe real → CNES → unidade
real → endereço real da unidade**, o que desfaz a migration 02 por um
caminho lateral; e os extratos públicos do CNES trazem a composição de
profissionais por equipe, enfraquecendo a migration 05.

**A micro-área é geografia mais fina que o bairro.** Com ~10,5 mil
cidadãos vinculados a 11 equipes (~950 por equipe) e 2–4 ACS por equipe,
chega-se a algo entre 22 e 44 micro-áreas, de ~240 a ~475 pessoas cada —
provavelmente mais fina que um setor censitário. Suprimir o endereço e
deixar a micro-área de pé repete o erro de A1: anonimizar uma
representação da localização e deixar outra, mais precisa, em outra
coluna.

**Duas geografias paralelas.** A base carrega duas partições
independentes da mesma cidade — território de saúde (micro-área ⊂ área) e
geografia do IBGE (setor ⊂ bairro) — cujos limites não coincidem.
Publicar as duas em resolução fina é pior que publicar qualquer uma
sozinha, porque a interseção de duas partições é mais fina que ambas. O
desenho precisa **escolher um eixo** e engrossar ou suprimir o outro.

### A4 — Unidades de saúde sem coordenada

Não existe uma única coluna de latitude/longitude em nenhuma tabela de
unidade de saúde. A distância cidadão↔unidade, que a equipe queria
preservar, **não existe como dado** — precisa ser criada geocodificando as
unidades. São 12, o que torna isso meia hora de trabalho manual, feito uma
vez. Precisa acontecer **antes** da migration 02, que destrói o CNES usado
para consultar o cadastro público.

### Decisão de desenho que saiu do diagnóstico

A migration 06 é substituída. O endereço deixa de ser trocado e passa a
ser **suprimido**, com a utilidade geográfica reconstruída por atributos
derivados:

1. **Suprimir**: logradouro, número, complemento, ponto de referência, CEP
   completo, coordenadas (inclusive as das visitas), e micro-área.
2. **Generalizar**: um eixo geográfico único, com k mínimo de 20 e
   generalização por registro (cada domicílio sobe na hierarquia só até
   alcançar o k); supressão para quem não alcança nem no topo.
3. **Derivar**: faixa de distância até a unidade de vínculo, em bandas de
   250 m, calculada antes da supressão.
4. **Tratar o INE** como o CNES já é tratado: código fictício
   determinístico, consistente entre tabelas.
5. **Não tocar** o endereço das 12 unidades — são institucionais, de
   endereço público, e servem de referencial fixo.

Justificativa em uma linha: generalização causa **perda de resolução**,
permutação causa **destruição de associação**; só a primeira é recuperável
por modelagem, e é a associação geografia × atributos que a população
sintética precisa aprender.

Pendências de medição antes de fechar os parâmetros: contagem de
micro-áreas distintas e de cidadãos por micro-área; k do par (bucket
geográfico, faixa de distância) — não de cada um isoladamente; e escolha
entre eixo IBGE e eixo território de saúde.

Pendência de manutenção: acrescentar as categorias **INE / equipe /
território** a `audit_schema.py`, senão a próxima auditoria continua sem
enxergar essas 50 colunas.

---

## Levantamento de quase-identificadores remanescentes

Depois das 12 migrations (mesmo supondo 11 e 12 corrigidas e aplicadas com
sucesso), vários campos continuam **intactos ou só fracamente
perturbados**. Isolados, nenhum reidentifica ninguém — mas a literatura de
privacidade (Sweeney 2000/2002; de Montjoye et al. 2013, "Unique in the
Crowd"; Rocher et al. 2019) mostra que a **combinação** de poucos
quase-identificadores costuma bastar. Segue o que sobra na base, por que
importa, e o que falta medir de fato.

### Campos preservados por decisão explícita da guideline

| Campo | Estado | Por quê fica |
|---|---|---|
| Sexo (`no_sexo`/`co_sexo`) | Intocado | Coerência com condições clínicas sexo-específicas (gravidez, câncer de próstata etc.) |
| Mês e ano de nascimento | Intocado (só o dia muda) | Restringe a idade a uma janela de ~30 dias — praticamente a idade exata |
| Diferença em dias entre atendimentos de uma mesma pessoa | Preservada exatamente (migration 04 desloca tudo pelo mesmo delta) | Necessário pra manter a evolução clínica coerente |

### Campos preservados por construção (não são "dado sensível" isolado, mas funcionam como localização/vínculo)

- **Unidade de saúde / equipe vinculada** (`co_dim_unidade_saude`,
  `nu_cnes_vinc_equipe` etc.): a **ligação** entre cidadão e unidade é
  preservada de propósito (GUIDELINE.md exige isso). Cobertura de
  ESF/UBS no Brasil é geograficamente pequena — saber a equipe já
  restringe a pessoa a um território de poucos quarteirões, com muito
  mais precisão do que "o mesmo município" (o critério usado pela troca
  de endereço da migration 06).
- **Composição familiar/domicílio**: quantidade de pessoas no mesmo
  domicílio, papéis (responsável, cuidador) e vínculos entre eles
  continuam intactos — só os identificadores (nome, CPF, CNS) de cada
  membro são trocados. Uma família com uma composição incomum (ex.: avó +
  3 netos, sem os pais) continua identificável pela estrutura, mesmo com
  nomes falsos.
- **Condições clínicas, diagnósticos, procedimentos, medicações**: fora
  de escopo da fase 1 por completo — é o próprio dado que dá valor de
  pesquisa à base, então não é (e não deveria ser) mascarado aqui. Mas é
  exatamente o tipo de atributo "sensível" que, cruzado com os
  quase-identificadores acima, cria unicidade (efeito mosaico).

### O ponto mais parecido com "identificação em 3-4 passos" (de Montjoye 2013)

A literatura de reidentificação por mobilidade mede unicidade a partir de
uma sequência de pontos espaço-temporais aproximados. Este projeto não
guarda trajetória GPS, mas a migration 04 cria um efeito equivalente no
eixo do tempo: **desloca todas as datas de atendimento de uma pessoa pelo
mesmo delta**, preservando o padrão exato de intervalos entre consultas
(3 dias, depois 45, depois 100, depois 2...). Esse padrão é uma
"impressão digital temporal" tão específica quanto uma sequência de
localizações — quem tiver conhecimento auxiliar de quando essa pessoa
foi de fato atendida (um encaminhamento, um atestado, um boletim) pode
reverter o deslocamento e recuperar a data de nascimento real, e por
tabela, a identidade.

### Campos possivelmente fora do radar da auditoria

`docs/auditoria_schema.md` não lista nenhuma categoria para raça/cor,
escolaridade, ocupação, estado civil, etnia, orientação sexual/identidade
de gênero ou deficiência — campos que o e-SUS APS tradicionalmente
armazena em `ta_cidadao`/`tb_cidadao`. Isso não significa que a base atual
não os tenha: só significa que **nenhuma migration cobre esses campos e a
auditoria não os categorizou como achado**, porque o heurístico da
auditoria busca por nomes de coluna associados às categorias já
conhecidas (CPF, CEP, CNS etc.), não por essa classe de atributo
demográfico. Não deu pra confirmar a existência real dessas colunas agora
porque o banco local não está acessível (ver limitação no topo) — vale
checar assim que a conexão voltar (`information_schema.columns`, consulta
só de metadado, sem risco).

### Por que "endereço trocado dentro do mesmo município" não é uma garantia formal

A migration 06 reduz o **espaço de busca** de um atacante que só olha o
campo de endereço, mas:

1. Não calcula nem impõe um tamanho mínimo de grupo (k-anonimato) — troca
   entre candidatos existentes mesmo que só haja 2 endereços distintos no
   município (o código lida explicitamente com esse caso:
   `candidate_count <= 1` no `06_anon_endereco.py:425`).
2. O "pool" de troca é limitado ao município — em municípios pequenos
   (comuns no e-SUS), isso pode significar dezenas de endereços, não
   milhares.
3. Os campos que ficam ao lado do endereço na mesma linha (sexo, mês/ano
   de nascimento, unidade/equipe vinculada, condição clínica) não são
   considerados — então mesmo com o endereço embaralhado, a combinação
   dos demais campos pode isolar a pessoa de qualquer forma (o resultado
   clássico de Sweeney: CEP + data de nascimento + sexo já reidentificam
   87% da população dos EUA sozinhos).

### O que falta pra medir isso de verdade

Hoje não existe, na pipeline, nenhum cálculo de k-anonimato real (tamanho
do menor grupo de registros que compartilham a mesma combinação de
quase-identificadores) nem de l-diversidade sobre o atributo sensível
dentro de cada grupo. Para transformar esta análise qualitativa em número,
seria necessário, com o banco acessível:

```sql
SELECT co_localidade_endereco, sexo, date_trunc('month', dt_nascimento),
       co_dim_unidade_saude, count(*) AS grupo
FROM ...
GROUP BY 1, 2, 3, 4
ORDER BY grupo ASC;
```

— e olhar a cauda de grupos pequenos (`grupo = 1` é reidentificação
garantida por essa combinação). Isso é leitura pura de metadado agregado
(nenhum valor identificável sai do agregado), então é seguro rodar mesmo
antes de decidir a política final de anonimização. Fica de fora deste
relatório porque o banco não estava acessível no momento em que foi
gerado.

## Conclusão prática

A pipeline hoje implementa **de-identificação de identificadores diretos**
(nome, CPF, CNS, e-mail, endereço, documentos) com boa cobertura e boa
engenharia (atomicidade, teste antes de aplicar, auditoria antes/depois).
O que ainda não existe é uma **garantia de anonimato contra ataque de
vínculo** usando o conjunto de quase-identificadores que sobra depois das
12 migrations — que é precisamente o tipo de garantia que a guideline já
reconhece como pendente para dado antropométrico (`08`) e doenças raras
("fase 2"), mas que hoje não está listada como pendente para endereço
(`06`) nem para o padrão temporal de atendimentos (`04`), apesar do
raciocínio acima sugerir que o risco é da mesma natureza.
