"""Conexão read-only e helpers compartilhados pelo levantamento de texto livre.

A sessão é aberta como read-only no próprio Postgres, então nenhum
UPDATE/DELETE/DDL é possível nem por acidente.

Diferente de `experimentos/geografia/_conexao.py`, aqui alguns scripts leem
valor de célula (texto clínico real) para caracterizar e amostrar. Por isso
toda saída vai para `resultados/`, que está no `.gitignore` inteiro — nada
gerado aqui deve ser commitado.
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
    sys.exit("psycopg2 não encontrado. Rode: pip install psycopg2-binary")

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
RESULTADOS = AQUI / "resultados"


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


TIMEOUT_MS = int(_cfg("STATEMENT_TIMEOUT_MS", "600000"))


def conectar():
    """Abre a conexão em modo read-only e autocommit.

    `client_encoding=utf8` pelo mesmo motivo de `scripts/00_connect_db.py`:
    o banco é SQL_ASCII mas guarda bytes UTF-8.
    """
    conn = psycopg2.connect(
        host=_cfg("DB_HOST", "localhost"),
        port=int(_cfg("DB_PORT", "5432")),
        user=_cfg("DB_USER", "postgres"),
        password=_cfg("DB_PASSWORD", ""),
        dbname=_cfg("DB_NAME", "esus"),
        connect_timeout=15,
        client_encoding="utf8",
    )
    conn.set_session(readonly=True, autocommit=True)
    with conn.cursor() as cur:
        cur.execute("SET statement_timeout = %s", (TIMEOUT_MS,))
    return conn


def consulta(conn, sql: str, params: tuple | dict | None = None):
    """Executa e devolve linhas, ou {'erro': ...} se falhar.

    Só interpola quando há params — sem eles o psycopg2 não tenta interpretar
    `%` de um LIKE como placeholder.
    """
    try:
        with conn.cursor() as cur:
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            return cur.fetchall()
    except Exception as exc:  # noqa: BLE001 - levantamento segue com o que der
        return {"erro": str(exc).strip().splitlines()[0][:300]}


def titulo(texto: str) -> None:
    print("\n" + "=" * 72)
    print(texto)
    print("=" * 72, flush=True)


def ident(nome: str) -> str:
    """Nome de tabela/coluna entre aspas, escapando aspas internas."""
    return '"' + nome.replace('"', '""') + '"'


def familia(tabela: str) -> str:
    """Papel da tabela pelo prefixo: tb (dado vivo), ta (auditoria),
    tl (revisão/histórico), rl (relacionamento), outro."""
    p = tabela.lower().split("_", 1)[0]
    return p if p in {"tb", "ta", "tl", "rl"} else "outro"


def ultimo(nome: str) -> Path:
    """Arquivo mais recente `resultados/<nome>_*.json` — é assim que um script
    consome a saída do anterior."""
    arquivos = sorted(RESULTADOS.glob(f"{nome}_*.json"))
    if not arquivos:
        sys.exit(f"Nenhum resultado de '{nome}' em {RESULTADOS}. Rode esse script antes.")
    return arquivos[-1]


def ler(nome: str) -> dict:
    return json.loads(ultimo(nome).read_text(encoding="utf-8"))


def gravar(nome: str, dados, sufixo: str = "json") -> Path:
    """Grava em resultados/<nome>_<timestamp>.<sufixo>."""
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    caminho = RESULTADOS / f"{nome}_{datetime.now():%Y%m%d_%H%M%S}.{sufixo}"
    if sufixo == "json":
        caminho.write_text(
            json.dumps(dados, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )
    else:
        caminho.write_text(dados, encoding="utf-8")
    print(f"\nResultado gravado em: {caminho}")
    return caminho
