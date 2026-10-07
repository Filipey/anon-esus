# Experimento — k-anonimato evoluído + kit DP

Workspace da metodologia final de anonimização da fase 2. Nada aqui roda
pela pipeline: são medições e experimentos que definem os parâmetros (k, ε)
e os algoritmos que depois viram migration.

## Contexto e prazo

A base original será apagada ao fim do período de retenção — **14 dias a
partir de 07/10/2026, ou seja, por volta de 21/10/2026**. Depois disso só
fica a base anonimizada, que será usada para gerar populações sintéticas.
Duas consequências guiam o plano:

1. **A base guardada precisa ser anônima** no sentido da LGPD (art. 12):
   não ser possível reidentificar uma pessoa por meios razoáveis.
2. **Tudo o que depende da original tem de acontecer antes do prazo**:
   escolher parâmetros, medir utilidade contra a original, anotar o
   gabarito do NER e medir as marginais com DP. Nada disso pode ser refeito
   depois.

## O que a primeira medição mostrou

`00_quase_identificadores.py`, sobre os 9.637 cidadãos ativos e vivos da
base original. Os valores valem também para a base da fase 1: a 04 preserva
mês/ano de nascimento, a 13 troca o INE 1:1 e a 06 deriva o mesmo tercil.

| O que o atacante conhece | Cidadãos únicos (k = 1) | Em grupo < 20 |
|---|---:|---:|
| sexo + mês/ano de nascimento | 2,5% | 100% |
| + equipe | 36,9% | 100% |
| + tercil de distância | 67,2% | 100% |
| + raça/cor | **81,2%** | 100% |
| todos os 13 quase-identificadores | 99,0% | 100% |

- O k ≥ 20 da geografia (migration 06) não protege ninguém: sexo + mês/ano
  de nascimento sozinhos já põem 100% da população em grupo menor que 20.
- O nascimento domina: tirá-lo do cenário completo derruba os únicos de 99%
  para 51%; tirar qualquer outro QI muda menos de 2 pontos.
- Generalizar só o nascimento não basta: mesmo em 5 faixas de ciclo de vida,
  20% ficam em grupo < 20 (sobre sexo + equipe + tercil + raça/cor).
- QI que nenhuma migration tratava: município de nascimento (275 valores),
  município de residência (149), ocupação (156).

## Metodologia final

| Camada | Tratamento |
|---|---|
| Identificadores diretos | Substituição por fictício (já existe). **Sal e semente passam a ser segredo fora do git**, destruído junto com a original — com o sal no repositório, o hash é pseudonimização reversível por quem conhece o valor real. |
| Núcleo de QI: sexo, nascimento, equipe, tercil, raça/cor | k-anonimato por microagregação da data de nascimento, com subida na hierarquia quando o grupo não alcança k. |
| QI fora do núcleo: município de nascimento/residência, ocupação | Valor raro vira "outro". |
| Antropometria | Corte dos extremos por idade e sexo + microagregação (MDAV) de peso/altura com o mesmo k. |
| Doenças raras | Código CID/CIAP sobe na hierarquia até a combinação com o núcleo atingir k (k^m-anonimato, m = 1 e 2). l-diversidade medida sobre diagnósticos sensíveis. |
| Texto livre | Pipeline de NER: léxico da base + regex + modelo, avaliado contra gabarito anotado. |
| Kit DP | Marginais com ruído medidas na original antes do prazo, para a geração sintética recuperar a resolução que a generalização remove. |
| Utilidade | Relatórios do PEC na original e na versão final; indicadores equivalentes em script. |

### Por que esta combinação

- **Não "DP para tudo"**: DP local (ruído registro a registro) com ε que
  protege destrói a coerência clínica (sexo trocado, datas deslocadas em
  anos, ruído de dezenas de cm na altura) e os relatórios do PEC; e uma base
  sintética com DP como único artefato seria aposta de tiro único, sem
  possibilidade de correção depois do prazo, e sem a estrutura relacional.
- **Não DP dentro da base para antropometria e doenças raras**: pelo mesmo
  motivo — ruído por registro pior que a generalização, e uma garantia que
  não compõe com o k do resto da base.
- **k-anonimato evoluído + kit DP**: a base guardada fica relacional,
  coerente e com risco medido (k, l); a resolução fina que a generalização
  remove fica no kit DP, que tem garantia formal e pode ser guardado para
  sempre (pós-processamento de saída DP continua DP).

## Experimentos de parâmetro

### k: curva risco × utilidade

Para k ∈ {2, 3, 5, 10, 15, 20, 30}, aplicar o tratamento completo e medir:

