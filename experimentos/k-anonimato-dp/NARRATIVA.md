# Trilho A — narrativa da metodologia: k-anonimato evoluído e kit DP

Texto de trabalho que reconstrói, etapa por etapa, o que foi feito no Trilho A
da fase 2, por que foi feito e o que cada etapa mostrou. Serve de insumo para
as seções de Métodos, Resultados e Discussão. Convenção: frases com números
descrevem o que foi medido; expressões como "isso indica", "uma leitura
possível" marcam interpretação a validar. Todos os números são da base
original (`esus-standalone`), medidos em 07/10/2026.

## 1. Contexto e objetivo

A base e-SUS APS/PEC usada no projeto tem um período de retenção: ao fim dele
(por volta de 21/10/2026) a base original é apagada e só a versão anonimizada
pode ser mantida. Essa versão é a que será usada, depois, para gerar
populações sintéticas. O critério adotado para "anonimizada" é o da LGPD
(art. 12): não ser possível reidentificar uma pessoa por meios razoáveis.

Duas consequências organizaram o trabalho. Primeiro, a base guardada precisa
de fato deixar de ser identificável — não basta trocar identificadores
diretos. Segundo, tudo o que depende da original (escolher parâmetros, medir
utilidade contra ela, medir estatísticas finas) tem de ser feito antes do
prazo, porque não pode ser refeito depois.

## 2. Ponto de partida: o que a fase 1 garantia

A fase 1 trocou ou suprimiu identificadores diretos (nome, CPF, CNS, e-mail,
documentos, logs, INE, CNES) e tratou o endereço: o endereço fino foi
suprimido e a localização passou a ser publicada como equipe de saúde mais
um tercil de distância do domicílio até a unidade, com k ≥ 20 nessa classe
geográfica (migration 06). Esse era o único k-anonimato da pipeline, e só
cobria a geografia. Outros atributos ficavam publicados de propósito: sexo,
mês e ano de nascimento (a migration 04 só trocava o dia), raça/cor,
escolaridade, município de nascimento e de residência, ocupação, além de
diagnósticos e medidas antropométricas — estas, com um hash provisório.

## 3. Etapa 1 — medir o risco que sobrava (experimento 00)

A pergunta era se esses atributos, combinados, ainda permitiam reidentificar
alguém. Para os 9.637 cidadãos ativos e vivos de `tb_cidadao`, o experimento
mediu o tamanho da classe de equivalência de cada pessoa à medida que
quase-identificadores (QI) eram somados.

Os dados mostram que sexo mais mês/ano de nascimento já deixam 2,5% das
pessoas únicas e 100% em grupos menores que 20. Somando a equipe, 36,9% ficam
únicas; com o tercil, 67,2%; com raça/cor, 81,2%. Com os 13 QI disponíveis,
99,0% das pessoas são únicas. Ou seja: o k ≥ 20 da geografia não protegia
ninguém, porque o nascimento sozinho já colocava todos abaixo dele.

Retirar um QI de cada vez do cenário completo mostrou que o nascimento
domina: sem ele, os únicos caem de 99,0% para 51,4%; sem qualquer outro, a
queda é menor que 2 pontos. Generalizar só a data não resolve: sobre sexo +
equipe + tercil + raça/cor, publicar só o ano deixa 22,5% únicos; faixas de
5 anos, 3,3%; e mesmo as 5 faixas de ciclo de vida deixam 20,4% das pessoas
em classes menores que 20. O experimento também revelou QI que nenhuma
migration tratava: município de nascimento (275 valores), município de
residência (149) e ocupação (156).

Isso indica que a base, como estava, dificilmente passaria pelo critério de
"meios razoáveis": o que um vizinho ou agente de saúde sabe (sexo, idade
aproximada, onde a pessoa mora, raça/cor) identifica 4 em cada 5 pessoas.

## 4. Etapa 2 — por que evoluir o k-anonimato, e não substituí-lo por DP

Diante de tantos QI, considerou-se trocar tudo por differential privacy (DP).
A decisão foi não fazer isso, por três razões discutidas e registradas no
plano do experimento:

