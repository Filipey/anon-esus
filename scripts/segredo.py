"""Segredo da anonimização: sais e sementes fora do código.

As migrations que trocam um valor real por um fictício de forma
determinística (hash com sal, Faker com semente, sorteio com semente)
precisavam de sal e semente fixos para manter o vínculo entre tabelas e
para uma versão refeita sair igual. Com esses valores no código, e o código
no git, a troca era só pseudonimização: quem conhece o valor real de uma
pessoa (o CNS, o INE da equipe, o CNES) recalcula o fictício e acha o
registro dela na base anonimizada.

Agora todo sal e toda semente são derivados, por HMAC-SHA256, de um único
segredo em `ANON_SEGREDO` (no `.env`, que não vai para o git), com um
"propósito" diferente para cada uso. Enquanto o segredo existir, a pipeline
é reprodutível; **depois do prazo de retenção ele deve ser destruído junto
com a base original** — sem ele, o mapeamento real -> fictício não pode
mais ser recalculado por ninguém.

O segredo é lido na hora do uso, não ao importar: `audit_schema.py` e o
relatório de auditoria importam as migrations só para ler as listas de
colunas e não precisam dele.
"""

from __future__ import annotations

import hashlib
import hmac
import os

from dotenv import load_dotenv

VARIAVEL = "ANON_SEGREDO"
TAMANHO_MINIMO = 32


def _mestre() -> bytes:
    load_dotenv()
    valor = os.getenv(VARIAVEL, "")
    if len(valor) < TAMANHO_MINIMO:
        raise RuntimeError(
            f"{VARIAVEL} ausente ou curto demais (mínimo {TAMANHO_MINIMO} caracteres) no .env. "
            "Gere com: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return valor.encode()


def sal(proposito: str) -> str:
    """Sal (64 caracteres hex) próprio de um uso, ex.: sal("cns")."""
    return hmac.new(_mestre(), proposito.encode(), hashlib.sha256).hexdigest()


def semente(proposito: str) -> int:
    """Semente inteira (32 bits) própria de um uso, ex.: semente("cpf")."""
    return int(sal(proposito)[:8], 16)
