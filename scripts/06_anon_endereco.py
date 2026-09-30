"""Migration 06 - Endereço: supressão + tercil de distância derivado.

Substitui a versão anterior, que trocava o endereço por outro do mesmo
município. Medida contra o banco real, a troca falhava nos dois sentidos:
era inerte ou reversível onde havia poucos endereços candidatos, e
destruía a associação pessoa↔lugar onde havia muitos (ver
`docs/relatorio_migrations.md`, achado A2 e "Decisão de desenho").

O desenho aprovado, com os parâmetros fechados em `experimentos/geografia/`:

1. **Suprimir** (NULL) o endereço fino de cidadão, profissional e
   domicílio: logradouro, número, complemento, ponto de referência, CEP,
   **bairro** e as coordenadas do domicílio. O bairro sai porque o eixo
   geográfico publicado é o da equipe, e publicar bairro junto cruzaria
   duas partições (a interseção é mais fina que qualquer uma).
2. **Generalizar** para a equipe (INE), que já está na base e é tratada pela
   13 (código fictício). Micro-área é suprimida pela 14.
3. **Derivar**, antes de suprimir a coordenada, o **tercil de distância**
   do domicílio até a sua unidade de saúde, com os cortes calculados dentro
   de cada equipe (`experimentos/geografia/06_agrupamentos.py`). Classes
   (equipe, tercil) com menos de `K_MIN` domicílios não recebem tercil.
4. **Não tocar** o endereço das unidades de saúde, DSEI e polo base:
   entidades institucionais, de endereço público.

Onde o tercil fica: o schema do e-SUS não tem coluna para ele, então ele é
gravado em `tb_cds_domicilio.ds_ponto_referencia` (suprimida no passo 1),
no formato de `TERCIL_TEMPLATE`. Só a tabela mestra do domicílio recebe o
tercil; nas cópias (`ta_`/`tl_`) e no DW o ponto de referência fica nulo.

A unidade do domicílio é `tb_cds_domicilio.nu_cnes`, e as coordenadas das
unidades vêm de `experimentos/geografia/unidades_coordenadas.csv` (endereço
institucional público, geocodificado à mão). Como a 02 roda antes e troca o
CNES por um fictício, o CSV é casado tanto pelo CNES real quanto pelo
fictício que a 02 gera para ele.

Atômica: tudo numa transação.
"""

from __future__ import annotations

import csv
import importlib.util
import math
import sys
from dataclasses import dataclass
from pathlib import Path

from pipeline_logging import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

log = get_logger("06_anon_endereco")

ROOT = Path(__file__).resolve().parent.parent
CSV_UNIDADES = ROOT / "experimentos" / "geografia" / "unidades_coordenadas.csv"

K_MIN = 20
N_TERCIS = 3
TERCIL_TEMPLATE = "faixa de distancia ate a unidade: tercil {n} de {total} da equipe"

# Mesmo filtro de sanidade do experimento: descarta coordenada fora do Brasil.
LAT_MIN, LAT_MAX = -34.0, 6.0
LNG_MIN, LNG_MAX = -74.0, -28.0

DOMICILIO_SCHEMA = "public"
DOMICILIO_TABLE = "tb_cds_domicilio"
DOMICILIO_PK = "co_seq_cds_domicilio"
DOMICILIO_DESTINO = "ds_ponto_referencia"


@dataclass(frozen=True)
class AddressTable:
    schema: str
    table: str
    address_columns: tuple[str, ...]

    @property
    def qualified(self) -> str:
        return f'"{self.schema}"."{self.table}"'


_PESSOA = (
    "ds_cep",
    "ds_complemento",
    "ds_logradouro",
    "ds_ponto_referencia",
    "no_bairro",
    "no_bairro_filtro",
    "nu_numero",
    "st_sem_numero",
)