- DP aplicada registro a registro (DP local), com um ε que de fato protege,
  exigiria trocar o sexo de muitas pessoas, deslocar datas em anos e somar
  ruído de dezenas de centímetros à altura. A base perderia a coerência
  clínica (gestação em homem, calendário vacinal sem sentido) e os
  relatórios do PEC, que serão usados para medir utilidade.
- Uma base sintética gerada com DP como único artefato guardado seria uma
  aposta de tiro único: o modelo teria de ser acertado em 14 dias e não
  poderia ser corrigido depois do prazo; e perderia a estrutura relacional
  (histórico de atendimentos, vínculos de família, texto clínico).
- O que a DP faz melhor aqui é complementar: medir na original, com garantia
  formal, as distribuições finas que a generalização vai destruir.

A metodologia ficou em duas camadas: a base guardada é tratada por
k-anonimato evoluído (risco medido, estrutura preservada) e, em paralelo, um
kit de marginais com DP guarda a resolução fina para a geração sintética.
Antropometria e doenças raras entram no k-anonimato por generalização
(microagregação e hierarquia de códigos), e não por DP dentro da base, porque
ruído por registro degradaria esses dados mais do que a generalização e daria
uma garantia que não se compõe com o k do resto da base.

## 5. Etapa 3 — sal e semente fora do código

Antes de qualquer generalização, apareceu um problema nos identificadores
diretos: as migrations que trocam valor real por fictício de forma
determinística (CNS, INE, CNES, telefone, CPF, nomes) usavam sal e semente
fixos no código, e o código está no git. Com isso, quem conhece o CNS real de
uma pessoa recalcula o hash e acha o registro: era pseudonimização, não
anonimização. Sais e sementes passaram a ser derivados por HMAC de um segredo
único fora do git (`scripts/segredo.py`), que deve ser destruído junto com a
base original. A migration 04 tinha um caso pior: o deslocamento do dia de
nascimento vinha de `md5(CPF fictício)`, sem sal, e o CPF fictício está na
própria base anonimizada — quem tem a base reverte o deslocamento. Esse ponto
foi resolvido na etapa 6, com a data de nascimento passando a vir do
k-anonimato.

## 6. Etapa 4 — referência de utilidade (experimento 01)

Como a original vai ser apagada, as estatísticas contra as quais a utilidade
será medida precisam ser calculadas agora. O experimento 01 grava, para a
original, a pirâmide etária (em anos e, abaixo de 5 anos, em meses), a
distribuição por equipe, sexo e faixa, raça/cor por faixa, a antropometria
por sexo e ciclo de vida (média e quantis) e a prevalência de cada código
CID-10 e CIAP-2 por sexo e ciclo de vida. O mesmo script roda em qualquer
versão anonimizada (`--banco`). Essas tabelas têm contagens pequenas e devem
ser apagadas junto com a original.

## 7. Etapa 5 — o algoritmo do núcleo e a varredura de k (experimento 02)

### 7.1 Evolução do algoritmo

O núcleo começou com sexo, data de nascimento, equipe, tercil e raça/cor. A
data de nascimento não pode virar faixa (o PEC calcula a idade a partir dela),
então a generalização foi feita por microagregação: dentro de cada grupo de
QI categóricos, as datas são ordenadas e cortadas em blocos de pelo menos k
pessoas, e todos do bloco recebem a mesma data.

A primeira versão dividia primeiro pelos atributos categóricos e depois
microagregava a data. Com k = 10, ela mantinha raça/cor e tercil (0,8% e 1,6%
suprimidos), mas deslocava a data de bebês em 322 dias na mediana: os ~240
grupos tinham ~50 pessoas de 0 a 90 anos, e qualquer bloco de 10 datas
misturava bebês com crianças mais velhas. A segunda versão fazia o inverso
(data primeiro, dentro de sexo × equipe): bebês com 64 dias de deslocamento,
mas raça/cor 100% suprimida e tercil suprimido para todos que o tinham. As
duas versões também deixavam algumas classes de tamanho 1. Isso indica que
não há um ponto que preserve tudo; existe uma fronteira de troca.

