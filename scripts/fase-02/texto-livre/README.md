# Fase 2 — levantamento de texto livre

Medição e caracterização de todo texto livre da base e-SUS, para embasar
a anonimização por NER (ver `GUIDELINE.md`, linha "Textos livres"). Nada
aqui roda pela pipeline e nada escreve no banco: a conexão é read-only no
próprio Postgres.

> **`resultados/` contém texto clínico real** (script 02 e os arquivos de
> verificação da 04) e está no `.gitignore`. Não copie trechos de lá para
> documento versionado.

## Scripts

Rodar a partir desta pasta, em ordem. Cada script lê o resultado mais
recente do anterior em `resultados/`.

```bash
cd scripts/fase-02/texto-livre
python 00_inventario.py          # todas as colunas textuais: preenchimento, tamanho, HTML, classe
python 01_caracterizacao.py      # conteúdo das colunas de texto clínico: HTML, forma, repetição, dado pessoal, cópias
python 02_exemplos.py            # exemplos reais por coluna (markdown) — NÃO VERSIONAR
python 03_figuras.py             # figuras agregadas (PDF/PNG)
```

| Script | Lê valor de célula? | Saída |
|---|---|---|
| `00_inventario.py` | Não (só agregado no SQL) | `00_inventario_<ts>.json` |
| `01_caracterizacao.py` | Sim, em memória | `01_caracterizacao_<ts>.json` (só contagem) |
| `02_exemplos.py` | Sim | `02_exemplos_<ts>.md` (**texto real**) |
| `03_figuras.py` | Não | `figuras_<ts>/*.pdf,png` |

Opções úteis: `01`/`02 --grupos clinico nome ...` escolhe os grupos (padrão:
só `clinico`); `01 --incluir-curto` estende a caracterização às colunas
`curto`; `02 --colunas tb_x.ds_y ...` restringe os exemplos;
`02 --amostra N --por-estrato K` controla o tamanho.

## Exportação pseudo-anonimizada (04-06)

Texto para os parceiros: receitas, atestados e SOAP com o texto livre
pseudo-anonimizado (`_anon_texto.py`: unidade, município, CPF, CNS, conselho,
telefone, nomes com substituto do mesmo sexo, datas deslocadas por paciente,
idade >= 90). Os três arquivos de uma rodada compartilham `paciente_id`,
deslocamento de data e nomes fictícios; ligam-se pelo `atendimento_prof_id`.

```bash
python 04_exporta.py resultados                       # banco -> 04_receitas_medicamento, 05_atestados, 06_soap (+ verificação)
python 05_sem_html.py resultados/06_soap.csv resultados/06_soap_sem_html.csv
python 05_sem_html.py resultados/05_atestados.csv resultados/05_atestados_sem_html.csv
python 06_junta.py resultados --sem-html              # -> 07_receitas_com_contexto_sem_html.csv (uma linha por receita)
```

Os `*_verificacao.csv` e `*_residuo.txt` têm o texto original: só para
conferência local, nunca para envio. O prefixo numérico dos CSVs é nome de
arquivo (já entregue aos parceiros), não a etapa que o gera.

## Análises linguísticas (07-14)

Leem os CSVs sem HTML da etapa anterior (não o banco) e gravam em
`resultados/<análise>_<ts>/` tabelas CSV e figuras PDF + PNG. Campos: os
quatro do SOAP, a recomendação da receita e o texto do atestado
(`_corpus.CAMPOS`); `--campos` escolhe, `--distintos` tira texto repetido.

```bash
python 07_tamanho.py             # # caracteres e # palavras por texto
python 08_vocabulario.py         # palavras únicas: vocabulário, hapax, TTR, Zipf
python 09_ngramas.py             # unigramas, bigramas e trigramas (sem stopword)
python 10_recusa_negacao.py      # combinações com recusar, rejeitar e negar (todas as formas)
python 11_participios.py         # palavras em -ado, -ada, -ados, -adas
python 12_liwc.py --dic LIWC.dic # categorias do LIWC (dicionário não versionado)
python 13_lftk.py                # atributos "general" do LFTK (amostra de 10 mil por campo)
python 14_detoxify.py            # toxicidade (Detoxify multilíngue, GPU se houver)
```

Dependências além do `requirements.txt` base: `pip install spacy lftk liwc
detoxify` e `python -m spacy download pt_core_news_md`; o Detoxify baixa o
modelo (~1 GB) no primeiro uso.