# Endereço suprimido (cidadão, profissional, domicílio). `audit_schema.py`
# lê esta lista para saber o que a 06 cobre.
ADDRESS_TABLES: list[AddressTable] = [
    AddressTable(
        "public",
        "ta_cds_domicilio",
        (
            "ds_cep",
            "ds_complemento",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
            "no_logradouro",
            "no_logradouro_filtro",
            "nu_domicilio",
            "st_sem_numero",
            "nu_latitude",
            "nu_longitude",
        ),
    ),
    AddressTable("public", "ta_cidadao", _PESSOA),
    AddressTable("public", "ta_prof", _PESSOA),
    AddressTable(
        "public",
        "tb_cds_cad_domiciliar",
        (
            "ds_complemento",
            "ds_complemento_filtro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_logradouro",
            "no_logradouro_filtro",
            "nu_cep",
            "nu_domicilio",
            "st_sem_numero",
            "nu_latitude",
            "nu_longitude",
        ),
    ),
    AddressTable(
        "public",
        "tb_cds_domicilio",
        (
            "ds_cep",
            "ds_complemento",
            "ds_ponto_referencia",
            "no_bairro",
            "no_bairro_filtro",
            "no_logradouro",
            "no_logradouro_filtro",
            "nu_domicilio",
            "st_sem_numero",
            "nu_latitude",
            "nu_longitude",
        ),
    ),
    AddressTable("public", "tb_cidadao", _PESSOA),
    AddressTable(
        "public",
        "tb_fat_cad_domiciliar",
        (
            "no_bairro",
            "no_complemento",
            "no_logradouro",
            "no_ponto_referencia",
            "nu_cep",
            "nu_num_logradouro",
            "nu_latitude",
            "nu_longitude",
        ),
    ),
    AddressTable(
        "public",
        "tb_fat_avaliacao_elegibilidade",
        (
            "no_bairro_residencia",
            "no_complemento_residencia",
            "no_logradouro_residencia",
            "nu_cep_residencia",
            "nu_num_logradouro_residencia",
        ),
    ),
    AddressTable("public", "tb_prof", _PESSOA),
    AddressTable(
        "public",
        "tl_cds_cad_domiciliar",
        (
            "ds_complemento",
            "ds_complemento_filtro",
            "ds_ponto_referencia",
            "no_bairro",
            "no_logradouro",
            "no_logradouro_filtro",
            "nu_cep",
            "nu_domicilio",
            "st_sem_numero",
            "nu_latitude",
            "nu_longitude",
        ),
    ),
    AddressTable(
        "public",
        "tl_cds_domicilio",
        (
            "ds_cep",
            "ds_complemento",
            "ds_ponto_referencia",
            "no_bairro",
            "no_logradouro",
            "nu_domicilio",
            "st_sem_numero",
            "nu_latitude",
            "nu_longitude",
        ),
    ),
    AddressTable("public", "tl_cidadao", _PESSOA),
    AddressTable("public", "tl_prof", _PESSOA),
]

# Endereço institucional, preservado de propósito (passo 4 do desenho).
PRESERVED_TABLES: tuple[str, ...] = (
    "tb_unidade_saude",
    "ta_unidade_saude",
    "tl_unidade_saude",
    "tb_dsei",
    "tb_polo_base",
)


# --------------------------------------------------------------- tercil
def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def tercis_por_grupo(chaves: list, distancias: list[float], n: int = N_TERCIS) -> list[int]:
    """Faixa (0..n-1) por quantil dentro de cada grupo — mesma regra de
    `experimentos/geografia/06_agrupamentos.py`, para a base anonimizada
    reproduzir o que foi medido."""
    por_grupo: dict[object, list[float]] = {}
    for ch, d in zip(chaves, distancias):
        por_grupo.setdefault(ch, []).append(d)
    cortes = {}
    for ch, ds in por_grupo.items():
        ds = sorted(ds)
        cortes[ch] = [ds[max(0, int(len(ds) * i / n) - 1)] for i in range(1, n)]
    saida = []
    for ch, d in zip(chaves, distancias):
        faixa = n - 1
        for i, c in enumerate(cortes[ch]):
            if d < c:
                faixa = i
                break
        saida.append(faixa)
    return saida