A versão final (`nucleo_adaptativo`) fica entre os extremos: corta por ciclo
de vida antes (bebês só concorrem com bebês da mesma equipe e sexo, então os
blocos de data deles são estreitos), suprime atributos categóricos numa
ordem de prioridade só em grupos que não alcançam k, e faz o grupo residual
(tudo suprimido) absorver subgrupos inteiros até alcançar k. Duas correções
vieram de testes: uma equipe com um único cidadão vinculado deixava a classe
com 1 pessoa (a equipe vinculada dessas pessoas deixa de ser publicada), e
pessoas sem equipe ou sem sexo informado podiam formar grupos pequenos (o
grupo absorve pessoas do maior grupo vizinho). Equipe não é generalizada de
modo geral porque aparece em cada atendimento — suprimi-la no vínculo não
esconderia nada. O tercil é um atributo do domicílio: suprimi-lo para uma
pessoa suprime para a família inteira, o que gera um efeito em cascata
(a criança de um domicílio cai num grupo pequeno e os adultos perdem o tercil
junto).

### 7.2 O modelo de ameaça

A primeira varredura revelou o resultado mais importante do trilho: o k só
vale para os atributos que entram no cálculo dele. Como as classes do núcleo
têm entre k e 2k−1 pessoas, somar um único atributo publicado as divide. Com
k = 10, acrescentar município de nascimento põe 92,6% das pessoas em classe
menor que k; escolaridade, 96,0%; município de residência, 75,8%; ocupação,
68,9%. Isso é a chamada maldição da dimensionalidade do k-anonimato
(Aggarwal, 2005): cada atributo que o atacante conhece tem de estar no
cálculo, e cada atributo a mais exige classes maiores.

Isso transformou a escolha de parâmetros numa decisão de modelo de ameaça.
Ficou definido (07/10/2026) que o atacante conhece sexo, data de nascimento,
equipe, tercil, raça/cor, escolaridade (agrupada em 5 níveis: nenhuma,
infantil, fundamental, médio, superior) e estado civil. Município de
nascimento, de residência e ocupação ficaram fora do k; neles, valores com
menos de k pessoas viram nulo. A ordem de supressão é estado civil →
escolaridade → raça/cor → tercil, do atributo de menor valor para a
população sintética ao de maior.

### 7.3 A varredura e a escolha de k

Com esse modelo, a varredura aplicou o tratamento completo para k ∈ {2, 3, 5,
10, 15, 20, 30} sobre os 11.604 registros de `tb_cidadao` e mediu, para cada
k, a fração suprimida de cada atributo e o deslocamento da data de
nascimento por faixa etária. Na variante com corte por ciclo de vida:

| k | estado civil | escolaridade | raça/cor | tercil | data, < 2 anos | 20–59 | 60+ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3 | 66% | 6% | 4% | 15% | 50 d | 80 d | 199 d |
| 5 | 86% | 16% | 8% | 34% | 69 d | 195 d | 464 d |
| 10 | 100% | 36% | 23% | 76% | 98 d | 348 d | 580 d |
| 20 | 100% | 55% | 35% | 99% | 187 d | 583 d | 778 d |

(supressão = fração dos que tinham o atributo preenchido; data = deslocamento
mediano). Sem o corte por ciclo, o tercil sobrevive muito mais (5% suprimido
com k = 5), mas a data de bebês desloca 297 dias com k = 5 e anos com k ≥ 10.
A variante com corte por ciclo foi adotada.

Foi adotado k = 5, no cotovelo da curva: risco máximo de 0,2 por classe, com
escolaridade e raça/cor mantidas para mais de 84% das pessoas, 66% do tercil
e deslocamento mediano de cerca de 2 meses em bebês e 6 em adultos. Uma
leitura possível do comportamento por idade é que idosos deslocam mais por
serem mais esparsos: há menos pessoas por ano de nascimento, então os blocos
de k pessoas cobrem intervalos maiores. O estado civil quase some, mas estava
preenchido para só 5% das pessoas.