Figuras: só 6x4 ou 4x3 polegadas (`_corpus.figura`), serifa Computer Modern
sem precisar de LaTeX (CMU Serif se instalada, senão DejaVu Serif; a `cmr10`
do matplotlib não tem acento), sem título (a legenda fica no LaTeX), eixo de
quantidade como "# itens", número com separador de milhar "." e uma cor fixa
por campo em todas as figuras.

Decisões que mudam o resultado:

- Token = sequência de letras; hífen separa ("recusa-se" -> "recusa se").
  N-grama e contexto não atravessam fim de frase nem o " | " de bloco.
- Stopword = lista do spaCy **menos a negação** (não, nem, nunca, sem,
  nada...): em texto clínico ela carrega o sentido ("sem febre").
- `10`: o lema vem de lista explícita de flexões (radical + desinência), não
  do lematizador do spaCy, que toma "Nega" no início da frase por nome
  próprio. "Negativo/negativa" fica de fora.
- `11`: palavra de 5+ letras; substantivo frequente com a mesma terminação
  (pomada, fígado, cunhada, resultado...) fica no CSV marcado e sai das
  figuras.
- `13`: só atributos sem dependência de idioma (legibilidade e dificuldade
  de palavra do LFTK são do inglês); texto quase todo em maiúscula vai para
  minúscula antes do spaCy, senão vira nome próprio.
- `14`: o Detoxify foi treinado em comentário de internet. Caixa alta conta
  como "grito" ("PARASITOSE INTESTINAL" = 0,99; em minúscula, 0,01), então o
  texto vai para minúscula antes de pontuar; termo anatômico de exame
  ("prurido anal", "pênis") continua saindo tóxico/sexual. Conferir
  `detoxify_mais_altos.csv` antes de interpretar.

## Grupos de texto livre

A classe `texto_livre` do `00` só olha a forma (três palavras ou mais), então
junta coisas muito diferentes. `_texto.grupo()` separa por nome de tabela e
de coluna:

| Grupo | O que é | Tratamento |
|---|---|---|
| `clinico` | SOAP, orientação, resultado de exame, encaminhamento, atestado, posologia, observações | alvo do NER |
| `nome` | nome de cidadão, mãe, pai, responsável, profissional | por coluna (migrations 05/09) |
| `endereco` | logradouro, bairro, complemento, referência | por coluna (migration 06) |
| `sistema` | auditoria, revisão, lotes, processamento, erros | logs (migration 12) ou técnico |
| `catalogo` | CID, CIAP, CBO, procedimentos, tipos, `*_filtro` | tabela de referência, não é dado pessoal |

Na base original (set/2026): 483 colunas `texto_livre`, das quais 115 são
`clinico` (1,23 mi células, 407 mil textos distintos, e todo o HTML). Os
scripts 01 e 02 rodam só sobre `clinico` por padrão — a coluna de detalhes da
auditoria sozinha tem 955 mil textos distintos, e caracterizar os outros
grupos não informa nada sobre o NER.

## Como uma coluna vira "texto livre"

O `00` classifica cada coluna `text`/`varchar`/`char`/`json` pelas
linhas preenchidas (limiares no topo do script):

- `texto_livre`: >= 5% das células com tag HTML, **ou** >= 20% com três
  palavras ou mais e tamanho médio >= 15;
- `codigo`: tamanho médio <= 8 ou <= 5% com três palavras (enum, código,
  identificador);
- `curto`: o resto (nomes, rótulos, frases curtas);
- `vazia`: nenhuma célula preenchida.

As tabelas `ta_*` (auditoria) e `tl_*` (revisão) entram de propósito: são
cópias das `tb_*` e guardam o mesmo texto. O `01` mede quanto do texto de
cada `tb_X.col` reaparece nas cópias.

## Limitações

- O banco é `SQL_ASCII` com bytes UTF-8: as regex do `00` rodam no Postgres
  e só usam padrões ASCII. As do `01`/`02` rodam em Python, sobre o texto
  já decodificado.
- Os padrões de dado pessoal (CPF, telefone, data, parentesco...) são
  sensíveis de propósito e dão falso positivo: servem para dimensionar e
  priorizar, não como verdade.
- O match de nome usa o léxico de nomes de cidadão e profissional da
  própria base. Se o banco já passou pelas migrations 05/09, esses nomes
  são fictícios e o match de nome deixa de medir risco real.
