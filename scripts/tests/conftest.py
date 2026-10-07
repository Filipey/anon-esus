"""Infra de testes da pipeline.

Fornece a fixture `pg_engine`: um PostgreSQL **efêmero**, criado num
diretório temporário e destruído ao fim de cada teste. É o "banco em
memória" do projeto — descartável e isolado, porém com fidelidade total
ao Postgres real (suporta `information_schema`, `TEMP TABLE`, `UPDATE ...
FROM`, casts `::text`, triggers etc.), o que SQLite/H2 não ofereceriam.
"""

from __future__ import annotations

import os

import pytest
import testing.postgresql
from sqlalchemy import Engine, create_engine

# Segredo fixo de teste (scripts/segredo.py): os testes não podem depender do
# segredo real do .env, e o load_dotenv não sobrescreve variável já definida.
os.environ["ANON_SEGREDO"] = "segredo-de-teste-" + "0" * 32


@pytest.fixture
def pg_engine() -> Engine:
    """Engine apontando para um Postgres efêmero, novo a cada teste."""
    with testing.postgresql.Postgresql() as postgresql:
        engine = create_engine(postgresql.url(), future=True)
        try:
            yield engine
        finally:
            engine.dispose()