## 8. Etapa 6 — antropometria (migration 08)

O hash provisório da 08 destruía o dado (nenhuma distribuição de peso ou
altura sobrevivia) e não protegia: campo numérico com poucos milhares de
valores plausíveis é revertido por força bruta. A antropometria tem 115.074
medições em `tb_medicao` (peso em 104.382, altura em 48.957, IMC em 48.922,
perímetro cefálico em 7.368), com erros de digitação visíveis (peso de 500 kg,
IMC de 2.721,1).

O tratamento: por variável, os valores abaixo do quantil 0,1% e acima de
99,9% vão para a faixa da ponta, e os valores ordenados são agrupados em
blocos com pelo menos k = 5 pessoas distintas; cada valor vira a mediana do
bloco. A mediana substituiu a média depois de um teste mostrar que, numa
amostra pequena, um erro de digitação que escapa do corte puxava a média do
último bloco. A regra é uma tabela de faixas que depende só do valor, então
o mesmo peso vira o mesmo número em qualquer tabela, operacional ou DW, sem
ligar cada linha à sua medição; o IMC é recalculado do peso e da altura
publicados. A varredura mediu distorção desprezível: a distância de
Wasserstein entre as distribuições original e tratada ficou em ~0,1% do
desvio padrão, e a correlação peso × altura passou de 0,844 para 0,852. Duas
tabelas do DW com peso e altura (`tb_fat_rel_op_crianca` e
`tb_fat_visita_domiciliar`) não estavam na lista antiga e foram incluídas.

## 9. Etapa 7 — doenças raras (migration 16) e l-diversidade

Um diagnóstico raro identifica sozinho e, com o núcleo, ainda mais. A
regra adotada é que todo código publicado tenha pelo menos k = 5 pessoas
distintas na base inteira. A alternativa de exigir k dentro de cada sexo ×
ciclo de vida (atacante que sabe o diagnóstico e a faixa da pessoa) foi
medida e descartada: com k = 5, generalizava 80% dos pares
pessoa-diagnóstico, contra 3,2% na regra global.

A recodificação é global e por código: CID-10 raro sobe para a categoria de 3
caracteres e, se ainda raro, é suprimido; CIAP-2 raro é suprimido, porque o
catálogo não tem nível intermediário para onde subir. As colunas tratadas
foram achadas pelas chaves estrangeiras para os catálogos (`tb_cid10`,
`tb_ciap`, `tb_dim_cid`, `tb_dim_ciap`), excluindo tabelas de referência, mais
as cópias `ta_`/`tl_`: 54 colunas ao todo. Calculado sobre a base real, dos
2.752 códigos CID, 765 ficam, 867 sobem para a categoria e 1.120 são
suprimidos; dos 596 CIAP, 354 ficam e 242 são suprimidos. Isso muda 21.296
de 1.094.007 linhas com diagnóstico (~2%), mas atinge 25% das pessoas, que
têm pelo menos um código raro.

A l-diversidade foi medida sobre as classes do núcleo publicado, para oito
condições sensíveis (HIV/aids, tuberculose, hanseníase, IST, transtorno
mental, uso de substância, gestação/aborto e violência). Mediram-se duas
formas de exposição: a pessoa estar numa classe homogênea (todos da classe
têm a condição: quem conhece a classe descobre o diagnóstico com certeza) e
estar numa classe em que a condição é maioria (o diagnóstico fica provável).

Com k = 5 e o modelo de ameaça adotado, as condições raras e mais
estigmatizadas ficam sem exposição nenhuma: HIV/aids (6 pessoas), violência
(6), tuberculose (5), uso de substância (23) e IST (45) não aparecem em
classe homogênea nem em classe com maioria (hanseníase não ocorre na base).
A exposição fica concentrada em duas condições comuns: gestação/aborto, com
50 das 916 pessoas (5,5%) em classe homogênea e 48,8% em classe com maioria;
e transtorno mental, com 5 das 2.280 (0,2%) e 34,2%. Com k = 2, essas frações
eram de 41,4% e 24,8% em classe homogênea; a partir de k = 15 nenhuma pessoa
fica em classe homogênea, mas a gestação continua majoritária em ~40% dos
casos até k = 30.

