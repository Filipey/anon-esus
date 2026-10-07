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
