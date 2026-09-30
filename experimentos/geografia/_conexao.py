"""Conexao read-only e helpers compartilhados pelos experimentos de geografia.

A sessao e aberta como read-only no proprio Postgres, entao nenhum
UPDATE/DELETE/DDL e possivel nem por acidente. Todo helper daqui devolve
agregado - contagem, quantil, nome de coluna - nunca valor de celula.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import psycopg2
except ImportError:  # pragma: no cover - depende do ambiente
    sys.exit("psycopg2 nao encontrado. Rode: pip install psycopg2-binary")

RAIZ = Path(__file__).resolve().parents[2]
RESULTADOS = Path(__file__).resolve().parent / "resultados"


def _load_env(path: Path) -> dict[str, str]:
    cfg: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


_ENV = _load_env(Path(os.environ.get("ENV_FILE", RAIZ / ".env")))


def _cfg(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key) or _ENV.get(key) or default


TIMEOUT_MS = int(_cfg("STATEMENT_TIMEOUT_MS", "300000"))


def conectar():
    """Abre a conexao em modo read-only e autocommit."""
    conn = psycopg2.connect(
        host=_cfg("DB_HOST", "localhost"),
        port=int(_cfg("DB_PORT", "5432")),
        user=_cfg("DB_USER", "postgres"),
        password=_cfg("DB_PASSWORD", ""),
        dbname=_cfg("DB_NAME", "esus"),
        connect_timeout=15,
    )
    conn.set_session(readonly=True, autocommit=True)
    return conn


def consulta(conn, sql: str, params: tuple | None = None):
    """Executa e devolve linhas, ou {'erro': ...} se falhar.

    So interpola quando ha params - passar tupla vazia faz o psycopg2 tentar
    interpretar `%` de um LIKE como placeholder.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = %s", (TIMEOUT_MS,))
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            return cur.fetchall()
    except Exception as exc:  # noqa: BLE001 - experimento segue com o que der
        return {"erro": str(exc).strip().splitlines()[0][:300]}


def uma(conn, sql: str, params: tuple | None = None):
    r = consulta(conn, sql, params)
    if isinstance(r, dict):
        return r
    return r[0] if r else None


def colunas_de(conn, tabela: str) -> set[str]:
    r = consulta(
        conn,
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (tabela,),
    )
    return set() if isinstance(r, dict) else {c[0] for c in r}


def existe_tabela(conn, tabela: str) -> bool:
    r = uma(
        conn,
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (tabela,),
    )
    return bool(r) and not isinstance(r, dict)


def titulo(texto: str) -> None:
    print("\n" + "=" * 72)
    print(texto)
    print("=" * 72, flush=True)


def gravar(nome: str, dados: dict) -> Path:
    """Grava o resultado em resultados/<nome>_<timestamp>.json."""
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    caminho = RESULTADOS / f"{nome}_{datetime.now():%Y%m%d_%H%M%S}.json"
    caminho.write_text(
        json.dumps(dados, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    print(f"\nResultado gravado em: {caminho}")
    print("Contem apenas contagens, quantis e nomes de coluna.")
    return caminho