Uma leitura possível é que a gestação expõe mais porque se concentra num
subgrupo que o próprio núcleo isola (mulheres em idade fértil, numa equipe):
é a limitação conhecida da l-diversidade com atributos frequentes dentro de
um subgrupo, que t-closeness trata. O resultado indica que o k = 5 basta para
as condições raras, mas não impede inferência de gestação para cerca de 50
pessoas; tratar isso (impor l-diversidade por fusão de classes, ou aceitar o
risco por ser atributo pouco estigmatizado e inferível pelo próprio perfil)
é uma decisão em aberto. Transtorno mental inclui o capítulo P inteiro da
CIAP, que tem sintomas comuns, o que provavelmente infla sua prevalência
(2.280 pessoas, ~20% da população) — a definição da lista de condições
sensíveis deve ser revista antes de citar esse número.

## 9b. Mudança das distribuições (experimento 05)

Além de quanto é suprimido, importa quanto a forma das distribuições muda,
porque é a forma que a geração sintética vai aprender. O experimento 05
compara, para k ∈ {2, 3, 5, 10, 15, 20, 30}, a distribuição original e a
publicada de cada variável tratada, com a divergência de Kullback-Leibler
KL(original ‖ tratada) — quanta informação se perde ao usar a tratada no
lugar da original — e com Jensen-Shannon, que é simétrica e vai de 0 a 1.
As duas são calculadas em faixas fixas, iguais para as duas distribuições,
com suavização aditiva de 0,5 por célula: sem ela a KL é infinita sempre
que a tratada zera uma faixa que a original tem, e a microagregação e a
supressão fazem exatamente isso. A suavização afeta a magnitude absoluta da
KL; as comparações entre variáveis e entre valores de k, feitas com a mesma
suavização, são o que importa.

Com k = 5, a antropometria praticamente não muda (KL ≈ 0,001 para peso e
IMC, 0,002 para altura). A idade em anos muda pouco (KL = 0,038; JS =
0,012), assim como escolaridade (0,050), estado civil (0,077), raça/cor
(0,090) e a distribuição sobre os códigos de diagnóstico (0,055). O que
muda bastante é a idade em meses abaixo de 5 anos (KL = 0,616; JS = 0,167):
os blocos de data dos bebês têm cerca de 2 meses, a distribuição mês a mês
fica cheia de dentes, e 12,5% das crianças com menos de 60 meses na
original passam de 60 meses na tratada. Nas categóricas, a mudança é quase
toda a migração para "não informado" (raça/cor: 0% → 8%; escolaridade: 17%
→ 30%). Com k crescente, a KL sobe em todas as variáveis; a idade em meses
chega a 1,0 com k = 10 e a 2,1 com k = 30, e a escolaridade a 1,1 com k = 30.

Uma leitura possível é que, com k = 5, a base guardada preserva a forma das
distribuições usadas na geração sintética, com a exceção da idade fina das
crianças pequenas — exatamente a resolução que o kit DP guarda (idade em
anos por sexo) e que o modelo sintético teria de recuperar de lá. Se a
idade em meses for necessária (calendário vacinal, puericultura), isso
pesa a favor de um k menor ou de um tratamento específico para menores de 2
anos.

## 10. Etapa 8 — as migrations e o que os dados revelaram

O núcleo virou a migration 15, que roda depois da 06 (usa o tercil gravado
por ela) e da 13 (a equipe já fictícia dá os mesmos grupos). Ela calcula o
k-anonimato sobre todo `tb_cidadao` e as pessoas que só existem no cadastro
individual CDS, e propaga a data publicada e os atributos suprimidos para
todas as cópias: `ta_/tb_/tl_cidadao` pelo código do cidadão, cadastro CDS
pela cadeia de versões, CPF ou CNS, e DW pelo CPF/CNS. Antes de gravar, ela
confere o k sobre os valores publicados e aborta se alguma classe ficar
abaixo de k. Calculada sobre a base real (sem gravar), a população foi de
12.434 pessoas e a trava passou.

