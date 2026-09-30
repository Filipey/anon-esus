# Fase 2 — levantamento de texto livre

Medição e caracterização de todo texto livre da base e-SUS, para embasar
a anonimização por NER (ver `GUIDELINE.md`, linha "Textos livres"). Nada
aqui roda pela pipeline e nada escreve no banco: a conexão é read-only no
próprio Postgres.

> **`resultados/` contém texto clínico real** (script 02) e está no
> `.gitignore`. Não copie trechos de lá para documento versionado.

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
