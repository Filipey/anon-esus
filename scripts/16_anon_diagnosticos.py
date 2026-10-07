"""Migration 16 - Doenças raras: generalização de diagnóstico com k pessoas.

Um diagnóstico raro identifica a pessoa sozinho ("a única pessoa com doença X
na base") e, junto com os quase-identificadores, também. A guideline manda
proteger doenças raras; a decisão de 07/10/2026 (`experimentos/k-anonimato-dp/`)
foi k global por código: todo código CID-10/CIAP-2 publicado precisa
aparecer em pelo menos `K` pessoas distintas.

Recodificação global, decidida por código (`k_anonimato.diagnosticos`):

- CID-10: subcategoria rara (ex.: A001) sobe para a categoria (A00), que
  existe como linha própria em `tb_cid10`; categoria ainda rara é suprimida
  (não há linha de capítulo no catálogo para onde subir);
- CIAP-2: código raro é suprimido (o catálogo não tem nível intermediário);
- o mesmo código vira o mesmo publicado em toda a base, operacional e DW.

Raridade: pessoas distintas por código nos problemas do DW
(`tb_fat_atd_ind_problemas`, `tb_fat_atend_odonto_problemas`), que ligam cada
diagnóstico ao cidadão. Código que só aparece fora deles é raro se tiver
menos de `K` linhas no total — linhas são um teto para pessoas, então nada
raro escapa por esse caminho.

Colunas: as que têm chave estrangeira para `tb_cid10`, `tb_ciap`, `tb_dim_cid`
e `tb_dim_ciap` em tabelas de dado de pessoa (as de referência, como
`rl_ciap_cid10`, ficam de fora), mais as cópias `ta_`/`tl_` com o mesmo
nome de coluna. Suprimir: nulo no operacional; "não informado" no DW. A
categoria que faltar em `tb_dim_cid` é criada a partir do nome em `tb_cid10`.

Atômica: tudo numa transação.
"""

from __future__ import annotations

import pandas as pd
from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

import k_anonimato as ka

log = get_logger("16_anon_diagnosticos")

K = 5

# (tabela, coluna, sistema) com diagnóstico de pessoa; ta_/tl_ são achadas em tempo de execução.
COLUNAS_OPERACIONAIS: list[tuple[str, str, str]] = [
    ("rl_evolucao_avaliacao_ciap_cid", "co_cid10", "CID"),
    ("rl_evolucao_avaliacao_ciap_cid", "co_ciap", "CIAP"),
    ("rl_evolucao_subjetivo_ciap", "co_ciap", "CIAP"),
    ("rl_evolucao_plano_ciap", "co_ciap", "CIAP"),
    ("rl_cds_atend_individual_ciap", "co_ciap", "CIAP"),
    ("rl_atend_proced", "co_cid10_principal", "CID"),
    ("tb_problema", "co_cid10", "CID"),
    ("tb_problema", "co_ciap", "CIAP"),
    ("tb_atestado", "co_cid10", "CID"),
    ("tb_encaminhamento", "co_cid10", "CID"),
    ("tb_encaminhamento", "co_ciap", "CIAP"),
    ("tb_guia_encaminhamento", "co_cid10", "CID"),
    ("tb_guia_encaminhamento", "co_ciap", "CIAP"),
    ("tb_requisicao_exame", "co_cid10", "CID"),
    ("tb_cuidado_compartilhado", "co_cid10", "CID"),
    ("tb_cuidado_compartilhado", "co_ciap", "CIAP"),
    ("tb_antecedente_familiar_ciap", "co_ciap", "CIAP"),
    ("tb_cds_atend_individual", "co_cid10", "CID"),
    ("tb_cds_atend_individual", "co_cid10_2", "CID"),
    ("tb_cds_vacina", "co_cid10_motivo_indicacao", "CID"),
    ("tb_registro_vacinacao", "co_cid10_motivo_indicacao", "CID"),
    ("tb_sinan_notificacao", "co_cid10_principal", "CID"),
    ("tb_tecido_mole", "co_cid10", "CID"),
]
COLUNAS_DW: list[tuple[str, str, str]] = [
    ("tb_fat_atd_ind_problemas", "co_dim_cid", "CID"),
    ("tb_fat_atd_ind_problemas", "co_dim_ciap", "CIAP"),
    ("tb_fat_atend_odonto_problemas", "co_dim_cid", "CID"),
    ("tb_fat_atend_odonto_problemas", "co_dim_ciap", "CIAP"),
    ("tb_fat_atd_ind_encaminhamentos", "co_dim_cid10", "CID"),
    ("tb_fat_atd_ind_encaminhamentos", "co_dim_ciap2", "CIAP"),
    ("tb_fat_cuidado_compartilhado", "co_dim_cid", "CID"),
    ("tb_fat_cuidado_compartilhado", "co_dim_ciap", "CIAP"),
    ("tb_fat_vacinacao_vacina", "co_dim_cid_motivo_indicacao", "CID"),
]
DW_NAO_INFORMADO = {"CID": 1, "CIAP": 1}  # linhas "-" de tb_dim_cid e tb_dim_ciap
CATALOGO = {"CID": ("tb_cid10", "co_cid10", "nu_cid10"), "CIAP": ("tb_ciap", "co_seq_ciap", "co_ciap")}
DIMENSAO = {"CID": ("tb_dim_cid", "co_seq_dim_cid", "nu_cid"), "CIAP": ("tb_dim_ciap", "co_seq_dim_ciap", "nu_ciap")}


