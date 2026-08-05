"""Auditoria do schema real do banco.

Le so metadados de tabelas/colunas via `information_schema` - nunca le
valores de celula. Classifica cada coluna por padroes de nome que sugerem
dado sensivel (`CATEGORY_PATTERNS`), cruza contra as colunas declaradas em
cada migration de `scripts/NN_*.py`, e escreve um relatorio em Markdown
(`docs/auditoria_schema.md`) com o que ja esta coberto, o que ainda nao
tem migration, e colunas declaradas numa migration que nao existem mais no
banco (schema mudou).

Nota: o script que gerou a primeira versao de `docs/auditoria_schema.md`
nao foi commitado - este arquivo reconstroi a mesma estrutura de
categorias a partir do relatorio ja existente. Os padroes em
`CATEGORY_PATTERNS` sao um ponto de partida; ajuste e re-rode contra o
schema real sempre que uma migration nova for cogitada.

Uso:
    python scripts/audit_schema.py [--schema public] [--out docs/auditoria_schema.md]
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# Categorias de dado sensivel, na ordem em que devem ser testadas (a
# primeira que bater vence - evita uma coluna cair em duas categorias).
# Cada entrada: (categoria, [padroes ILIKE], detalhe).
# ---------------------------------------------------------------------------
CATEGORY_PATTERNS: list[tuple[str, list[str], str]] = [
    # Mistas primeiro - senao "nu_cpf_cns_responsavel" bateria em "CPF"
    # (prefixo "nu_cpf") antes de chegar aqui.
    ("Identificacao mista", ["%cpf_cns%", "%cpf_cnpj%"], "pode ser CPF/CNS ou CPF/CNPJ; exige regra propria"),
    ("Identificacao", ["co_identificacao"], "pode ser CPF/CNS/UUID; exige coluna de tipo"),
    ("CPF", ["nu_cpf%"], "CPF de cidadao ou profissional"),
    (
        "CNS",
        [
            "nu_cns%",
            "%nu_cns",
            "nu_participante_cns",
            "nu_instituicao_cns",
        ],
        "identificador nacional de saude",
    ),
    ("E-mail", ["%email%"], "endereco de e-mail"),
    (
        "Telefone",
        ["%telefone%", "%fone_%", "nu_celular%", "%celular_cidadao"],
        "contato pessoal",
    ),
    (
        "Endereco",
        [
            "%logradouro%",
            "%bairro%",
            "%cep",
            "%cep_%",
            "%complemento%",
            "%ponto_referencia%",
            "nu_numero",
            "st_sem_numero",
            "nu_domicilio",
            "%latitude%",
            "%longitude%",
        ],
        "endereco",
    ),
    ("Data nascimento", ["dt_nascimento%", "%_nascimento", "%dt_participante_nascimento"], "data de nascimento"),
    (
        "Data registro",
        [
            "dt_inicial_atendimento",
            "dt_final_atendimento",
            "dt_evolucao%",
            "dt_criacao_cuidado",
            "dt_resultado",
            "dt_acesso_prontuario",
            "dt_prontuario_lembrete",
            "dt_visita%",
        ],
        "data de registro/atendimento",
    ),
    ("NIS", ["nu_nis%"], "identificador social"),
    ("Naturalizacao", ["%naturalizacao%", "%portaria_naturalizacao%"], "documento de naturalizacao"),
    ("Obito/DO", ["%obito%"], "numero/documento de obito"),
    ("Prontuario", ["%prontuario%"], "identificador interno"),
    (
        "Documento/anexo",
        ["%arquivo%", "%documento_obito%", "nu_documento%", "bl_arquivo%"],
        "arquivo ou documento anexado",
    ),
    ("Registro profissional", ["%conselho_classe%", "st_registro%"], "registro/conselho profissional"),
    (
        "Nome profissional",
        ["no_profissional%", "no_civil_profissional", "no_social_profissional"],
        "nome do profissional",
    ),
    ("Nome cidadao", ["no_nome%"], "nome de pessoa"),
    ("Nome unidade de saude", ["no_unidade_saude", "no_estabelecimento"], "nome da unidade"),
    ("CNES unidade", ["nu_cnes"], "codigo publico da unidade - risco de reidentificacao"),
    (
        "Antropometria",
        [
            "nu_medicao_peso",
            "nu_medicao_altura",
            "nu_medicao_perimetro_cefalico",
            "nu_medicao_circunf_abdominal",
            "nu_perimetro_panturrilha",
            "nu_medicao_imc",
            "nu_medicao_altura_uterina",
            "nu_circ_abdominal",
            "nu_perim_panturrilha",
        ],
        "dado antropometrico/medicao clinica",
    ),
    ("IP de acesso", ["co_ip", "%_ip", "ds_endereco_ip%", "ds_ip%"], "endereco IP"),
]

# Tabelas identificadas manualmente (busca por nome de tabela, nao de
# coluna - colunas de log costumam ter nomes genericos como `dt_acesso`,
# `co_usuario`, que so fazem sentido como "log" no contexto da tabela).
# `tl_acesso` foi conferida e excluida de proposito - e uma tabela de
# controle de permissao (RBAC), nao um log de acesso.
LOG_TABLES: frozenset[str] = frozenset(
    {
        "tb_auditoria_evento",
        "tb_auditoria_processo",
        "tb_envio_log",
        "tb_historico_acesso",
        "tb_sessao_sincronizacao",
        "tb_ad_transmissao_sessao",
    }
)


def _classify(table_name: str, column_name: str) -> tuple[str, str] | None:
    if table_name in LOG_TABLES:
        return "Log de acesso", "tabela inteira de auditoria/log/sessao - guideline pede exclusao"
    lowered = column_name.lower()
    for categoria, patterns, detalhe in CATEGORY_PATTERNS:
        for pattern in patterns:
            if _ilike(lowered, pattern.lower()):
                return categoria, detalhe
    return None


def _ilike(value: str, pattern: str) -> bool:
    """SQL ILIKE simplificado (so `%` como coringa) para comparar em Python.

    `re.escape` nao escapa `%` (nao e especial em regex), entao o coringa
    e tratado separando por `%` e escapando cada pedaco literal.
    """
    import re

    segments = pattern.split("%")
    regex = "^" + ".*".join(re.escape(segment) for segment in segments) + "$"
    return re.match(regex, value, re.IGNORECASE) is not None


# ---------------------------------------------------------------------------
# Cruzamento com as colunas ja declaradas nas migrations existentes.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DeclaredColumn:
    schema: str
    table: str
    column: str
    migration: str


def _load_module(filename: str) -> ModuleType:
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"nao foi possivel carregar {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def _declared_columns() -> list[DeclaredColumn]:
    """Extrai (schema, tabela, coluna) declarados em cada migration.

    `04_anon_datas_cidadao.py` descobre colunas de registro em tempo de
    execucao (nao ha lista estatica) - so a coluna de nascimento entra
    aqui. `06_anon_endereco.py` declara varias colunas de endereco por
    tabela (`address_columns`), tratado a parte.
    """
    declared: list[DeclaredColumn] = []

    def add(items, migration: str) -> None:
        for item in items:
            declared.append(DeclaredColumn(item.schema, item.table, item.column, migration))

    m01 = _load_module("01_anon_cpf.py")
    add(m01.CPF_COLUMNS, "01_anon_cpf")

    m02 = _load_module("02_anon_unidade_saude.py")
    add(m02.NAME_COLUMNS, "02_anon_unidade_saude")
    add(m02.CNES_COLUMNS, "02_anon_unidade_saude")

    m03 = _load_module("03_anon_email.py")
    add(m03.PERSONAL_EMAIL_COLUMNS, "03_anon_email")
    add(m03.INSTITUTIONAL_EMAIL_COLUMNS, "03_anon_email")

    m04 = _load_module("04_anon_datas_cidadao.py")
    for t in m04.DATE_TABLES:
        declared.append(DeclaredColumn(t.schema, t.table, t.birth_column, "04_anon_datas_cidadao"))

    m05 = _load_module("05_anon_profissional.py")
    add(m05.NAME_COLUMNS, "05_anon_profissional")
    add(m05.REGISTRATION_COLUMNS, "05_anon_profissional")

    m06 = _load_module("06_anon_endereco.py")
    for t in m06.ADDRESS_TABLES:
        for col in t.address_columns:
            declared.append(DeclaredColumn(t.schema, t.table, col, "06_anon_endereco"))

    m07 = _load_module("07_anon_documentos.py")
    add(m07.DOCUMENT_COLUMNS, "07_anon_documentos")

    m08 = _load_module("08_anon_antropometrico.py")
    add(m08.ANTHRO_COLUMNS, "08_anon_antropometrico")

    m09 = _load_module("09_anon_nome_cidadao.py")
    add(m09.NAME_COLUMNS, "09_anon_nome_cidadao")

    m10 = _load_module("10_anon_cns.py")
    add(m10.CNS_COLUMNS, "10_anon_cns")

    m11 = _load_module("11_anon_identificadores_diversos.py")
    for attr in (
        "PRONTUARIO_COLUMNS",
        "PHONE_COLUMNS",
        "NIS_COLUMNS",
        "NATURALIZACAO_NUMBER_COLUMNS",
        "NATURALIZACAO_DATE_COLUMNS",
        "OBITO_COLUMNS",
        "MIXED_ID_COLUMNS",
    ):
        add(getattr(m11, attr), "11_anon_identificadores_diversos")

    return declared


# ---------------------------------------------------------------------------
# Consulta ao banco e geracao do relatorio.
# ---------------------------------------------------------------------------
def _fetch_real_columns(engine, schema: str) -> list[tuple[str, str, str, str]]:
    from sqlalchemy import text

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT table_schema, table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = :schema
                ORDER BY table_name, column_name
                """
            ),
            {"schema": schema},
        )
        return [(r.table_schema, r.table_name, r.column_name, r.data_type) for r in rows]