Montar a 15 revelou problemas nos dados e na fase 1:

- a 04 só alterava linhas com CPF, então cerca de 11% dos cidadãos saíam com
  a data de nascimento original em todas as tabelas — a 15 cobre todas as
  linhas, e quem não se liga a ninguém recebe uma data microagregada na
  própria tabela;
- 20% das linhas do cadastro individual (26.902) não se ligavam a nenhum
  cidadão; quase todas eram versões antigas de cadastros, ligadas à pessoa
  pela cadeia de versões, e restaram 830 pessoas que só existem no CDS, que
  entraram na população do k;
- `tb_acomp_cidadaos_vinculados` guardava uma cópia completa do endereço e da
  micro-área, sem tratamento — passou a ser suprimida na 06 e na 14;
- cerca de 2% das pessoas já têm, na original, data de nascimento posterior à
  primeira medição registrada — é dado da base, não efeito do tratamento.

## 11. Etapa 9 — o kit de differential privacy (experimento 03)

### O que é e por que existe

O k-anonimato engrossa o dado de forma permanente: a idade vira um bloco, a
doença rara vira categoria ou some, o peso vira a mediana de um grupo. Para
gerar populações sintéticas, essa resolução fina faz falta, e depois do
prazo não haverá como recuperá-la. O kit guarda essa resolução com garantia
formal: são tabelas de contagem (marginais) medidas agora na original, com
ruído calibrado. Pela propriedade de pós-processamento da DP, qualquer coisa
derivada do kit continua protegida, então ele pode ser mantido sem prazo.
É o mesmo insumo que métodos de geração sintética como MST e AIM usam.

### Como foi feito

As marginais cobrem o modelo de pessoas (sexo × idade em grupos de 5 anos ×
equipe; × raça × escolaridade; × equipe × tercil; × estado civil; idade ×
raça × equipe), a idade em anos por sexo, os diagnósticos (pessoas por código
e capítulo × sexo × faixa) e a antropometria (peso, altura e IMC por sexo e
idade). Cada pessoa contribui no máximo uma vez por marginal (até 10
diagnósticos; a última medição de cada variável), o que limita a
sensibilidade. O ruído é gaussiano discreto, sorteado pela biblioteca OpenDP
(e não por código próprio, porque amostrar ruído em ponto flutuante de forma
ingênua tem falhas de privacidade conhecidas); o orçamento é contado em zCDP,
dividido igualmente entre as marginais e convertido para (ε, δ) com
δ = 10⁻⁶.

A primeira versão usava antropometria por quilo × idade em anos (~30 mil
células) e diagnóstico × sexo × faixa (~40 mil): com 11,6 mil pessoas, quase
todas as células tinham 0 a 2 pessoas, e o resultado foi só ruído (distância
de variação total de ~0,8 com ε = 1). A granularidade foi ajustada ao tamanho
da população (faixas de 2,5 kg e 2,5 cm, idade em grupos de 5 anos,
diagnóstico separado em contagem por código e distribuição por capítulo).

### A varredura de ε

Para ε ∈ {0,1; 0,5; 1; 2; 5; 10; 20}, o kit foi sorteado e comparado com a
verdade. Além do erro de cada marginal, foi ajustado um modelo gráfico
(private-pgm) só com as marginais de pessoas, e medida a fidelidade em três
combinações de 3 atributos que não foram medidas — que é o que a geração
sintética precisa extrapolar.

| ε | idade × sexo × equipe | raça × escolaridade | por diagnóstico | peso × idade | modelo, não medidas (média) |
|---|---:|---:|---:|---:|---:|
| 1 | 0,15 | 0,66 | 0,31 | 0,59 | 0,30 |
| 2 | 0,07 | 0,53 | 0,18 | 0,46 | 0,21 |
| 5 | 0,03 | 0,31 | 0,09 | 0,27 | 0,16 |
| 10 | 0,02 | 0,20 | 0,05 | 0,16 | 0,14 |