def _colunas(conn: Connection, tabela: str) -> dict[str, str]:
    return dict(conn.execute(text(
        "SELECT column_name, is_nullable FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t"), {"t": tabela}).all())


def _alvos_operacionais(conn: Connection) -> list[tuple[str, str, str]]:
    alvos = []
    for tabela, coluna, sistema in COLUNAS_OPERACIONAIS:
        for prefixo in ("", "ta_", "tl_"):
            t = tabela if not prefixo else prefixo + tabela.split("_", 1)[1]
            if coluna in _colunas(conn, t):
                alvos.append((t, coluna, sistema))
    return alvos


def _pessoas_por_codigo(conn: Connection) -> pd.DataFrame:
    """(id da pessoa, sistema, código) dos problemas do DW."""
    partes = []
    for tabela in ("tb_fat_atd_ind_problemas", "tb_fat_atend_odonto_problemas"):
        cols = _colunas(conn, tabela)
        if "co_fat_cidadao_pec" not in cols or not _colunas(conn, "tb_fat_cidadao_pec"):
            continue
        for sistema, col in (("CID", "co_dim_cid"), ("CIAP", "co_dim_ciap")):
            dim, pk, num = DIMENSAO[sistema]
            if col not in cols or not _colunas(conn, dim):
                continue
            partes += conn.execute(text(
                f"SELECT DISTINCT p.co_cidadao, '{sistema}', d.{num} FROM public.{tabela} f "
                f"JOIN public.tb_fat_cidadao_pec p ON p.co_seq_fat_cidadao_pec = f.co_fat_cidadao_pec "
                f"JOIN public.{dim} d ON d.{pk} = f.{col} "
                f"WHERE d.{num} IS NOT NULL AND d.{num} NOT IN ('-', '')")).all()
    df = pd.DataFrame(partes, columns=["id", "sistema", "codigo"])
    df["codigo"] = df["codigo"].astype(str).str.strip().str.upper()
    return df


def _linhas_por_codigo(conn: Connection, alvos_op, alvos_dw) -> pd.DataFrame:
    """Total de linhas por código em todas as colunas tratadas."""
    contagens: dict[tuple[str, str], int] = {}
    for tabela, coluna, sistema in alvos_op:
        cat, pk, num = CATALOGO[sistema]
        for codigo, n in conn.execute(text(
                f'SELECT c.{num}, count(*) FROM public."{tabela}" t JOIN public.{cat} c ON c.{pk} = t."{coluna}" '
                f"GROUP BY 1")).all():
            chave = (sistema, str(codigo).strip().upper())
            contagens[chave] = contagens.get(chave, 0) + n
    for tabela, coluna, sistema in alvos_dw:
        dim, pk, num = DIMENSAO[sistema]
        for codigo, n in conn.execute(text(
                f'SELECT d.{num}, count(*) FROM public."{tabela}" t JOIN public.{dim} d ON d.{pk} = t."{coluna}" '
                f"WHERE d.{num} NOT IN ('-', '') GROUP BY 1")).all():
            chave = (sistema, str(codigo).strip().upper())
            contagens[chave] = contagens.get(chave, 0) + n
    return pd.DataFrame([(s, c, n) for (s, c), n in contagens.items()], columns=["sistema", "codigo", "linhas"])


def decidir(pessoas: pd.DataFrame, linhas: pd.DataFrame) -> dict[tuple[str, str], str | None]:
    """(sistema, código) -> código publicado (ele mesmo ou a categoria) ou None (suprimido)."""
    destino: dict[tuple[str, str], str | None] = {}
    if not pessoas.empty:
        d = ka.diagnosticos(pessoas, None, K)
        for sistema, codigo, nivel in d[["sistema", "codigo", "nivel"]].drop_duplicates().itertuples(index=False):
            if nivel == 0:
                destino[(sistema, codigo)] = codigo
            elif sistema == "CID" and nivel == 1 and len(codigo) > 3:
                destino[(sistema, codigo)] = codigo[:3]
            else:
                destino[(sistema, codigo)] = None
    # código fora dos problemas do DW: raro se tiver < K linhas no total
    for sistema, codigo, n in linhas.itertuples(index=False):
        if (sistema, codigo) in destino:
            continue
        if n >= K:
            destino[(sistema, codigo)] = codigo
        elif sistema == "CID" and len(codigo) > 3:
            categoria = linhas[(linhas["sistema"] == "CID") & (linhas["codigo"].str[:3] == codigo[:3])]["linhas"].sum()
            destino[(sistema, codigo)] = codigo[:3] if categoria >= K else None
        else:
            destino[(sistema, codigo)] = None
    return destino