def _write_report(
    out_path: Path,
    real_columns: list[tuple[str, str, str, str]],
    declared: list[DeclaredColumn],
) -> None:
    declared_by_key = {(d.schema, d.table, d.column): d.migration for d in declared}
    real_keys = {(s, t, c) for s, t, c, _ in real_columns}

    suspeito: list[tuple[str, str, str, str]] = []
    coberto: list[tuple[str, str, str, str]] = []

    for schema, table, column, data_type in real_columns:
        classified = _classify(table, column)
        if classified is None:
            continue
        categoria, detalhe = classified
        key = (schema, table, column)
        if key in declared_by_key:
            coberto.append((categoria, f"{schema}.{table}.{column}", data_type, declared_by_key[key]))
        else:
            suspeito.append((categoria, f"{schema}.{table}.{column}", data_type, detalhe))

    ausentes = sorted(
        (d.migration, f"{d.schema}.{d.table}.{d.column}")
        for d in declared
        if (d.schema, d.table, d.column) not in real_keys
    )

    resumo: dict[tuple[str, str], int] = {}
    for categoria, *_ in suspeito:
        resumo[("Suspeito nao coberto", categoria)] = resumo.get(("Suspeito nao coberto", categoria), 0) + 1
    for categoria, *_ in coberto:
        resumo[("Coberto", categoria)] = resumo.get(("Coberto", categoria), 0) + 1

    lines: list[str] = []
    lines.append("# Auditoria do schema real")
    lines.append("")
    lines.append("O script le apenas metadados de tabelas/colunas; nao le valores de celulas.")
    lines.append("")
    lines.append(f"- Tabelas inspecionadas: {len({(s, t) for s, t, _, _ in real_columns})}")
    lines.append(f"- Colunas inspecionadas: {len(real_columns)}")
    lines.append(f"- Achados cobertos: {len(coberto)}")
    lines.append(f"- Achados suspeitos nao cobertos: {len(suspeito)}")
    lines.append(f"- Colunas declaradas em migrations mas ausentes no banco: {len(ausentes)}")
    lines.append("")
    lines.append("## Resumo por categoria")
    lines.append("")
    lines.append("| Status | Categoria | Quantidade |")
    lines.append("|---|---|---|")
    for (status, categoria), qtd in sorted(resumo.items()):
        lines.append(f"| {status} | {categoria} | {qtd} |")
    lines.append("")
    lines.append("## Suspeito nao coberto")
    lines.append("")
    lines.append("| Categoria | Coluna | Tipo | Detalhe |")
    lines.append("|---|---|---|---|")
    for categoria, coluna, tipo, detalhe in sorted(suspeito):
        lines.append(f"| {categoria} | `{coluna}` | `{tipo}` | {detalhe} |")
    lines.append("")
    lines.append("## Coberto")
    lines.append("")
    lines.append("| Categoria | Coluna | Tipo | Migration |")
    lines.append("|---|---|---|---|")
    for categoria, coluna, tipo, migration in sorted(coberto):
        lines.append(f"| {categoria} | `{coluna}` | `{tipo}` | {migration} |")
    lines.append("")
    lines.append("## Declarado nas migrations, ausente no banco")
    lines.append("")
    if ausentes:
        lines.append("| Migration | Coluna |")
        lines.append("|---|---|")
        for migration, coluna in ausentes:
            lines.append(f"| {migration} | `{coluna}` |")
    else:
        lines.append("Nenhuma coluna declarada ficou ausente.")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", default="public")
    parser.add_argument("--out", default=str(ROOT / "docs" / "auditoria_schema.md"))
    args = parser.parse_args()

    connect = _load_module("00_connect_db.py")
    engine = connect.engine

    real_columns = _fetch_real_columns(engine, args.schema)
    declared = _declared_columns()
    _write_report(Path(args.out), real_columns, declared)
    print(f"Relatorio escrito em {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