(distância de variação total; menor é melhor). A fidelidade do modelo nas
combinações não medidas praticamente para de melhorar a partir de ε ≈ 5.
Uma leitura possível é que, daí em diante, o limite passa a ser o que o modelo
não mediu, e não o ruído. Para as doenças raras, com ε = 5 o ruído por código
tem desvio-padrão de ~12 pessoas, e um código com 1 a 4 pessoas fica
indistinguível de zero — que é a proteção funcionando. A recomendação é
ε = 5; a escolha final cabe ao pesquisador e ao orientador. Só um kit será
gravado: guardar kits com ε diferentes somaria os custos de privacidade.

## 12. Estado atual e lacunas

- **ε não escolhido**: o kit não foi gravado. Precisa ser feito antes do
  prazo (`03_kit_dp.py --gravar --epsilon X`).
- **Não aplicado na base real**: as migrations 08, 15 e 16 foram testadas no
  Postgres efêmero e calculadas (sem gravar) sobre a base real. A pipeline
  completa (v00 a v16) ainda não rodou até o fim: a última execução parou na
  05 por queda de conexão.
- **Validação pendente**: falta medir o k na versão final gravada (rodar o
  00 sobre a v16) e comparar a utilidade (rodar o 01 na v16 e os relatórios
  do PEC na original e na final).
- **Limitações assumidas**: município de nascimento, de residência e
  ocupação estão fora do k por decisão de modelo de ameaça; se forem de
  conhecimento do atacante, o risco residual é alto. A 04 ainda desloca datas
  de atendimento com `md5(CPF fictício)`, reversível; como essas datas são
  mantidas reais pela decisão de desenho, isso não expõe além do que já é
  publicado.
- **Validação de cores**: as figuras usam uma paleta documentada como segura
  para daltonismo, mas o validador automático não pôde ser executado (falta
  `node` no ambiente).

## Notas de rastreabilidade

- Escada de QI, efeito de tirar cada um, generalização da data:
  `resultados/00_quase_identificadores_*.json`; figuras `01`, `02`, `03`.
- Versões anteriores do algoritmo (322 d / 64 d, supressão 0,8% / 100%):
  medições ad hoc registradas no histórico da sessão de 07/10/2026; não há
  JSON gravado — reproduzir antes de citar.
- Efeito de cada QI fora do núcleo (92,6%, 96,0%, 75,8%, 68,9%, k = 10):
  medição ad hoc da mesma sessão; não há JSON — reproduzir antes de citar.
- Tabela de k e variante sem ciclo: `resultados/02_varredura_k_*.json`
  (execução completa mais recente); figuras `04`, `05`, `06`.
- Diagnósticos (3,2% / 80% / 25%): `02_varredura_k_*.json`; figura `07`.
- l-diversidade (k = 5: gestação 5,5% / 48,8%; transtorno mental 0,2% / 34,2%;
  demais 0): `02_varredura_k_20261007_122432.json` (varredura final com
  `pessoas_com_condicao`); figuras `10` e `11`.
- Antropometria (Wasserstein, correlação 0,844 → 0,852): `02_varredura_k_*.json`.
- Contagens da migration 16 (2.752 / 596 códigos; 21.296 de 1.094.007 linhas)
  e da 15 (12.434 pessoas): execuções em modo leitura da sessão; reproduzíveis
  com as funções `decidir` e `calcular` das migrations.
- Achados de dados (04 só com CPF, 26.902 linhas sem ligação, cópia de
  endereço em `tb_acomp_cidadaos_vinculados`, 2% de nascimento após medição):
  consultas da sessão; registrados em `README.md` (Decisões tomadas).
- Varredura de ε: `resultados/03_varredura_epsilon_*.json`; figuras `08`, `09`.
- Mudança das distribuições (KL e JS por variável e por k):
  `resultados/05_distribuicoes_*.json`; figuras `12` a `15`.
- Decisões (k = 5, modelo de ameaça, variante, ε recomendado) e prazo:
  `README.md`, seção "Decisões tomadas".
- Metodologia em diagrama: figura `00_metodologia_trilho_a`.