def _fake_cnes():
    """`_fake_cnes` da migration 02, para casar o CSV (CNES real) com a base
    depois da 02 ter trocado o CNES."""
    path = Path(__file__).resolve().parent / "02_anon_unidade_saude.py"
    spec = importlib.util.spec_from_file_location("_m02_para_06", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_m02_para_06"] = module
    spec.loader.exec_module(module)
    return module._fake_cnes


def carregar_unidades(path: Path | None = None) -> dict[str, tuple[float, float]]:
    """CNES -> (lat, lng), indexado pelo CNES real e pelo fictício da 02."""
    path = path or CSV_UNIDADES
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        linhas = [linha for linha in fh if not linha.lstrip().startswith("#")]
    fake = _fake_cnes()
    unidades: dict[str, tuple[float, float]] = {}
    for row in csv.DictReader(linhas):
        lat, lng = (row.get("latitude") or "").strip(), (row.get("longitude") or "").strip()
        cnes = (row.get("nu_cnes") or row.get("co_unidade") or "").strip()
        if not (cnes and lat and lng):
            continue
        try:
            coord = (float(lat), float(lng))
        except ValueError:
            continue
        unidades[cnes] = coord
        unidades[fake(cnes)] = coord
    return unidades


def calcular_tercis(linhas, unidades: dict[str, tuple[float, float]], k_min: int | None = None) -> dict:
    """linhas: (pk, lat, lng, ine, cnes). Devolve {pk: tercil 1..N} só para
    domicílios com coordenada válida, equipe e unidade geocodificada, cuja
    classe (equipe, tercil) tenha pelo menos `k_min` (padrão `K_MIN`)
    domicílios."""
    k_min = K_MIN if k_min is None else k_min
    usados = []
    for pk, lat, lng, ine, cnes in linhas:
        if lat is None or lng is None or not ine:
            continue
        if not (LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX):
            continue
        unidade = unidades.get(str(cnes).strip()) if cnes is not None else None
        if unidade is None:
            continue
        usados.append((pk, str(ine).strip(), haversine_m(lat, lng, *unidade)))
    if not usados:
        return {}

    equipes = [u[1] for u in usados]
    faixas = tercis_por_grupo(equipes, [u[2] for u in usados])
    tamanho: dict[tuple[str, int], int] = {}
    for eq, fx in zip(equipes, faixas):
        tamanho[(eq, fx)] = tamanho.get((eq, fx), 0) + 1
    return {
        pk: fx + 1
        for (pk, eq, _), fx in zip(usados, faixas)
        if tamanho[(eq, fx)] >= k_min
    }


# --------------------------------------------------------------- banco
def _existing_columns(conn: Connection, schema: str, table: str) -> set[str]:
    rows = conn.execute(
        text(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table
            """
        ),
        {"schema": schema, "table": table},
    )
    return {r.column_name for r in rows}


def _ler_domicilios(conn: Connection) -> list[tuple]:
    colunas = _existing_columns(conn, DOMICILIO_SCHEMA, DOMICILIO_TABLE)
    precisa = {DOMICILIO_PK, "nu_latitude", "nu_longitude", "nu_ine", "nu_cnes", DOMICILIO_DESTINO}
    if not precisa <= colunas:
        log.warning(
            "%s sem as colunas %s — tercil de distância não será derivado.",
            DOMICILIO_TABLE, sorted(precisa - colunas),
        )
        return []
    return conn.execute(
        text(
            f'SELECT "{DOMICILIO_PK}", nu_latitude::double precision, '
            f"nu_longitude::double precision, nu_ine::text, nu_cnes::text "
            f'FROM "{DOMICILIO_SCHEMA}"."{DOMICILIO_TABLE}"'
        )
    ).all()


def _suprimir(conn: Connection, target: AddressTable) -> int:
    existentes = _existing_columns(conn, target.schema, target.table)
    if not existentes:
        log.warning("tabela inexistente, pulando: %s", target.qualified)
        return 0
    colunas = [c for c in target.address_columns if c in existentes]
    for c in target.address_columns:
        if c not in existentes:
            log.warning("coluna inexistente, pulando: %s.\"%s\"", target.qualified, c)
    if not colunas:
        return 0
    sets = ", ".join(f'"{c}" = NULL' for c in colunas)
    algum = " OR ".join(f'"{c}" IS NOT NULL' for c in colunas)
    n = conn.execute(text(f"UPDATE {target.qualified} SET {sets} WHERE {algum}")).rowcount
    log.info("%s: %d linha(s) com endereço suprimido (%d coluna(s))", target.qualified, n, len(colunas))
    return n


def _gravar_tercis(conn: Connection, tercis: dict) -> int:
    if not tercis:
        return 0
    conn.execute(
        text("CREATE TEMP TABLE _tercil (pk bigint PRIMARY KEY, valor text NOT NULL) ON COMMIT DROP")
    )
    conn.execute(
        text("INSERT INTO _tercil (pk, valor) VALUES (:pk, :valor)"),
        [{"pk": pk, "valor": TERCIL_TEMPLATE.format(n=t, total=N_TERCIS)} for pk, t in tercis.items()],
    )
    return conn.execute(
        text(
            f'UPDATE "{DOMICILIO_SCHEMA}"."{DOMICILIO_TABLE}" AS d '
            f'SET "{DOMICILIO_DESTINO}" = t.valor FROM _tercil t '
            f'WHERE d."{DOMICILIO_PK}" = t.pk'
        )
    ).rowcount


def run(engine: Engine) -> None:
    """Executa a migration de forma atômica."""
    preservadas = set(PRESERVED_TABLES) & {t.table for t in ADDRESS_TABLES}
    if preservadas:
        raise RuntimeError(
            f"ADDRESS_TABLES inclui tabela(s) institucional(is) que devem ser preservadas: "
            f"{sorted(preservadas)}"
        )

    log.info("iniciando supressão de endereços e derivação do tercil de distância...")
    with engine.begin() as conn:
        # 1) Derivar antes de suprimir: a coordenada some no passo 2.
        domicilios = _ler_domicilios(conn)
        unidades = carregar_unidades()
        if domicilios and not unidades:
            log.warning(
                "%s ausente ou sem coordenadas — nenhum domicílio receberá tercil.", CSV_UNIDADES
            )
        tercis = calcular_tercis(domicilios, unidades)
        if domicilios:
            log.info(
                "tercil derivado para %d de %d domicílio(s) (k mínimo por classe = %d)",
                len(tercis), len(domicilios), K_MIN,
            )

        # 2) Suprimir o endereço fino.
        total = sum(_suprimir(conn, t) for t in ADDRESS_TABLES)

        # 3) Gravar o tercil na coluna já suprimida da tabela mestra.
        gravados = _gravar_tercis(conn, tercis)

    log.info(
        "concluído: %d linha(s) com endereço suprimido, %d domicílio(s) com tercil gravado em %s.%s",
        total, gravados, DOMICILIO_TABLE, DOMICILIO_DESTINO,
    )
