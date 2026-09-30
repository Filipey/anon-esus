"""Conexão compartilhada com o banco.

Lê as credenciais do `.env` e expõe um `engine` do SQLAlchemy que é
reutilizado por todas as migrations da pipeline.

O banco de treinamento real reporta `server_encoding = SQL_ASCII` (sem
validação de encoding — Postgres so guarda/devolve os bytes crus), mas os
dados de fato estão em UTF-8 (nomes/endereços com acento). Sem forçar
`client_encoding=utf8`, o psycopg2 tenta decodificar como ASCII puro e
quebra com `UnicodeDecodeError` no primeiro valor acentuado (confirmado
na migration 02, nomes de unidade). Forçar UTF-8 no client faz o
Postgres repassar os bytes sem tentar (re)converter, e o psycopg2
decodifica certo.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import URL, Engine, create_engine

load_dotenv()

_REQUIRED_VARS = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")


def _build_url(database: str | None = None) -> URL:
    """Monta a URL de conexão a partir do ambiente.

    Usa `URL.create` em vez de uma f-string para que senhas com
    caracteres especiais (`@`, `:`, `/`, `'`, ...) sejam corretamente
    escapadas — montar a string manualmente quebra o parsing do host.

    `database` troca só o banco, mantendo host/usuário do `.env` — é como
    a pipeline aponta para cada versão (`scripts/versionamento.py`).
    """
    missing = [var for var in _REQUIRED_VARS if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            f"Variáveis de ambiente ausentes no .env: {', '.join(missing)}"
        )

    return URL.create(
        "postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=database or os.environ["DB_NAME"],
    )


def create_db_engine(database: str | None = None, **kwargs) -> Engine:
    """Cria um novo engine, por padrão no banco `DB_NAME`. Útil para testes,
    conexões isoladas ou para abrir uma versão específica da base."""
    return create_engine(
        _build_url(database), future=True, connect_args={"client_encoding": "utf8"}, **kwargs
    )


# Engine compartilhado, importado pelas migrations.
engine: Engine = create_db_engine()
