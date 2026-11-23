"""Etapa 05 - tira o HTML das células de um CSV exportado (`;`, UTF-8 com BOM).

Regras de limpeza em `_limpeza.sem_html`.

Uso: 05_sem_html.py <entrada.csv> <saida.csv>"""

import csv
import sys

from _limpeza import sem_html

csv.field_size_limit(10**9)


def main(entrada: str, saida: str) -> None:
    mudou = 0
    with open(entrada, encoding="utf-8-sig", newline="") as fe, \
            open(saida, "w", encoding="utf-8-sig", newline="") as fs:
        r = csv.reader(fe, delimiter=";")
        w = csv.writer(fs, delimiter=";", quoting=csv.QUOTE_ALL)
        w.writerow(next(r))
        for linha in r:
            nova = [sem_html(c) for c in linha]
            mudou += sum(a != b for a, b in zip(linha, nova))
            w.writerow(nova)
    print(f"{saida}: {mudou} células limpas")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