- **risco**: no núcleo, por construção, ≤ 1/k; únicos residuais somando os
  QI de fora do núcleo; l-diversidade dos diagnósticos sensíveis;
- **utilidade**: deslocamento da data de nascimento (mediana e p95, em
  dias); distância entre distribuições de idade, peso e altura original ×
  tratada; fração de códigos de doença generalizados; preservação de
  correlações (prevalência por faixa etária, IMC por sexo e idade).

O k escolhido fica no cotovelo da curva.

### ε: erro das marginais × ε

Para ε ∈ {0,1; 0,5; 1; 2; 5; 10; 20}, medir o erro das marginais com ruído
(geral e nas células raras) e a fidelidade de uma população gerada a partir
delas (MST) nos mesmos indicadores. Referências de mercado: ε ≤ 1 é proteção
forte; o Censo dos EUA 2020 somou ~17; ε = 10 aparece em benchmarks, mas é
proteção fraca. **Só o kit escolhido é guardado** — guardar vários soma os ε.

## Plano de implementação

Dois trilhos em paralelo; o B depende de anotação manual.

### Trilho A — k-anonimato e DP

| Dias | Entrega |
|---|---|
| 1 | Sal/semente lidos de segredo fora do git nas migrations com hash. Script de indicadores de referência na original. |
| 1–2 | Algoritmo do núcleo: estratos sexo + equipe + tercil + raça/cor; microagregação 1-D da data de nascimento em blocos ≥ k; estrato < k sobe na hierarquia (sem tercil → raça/cor agrupada → sem equipe). Município e ocupação raros → "outro". |
| 3 | Antropometria: corte de extremos por idade/sexo + MDAV de peso/altura por medição. |
| 3–4 | Doenças raras: inventário de colunas de CID/CIAP, hierarquia subcategoria → categoria → grupo → capítulo, k^m com m = 1 e 2, l-diversidade. |
| 4–5 | Varredura de k e escolha. |
| 5–7 | Migrations: 04 grava a data do k-anonimato; 08 reescrita (microagregação); migration nova para doenças raras. |
| 6–8 | Kit DP: definição das marginais, ruído com biblioteca testada (OpenDP / private-pgm), varredura de ε e escolha. |

### Trilho B — NER

| Dias | Entrega |
|---|---|
| 3 | Amostra estratificada do SOAP (200–300 textos) pré-marcada pela união de léxico, regex e modelos. |
| 4–6 | Correção manual da pré-marcação (gabarito). |
| 7 | Avaliação de cada técnica e da combinação contra o gabarito. |
| 8–9 | Migration de NER, preservando o HTML. |

### Fechamento

| Dias | Entrega |
|---|---|
| 10–11 | Pipeline completa (versões v00–v15+), com keepalive na conexão. |
| 12–13 | Validação: risco na versão final; relatórios do PEC na original e na final; conferência do kit DP. |
| 14 | Folga. Destruição de sal/semente junto com a original. |

## Decisões tomadas (07/10/2026)

| Decisão | Valor | Base |
|---|---|---|
| Modelo de ameaça | O atacante conhece sexo, nascimento, equipe, tercil de distância, raça/cor, **escolaridade** (5 níveis) e **estado civil**. Município de nascimento/residência e ocupação ficam fora do k (valor raro → nulo). | `02_varredura_k.py`: qualquer atributo publicado fora do cálculo do k desfaz a garantia (com k = 10, só a escolaridade põe 96% em classe < k). |
| Variante do núcleo | Corte por ciclo de vida, m = 1 | Datas de criança 3x mais precisas que sem o corte, ao custo de mais tercil suprimido. |
| **k** | **5** | Cotovelo da curva: com k = 5 mantém escolaridade (84%) e raça/cor (92%) e 66% do tercil; deslocamento mediano da data ~2 meses em bebês e ~6 em adultos. Risco máximo 0,2 por classe — limite usual para base de acesso controlado. |
| Diagnósticos | k global por código (não por sexo x ciclo) | Por sexo x ciclo generaliza ~90% dos pares pessoa-código; global, 3% com k = 5. |
| Antropometria | Corte de extremos (0,1% / 99,9%) + microagregação por valor, k pessoas distintas por bloco | Distorção desprezível (Wasserstein ~0,1% do desvio padrão). |
| População do k | `tb_cidadao` (11.604) + pessoas só no CDS (832 cadastros atuais sem cidadão correspondente) | Todas estão na base publicada. Versões antigas do cadastro CDS ligam-se à pessoa pela cadeia `co_unico_ficha_origem`. |

Achados de dado que entram no desenho das migrations:

- a 04 só altera linhas com CPF: ~11% dos cidadãos (sem CPF) saem com a data de nascimento original em todas as tabelas — a migration do núcleo cobre todas as linhas;
- a 04 deriva o deslocamento de `md5(CPF fictício)`, sem sal: quem tem a base anonimizada recalcula o deslocamento. A data de nascimento passa a ser a do k-anonimato; o deslocamento das demais datas (até 30 dias) fica, sem efeito sobre a proteção;
- ~2% das pessoas já têm, na original, data de nascimento posterior à primeira medição;
- a antropometria tem erros de digitação (peso de 500 kg, IMC de 2.721), absorvidos pelo corte de extremos.

## Andamento do Trilho A (07/10/2026)

| Passo | Estado | Onde |
|---|---|---|
| Sal e semente fora do git | feito | `scripts/segredo.py`, `ANON_SEGREDO` no `.env` |
| Estatísticas de referência da original | feito | `01_referencia.py` |
| Algoritmos e varredura de k | feito; k = 5 | `scripts/k_anonimato.py`, `02_varredura_k.py` |
| Migration da antropometria | feito (08 reescrita) | `scripts/08_anon_antropometrico.py` |
| Migration do núcleo | feito (nova 15) | `scripts/15_anon_k_anonimato.py` |
| Migration de doenças raras | feito (nova 16) | `scripts/16_anon_diagnosticos.py` |
| Kit DP e varredura de ε | varredura feita; **ε a escolher** | `03_kit_dp.py` |

A data de nascimento do k-anonimato ficou numa migration nova (15), e não na
04: ela precisa do tercil (06) e da equipe já fictícia (13). A 04 continua;
o dia que ela troca é sobrescrito pela 15.

### Varredura de ε (δ = 10⁻⁶, mesmo ρ por marginal)

Distância de variação total entre a marginal com ruído e a verdadeira:

| ε | sexo x idade5 x equipe | sexo x idade5 x raça x escol. | por código de diagnóstico | peso x sexo x idade5 | modelo: combinações não medidas |
|---|---:|---:|---:|---:|---:|
| 0,5 | 0,26 | 0,76 | 0,47 | 0,67 | 0,32 a 0,51 |
| 1 | 0,15 | 0,66 | 0,31 | 0,59 | 0,21 a 0,35 |
| 2 | 0,07 | 0,53 | 0,18 | 0,46 | 0,12 a 0,26 |
| **5** | **0,03** | **0,31** | **0,09** | **0,27** | **0,06 a 0,22** |
| 10 | 0,02 | 0,20 | 0,05 | 0,16 | 0,06 a 0,20 |
| 20 | 0,01 | 0,12 | 0,03 | 0,09 | 0,05 a 0,20 |

- A fidelidade do modelo nas combinações que não foram medidas para de
  melhorar perto de ε = 5: daí em diante o limite é o que o modelo não
  mediu, não o ruído.
- Doença rara: com ε = 5 o ruído por código tem σ ≈ 12 pessoas; um código com
  1 a 4 pessoas fica indistinguível de zero — é a proteção funcionando.
- Primeira versão usava antropometria por kg x idade em anos (~30 mil
  células) e diagnóstico x sexo x faixa (~40 mil): com 11 mil pessoas, só
  ruído (TVD ~0,8 com ε = 1). A granularidade foi ajustada.

## Pontos de desenho em aberto

1. **Datas de atendimento.** Mudar o nascimento e manter os atendimentos
   reais altera a idade no atendimento na mesma medida (pouco em criança,
   cujo bloco é estreito). Deslocar todas as datas da pessoa destrói a
   sazonalidade. Proposta: manter os atendimentos reais.
2. **Doenças no DW.** O DW guarda o código como chave de dimensão; a
   generalização só funciona se o código-pai existir na dimensão. Se não
   existir, vira supressão no DW.
3. **Medições repetidas de antropometria.** Microagregar cada medição pode
   deixar a curva de crescimento de uma criança irregular; a varredura de k
   mostra o custo.

## Dependências externas

- Relatórios do PEC rodados na original nos primeiros dias (referência de
  utilidade que some no prazo).
- Anotação do gabarito do NER (dias 4–6).
- Faixa aceitável de ε definida com o orientador.

## Como rodar

```bash
cd experimentos/k-anonimato-dp
../../venv/bin/python 00_quase_identificadores.py   # --referencia AAAA-MM-DD fixa a data da idade
```

Conexão read-only no próprio Postgres (lê o `.env` da raiz). Só contagens
saem dos scripts; `resultados/` está no `.gitignore`.
