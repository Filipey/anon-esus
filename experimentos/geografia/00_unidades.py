"""Experimento 00 - monta o esqueleto de `unidades_coordenadas.csv`.

Destrava o passo manual: descobre quais sao as unidades que aparecem como
vinculo nos domicilios, puxa CNES/nome/endereco de cada uma, e escreve o CSV
ja com uma linha por unidade - faltando so preencher latitude e longitude.

Precisa rodar **antes da migration 02**, que substitui o CNES e o nome da
unidade. Depois dela nao ha mais como consultar o cadastro publico.

A chave emitida na coluna `co_unidade` e a que aparece **na tabela de
domicilio**, nao a chave primaria da tabela de unidade - e ela que o
`03_faixa_de_distancia.py` usa para casar domicilio com coordenada.

Endereco de unidade de saude e dado institucional publico, entao pode ser
gravado e versionado. Nenhuma coordenada de domicilio ou de cidadao entra
aqui.
"""

from __future__ import annotations

import csv

from _conexao import colunas_de, conectar, consulta, existe_tabela, titulo

CSV_UNIDADES = __import__("pathlib").Path(__file__).resolve().parent / "unidades_coordenadas.csv"

CABECALHO = """\
# Coordenadas das unidades de saude. Preencher latitude e longitude a mao,
# a partir do cadastro publico do CNES ou geocodificando o endereco abaixo.
#
# Gerado por 00_unidades.py. Endereco de unidade e dado institucional
# publico - nenhuma coordenada de domicilio ou de cidadao entra aqui.
#
# co_unidade: chave como aparece na tabela de domicilio (e a que o
#             03_faixa_de_distancia.py usa para casar).
"""

CAMPOS = ["co_unidade", "nu_cnes", "nome_referencia", "endereco_referencia", "latitude", "longitude"]

FONTES_DOMICILIO = ["tb_cds_domicilio", "tb_cds_cad_domiciliar", "tb_fat_cad_domiciliar"]
COLS_UNIDADE_NO_DOMICILIO = ["nu_cnes", "co_unidade_saude", "co_dim_unidade_saude"]

PARTES_ENDERECO = [
    "ds_logradouro", "no_logradouro", "nu_numero",
    "ds_complemento", "no_bairro", "ds_cep", "nu_cep",
]


def _ja_preenchido() -> bool:
    if not CSV_UNIDADES.exists():
        return False
    linhas = [
        l for l in CSV_UNIDADES.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.lstrip().startswith("#")
    ]
    return len(linhas) > 1  # cabecalho + pelo menos uma linha de dado


def main() -> None:
    conn = conectar()
    titulo("00 - Unidades a geocodificar")

    fonte = next((t for t in FONTES_DOMICILIO if existe_tabela(conn, t)), None)
    if fonte is None:
        raise SystemExit("nenhuma tabela de domicilio encontrada")

    cols_dom = colunas_de(conn, fonte)
    col_chave = next((c for c in COLS_UNIDADE_NO_DOMICILIO if c in cols_dom), None)
    if col_chave is None:
        raise SystemExit(
            f"{fonte} nao tem coluna de unidade reconhecida "
            f"({', '.join(COLS_UNIDADE_NO_DOMICILIO)})"
        )

    print(f"  fonte de domicilio: {fonte}")
    print(f"  chave de unidade:   {col_chave}")

    chaves = consulta(
        conn,
        f'SELECT DISTINCT "{col_chave}"::text FROM public."{fonte}" '
        f'WHERE "{col_chave}" IS NOT NULL ORDER BY 1',
    )
    if isinstance(chaves, dict):
        raise SystemExit(f"consulta falhou: {chaves['erro']}")
    chaves = [k[0] for k in chaves]
    print(f"  unidades distintas nos domicilios: {len(chaves)}")

    # Enriquece com nome e endereco, quando der pra casar com a tabela mestra.
    detalhe: dict[str, tuple[str, str]] = {}
    if existe_tabela(conn, "tb_unidade_saude"):
        cols_un = colunas_de(conn, "tb_unidade_saude")
        col_join = col_chave if col_chave in cols_un else ("nu_cnes" if "nu_cnes" in cols_un else None)
        partes = [c for c in PARTES_ENDERECO if c in cols_un]
        if col_join and "no_unidade_saude" in cols_un:
            endereco_sql = (
                "concat_ws(', ', " + ", ".join(f'"{c}"' for c in partes) + ")"
                if partes else "''"
            )
            r = consulta(
                conn,
                f'SELECT "{col_join}"::text, no_unidade_saude, {endereco_sql} '
                f"FROM public.tb_unidade_saude",
            )
            if not isinstance(r, dict):
                detalhe = {k: (nome or "", end or "") for k, nome, end in r}
                print(f"  enriquecidas com nome/endereco: {len(detalhe)} (join por {col_join})")
        else:
            print("  tb_unidade_saude sem coluna de join ou de nome - CSV sai so com a chave")

    if _ja_preenchido():
        destino = CSV_UNIDADES.with_suffix(".csv.novo")
        print(f"\n  ATENCAO: {CSV_UNIDADES.name} ja tem dados. Gravando em {destino.name}")
        print("  para nao sobrescrever coordenadas que voce ja preencheu.")
    else:
        destino = CSV_UNIDADES

    with destino.open("w", encoding="utf-8", newline="") as fh:
        fh.write(CABECALHO)
        w = csv.writer(fh)
        w.writerow(CAMPOS)
        for k in chaves:
            nome, endereco = detalhe.get(k, ("", ""))
            w.writerow([k, k if col_chave == "nu_cnes" else "", nome, endereco, "", ""])

    print(f"\n  Escrito: {destino}")
    print(f"  {len(chaves)} linha(s). Preencha latitude e longitude e rode o 03.")

    titulo("Lembrete de ordem")
    print("  Isto precisa rodar ANTES da migration 02, que substitui o CNES e o")
    print("  nome da unidade. Depois dela o cadastro publico nao e mais")
    print("  consultavel a partir da base.")

    conn.close()


if __name__ == "__main__":
    main()
