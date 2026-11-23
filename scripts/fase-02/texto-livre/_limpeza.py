"""Remoção do HTML do texto clínico, para leitura em planilha e para as análises.

O PEC grava boa parte do texto clínico como HTML do editor (e às vezes colado
do Word: `<o:p>`, `<!--[if gte mso]>`, `<style>`):

- bloco (`<p>`, `<div>`, `<br>`, `<li>`, `<tr>`, `<h1>`...) vira " | ", já
  que a célula precisa ficar numa linha só;
- demais tags saem sem deixar nada (`<strong>`, `<span>`, `<o:p>`...);
- comentário, `<style>`, `<script>` e `<xml>` saem com o conteúdo;
- entidade vira o caractere (`&nbsp;` -> espaço, `&gt;` -> `>`).

Só conta como tag `<` seguido direto de letra (ou `/`, `!`): "PA < 140" e
"TEC < 2s" digitados fora do HTML ficam como estão."""

import html
import re

LIXO = re.compile(r"<!--.*?-->|<(style|script|xml)\b[^>]*>.*?</\1\s*>", re.I | re.S)
BLOCO = re.compile(r"</?(?:p|div|br|li|ul|ol|tr|td|th|table|h[1-6]|blockquote)\b[^<>]*>", re.I)
TAG = re.compile(r"</?[a-zA-Z][\w:.-]*(?:\s[^<>]*)?/?>|<![^<>]*>")
ENTIDADE = re.compile(r"&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);")
SEPARADOR = "\x00"


def sem_html(texto: str) -> str:
    if not (TAG.search(texto) or ENTIDADE.search(texto)):
        return texto
    t = LIXO.sub(" ", texto)
    t = BLOCO.sub(SEPARADOR, t)
    t = TAG.sub("", t)
    t = html.unescape(t).replace("\xa0", " ")
    blocos = (re.sub(r"\s+", " ", b).strip() for b in t.split(SEPARADOR))
    return " | ".join(b for b in blocos if b)