def _mapa_ids(conn: Connection, sistema: str, destino, tabela, pk, num) -> list[dict]:
    ids = dict((str(c).strip().upper(), i) for i, c in conn.execute(text(f"SELECT {pk}, {num} FROM public.{tabela}")).all())
    out = []
    for (s, codigo), novo in destino.items():
        if s != sistema or novo == codigo or codigo not in ids:
            continue
        out.append({"antigo": ids[codigo], "novo": ids.get(novo) if novo else None})
    return out


def _garantir_categorias_dw(conn: Connection, destino) -> None:
    dim, pk, num = DIMENSAO["CID"]
    if not _colunas(conn, dim) or not _colunas(conn, "tb_cid10"):
        return
    existentes = {str(c).strip().upper() for c in conn.execute(text(f"SELECT {num} FROM public.{dim}")).scalars()}
    faltam = sorted({novo for (s, c), novo in destino.items() if s == "CID" and novo and novo != c} - existentes)
    if not faltam:
        return
    nomes = dict(conn.execute(text("SELECT nu_cid10, no_cid10 FROM public.tb_cid10 WHERE nu_cid10 = ANY(:c)"),
                              {"c": faltam}).all())
    proximo = (conn.execute(text(f"SELECT coalesce(max({pk}), 0) FROM public.{dim}")).scalar() or 0) + 1
    cols = _colunas(conn, dim)
    for i, codigo in enumerate(faltam):
        valores = {pk: proximo + i, num: codigo, "no_cid": nomes.get(codigo, codigo)}
        if "st_ativo" in cols:
            valores["st_ativo"] = 1
        if "st_registro_valido" in cols:
            valores["st_registro_valido"] = 1
        conn.execute(text(f"INSERT INTO public.{dim} ({', '.join(valores)}) VALUES "
                          f"({', '.join(':' + k for k in valores)})"), valores)
    log.info("%d categoria(s) CID criada(s) em %s", len(faltam), dim)


def _aplicar(conn: Connection, tabela: str, coluna: str, mapa: list[dict], valor_suprimido) -> int:
    if not mapa:
        return 0
    nullable = _colunas(conn, tabela).get(coluna) == "YES"
    conn.execute(text("CREATE TEMP TABLE _mapa_diag (antigo bigint PRIMARY KEY, novo bigint) ON COMMIT DROP"))
    linhas = [{"antigo": x["antigo"], "novo": x["novo"] if x["novo"] is not None else valor_suprimido}
              for x in mapa]
    if not nullable:
        linhas = [x for x in linhas if x["novo"] is not None]
    if linhas:
        conn.execute(text("INSERT INTO _mapa_diag VALUES (:antigo, :novo)"), linhas)
    n = conn.execute(text(
        f'UPDATE public."{tabela}" t SET "{coluna}" = m.novo FROM _mapa_diag m WHERE t."{coluna}" = m.antigo'
    )).rowcount
    conn.execute(text("DROP TABLE _mapa_diag"))
    return n


def run(engine: Engine) -> None:
    """Executa a migration de forma atômica."""
    log.info("iniciando generalização de diagnósticos raros (k=%d)...", K)
    with engine.begin() as conn:
        alvos_op = [a for a in _alvos_operacionais(conn) if _colunas(conn, CATALOGO[a[2]][0])]
        alvos_dw = [(t, c, s) for t, c, s in COLUNAS_DW
                    if c in _colunas(conn, t) and _colunas(conn, DIMENSAO[s][0])]
        if not alvos_op and not alvos_dw:
            log.info("nenhuma coluna de diagnóstico encontrada — nada a fazer.")
            return
        destino = decidir(_pessoas_por_codigo(conn), _linhas_por_codigo(conn, alvos_op, alvos_dw))
        for sistema in ("CID", "CIAP"):
            todos = [c for (s, c) in destino if s == sistema]
            gen = sum(1 for (s, c), n in destino.items() if s == sistema and n is not None and n != c)
            sup = sum(1 for (s, c), n in destino.items() if s == sistema and n is None)
            log.info("%s: %d código(s), %d generalizado(s), %d suprimido(s)", sistema, len(todos), gen, sup)

        mapas_op = {s: _mapa_ids(conn, s, destino, *CATALOGO[s]) for s in ("CID", "CIAP")
                    if _colunas(conn, CATALOGO[s][0])}
        total = 0
        for tabela, coluna, sistema in alvos_op:
            n = _aplicar(conn, tabela, coluna, mapas_op.get(sistema, []), None)
            log.info('"%s"."%s": %d linha(s)', tabela, coluna, n)
            total += n

        _garantir_categorias_dw(conn, destino)
        for tabela, coluna, sistema in alvos_dw:
            mapa = _mapa_ids(conn, sistema, destino, *DIMENSAO[sistema])
            n = _aplicar(conn, tabela, coluna, mapa, DW_NAO_INFORMADO[sistema])
            log.info('"%s"."%s": %d linha(s)', tabela, coluna, n)
            total += n
        log.info("concluído: %d linha(s) com diagnóstico generalizado ou suprimido.", total)
