"""Versões incrementais da base: um dump por etapa da anonimização.

A pipeline nunca escreve no banco `DB_NAME` (a base original). No servidor
existe um único banco de trabalho (`VERSAO_BANCO_TRABALHO`, padrão
`esus_anon_trabalho`), onde as migrations são aplicadas em sequência. Depois
de cada etapa, a pipeline grava um `pg_dump` da versão na máquina que roda a
pipeline (`VERSOES_DIR`, padrão `versoes/`, fora do git):

    versoes/v00_original.dump        dump da base original
    versoes/v01_cpf.dump             v00 + migration 01
    versoes/v02_unidade_saude.dump   v01 + migration 02
    ...

Assim o servidor só precisa de espaço para um banco além da original, e
qualquer versão pode ser restaurada (`pipeline.py --restaurar NN`) para o PEC
gerar os relatórios do próprio sistema sobre ela.

Procedência: cada dump tem um `.json` ao lado com a versão, a migration, a
**cadeia** (nome e SHA-256 de cada migration aplicada até ali), o commit do
git e o relatório de auditoria. O banco de trabalho guarda o mesmo JSON no
`COMMENT ON DATABASE`, para a pipeline saber em que etapa ele está. Uma
versão só é reaproveitada se a cadeia dela bate com os arquivos atuais.

O banco de trabalho é sempre recriado a partir de um dump (nunca copiando a
original viva, que o PEC continua alterando), então cada versão deriva
exatamente da anterior gravada. Apagar um banco exige que ninguém esteja
conectado a ele; a pipeline aborta e lista as conexões, nunca as derruba.
O `pg_dump` da original não tem essa restrição: o PEC pode seguir ligado.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Engine, text

ROOT = Path(__file__).resolve().parent.parent
BANCO_TRABALHO = os.getenv("VERSAO_BANCO_TRABALHO", "esus_anon_trabalho")
DIR_VERSOES = Path(os.getenv("VERSOES_DIR", ROOT / "versoes"))
NOME_V00 = "v00_original"

# pg_dump mais novo que o servidor emite parâmetros que o servidor não
# conhece; no restore eles dão erro inofensivo. Só estes são tolerados.
ERROS_TOLERADOS = (re.compile(r'unrecognized configuration parameter "transaction_timeout"'),)


class ConexoesAbertas(RuntimeError):
    """Há sessões conectadas no banco que seria copiado ou apagado."""


class ErroDump(RuntimeError):
    """pg_dump/pg_restore falhou."""


def _ident(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


# ------------------------------------------------------------ nomes e hashes
def nome_versao(migration: Path | None) -> str:
    """`None` -> `v00_original`; `scripts/01_anon_cpf.py` -> `v01_cpf`."""
    if migration is None:
        return NOME_V00
    numero, _, resto = migration.stem.partition("_")
    return f"v{numero}_{re.sub(r'^anon_', '', resto)}"


def numero_migration(migration: Path) -> int:
    return int(migration.stem.split("_", 1)[0])


def hash_arquivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cadeia(migrations: list[Path]) -> list[dict]:
    """Identidade de uma versão: as migrations aplicadas até ela, em ordem."""
    return [{"migration": p.name, "sha256": hash_arquivo(p)} for p in migrations]


def estado_git() -> dict:
    def git(*args: str) -> str:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        return r.stdout.strip()

    return {
        "commit": git("rev-parse", "HEAD") or None,
        "branch": git("rev-parse", "--abbrev-ref", "HEAD") or None,
        "sujo": bool(git("status", "--porcelain", "--untracked-files=no")),
    }


def meta_versao(
    numero: int,
    nome: str,
    cadeia_atual: list[dict],
    origem: str,
    auditoria: Path | None = None,
) -> dict:
    return {
        "versao": numero,
        "nome": nome,
        "origem": origem,
        "cadeia": cadeia_atual,
        "git": estado_git(),
        "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "auditoria": str(auditoria.relative_to(ROOT)) if auditoria else None,
    }


# ------------------------------------------------------------ dumps locais
def caminho_dump(nome: str) -> Path:
    return DIR_VERSOES / f"{nome}.dump"


def ler_meta_dump(nome: str) -> dict | None:
    meta = caminho_dump(nome).with_suffix(".json")
    if not (meta.exists() and caminho_dump(nome).exists()):
        return None
    try:
        return json.loads(meta.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def gravar_meta_dump(nome: str, meta: dict) -> None:
    caminho_dump(nome).with_suffix(".json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )


def apagar_dump(nome: str) -> None:
    for p in (caminho_dump(nome), caminho_dump(nome).with_suffix(".json")):
        p.unlink(missing_ok=True)


def listar_dumps() -> list[dict]:
    out = []
    for meta_path in sorted(DIR_VERSOES.glob("v*.json")):
        nome = meta_path.stem
        meta = ler_meta_dump(nome)
        if meta is None:
            continue
        tamanho = caminho_dump(nome).stat().st_size
        out.append({**meta, "arquivo": caminho_dump(nome), "bytes": tamanho})
    return out


def _env_pg() -> dict:
    return {
        **os.environ,
        "PGHOST": os.environ["DB_HOST"],
        "PGPORT": os.environ["DB_PORT"],
        "PGUSER": os.environ["DB_USER"],
        "PGPASSWORD": os.environ["DB_PASSWORD"],
    }


def dump(banco: str, nome: str) -> Path:
    """`pg_dump -Fc` de `banco` para `versoes/<nome>.dump`. Grava num
    temporário e renomeia, para um dump interrompido nunca parecer válido."""
    DIR_VERSOES.mkdir(parents=True, exist_ok=True)
    destino = caminho_dump(nome)
    tmp = destino.with_suffix(".dump.parcial")
    r = subprocess.run(
        ["pg_dump", "-Fc", "-d", banco, "-f", str(tmp)],
        env=_env_pg(), capture_output=True, text=True,
    )
    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise ErroDump(f"pg_dump de '{banco}' falhou:\n{r.stderr.strip()}")
    tmp.replace(destino)
    return destino


# ------------------------------------------------------------ servidor
def admin_engine(create_db_engine) -> Engine:
    """Engine no banco de manutenção `postgres`, em autocommit — CREATE/DROP
    DATABASE não rodam dentro de transação, e conectar em `postgres` evita
    ocupar a origem de uma cópia."""
    return create_db_engine("postgres", isolation_level="AUTOCOMMIT")


def existe(admin: Engine, nome: str) -> bool:
    with admin.connect() as c:
        return c.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": nome}).first() is not None


def conexoes_abertas(admin: Engine, nome: str) -> list[dict]:
    with admin.connect() as c:
        rows = c.execute(
            text(
                """
                SELECT pid, usename, application_name, client_addr::text, state, backend_start
                FROM pg_stat_activity
                WHERE datname = :n AND pid <> pg_backend_pid()
                ORDER BY backend_start
                """
            ),
            {"n": nome},
        ).mappings().all()
    return [dict(r) for r in rows]


def exigir_livre(admin: Engine, nome: str) -> None:
    """Levanta `ConexoesAbertas` se houver alguém conectado em `nome`."""
    sessoes = conexoes_abertas(admin, nome)
    if sessoes:
        linhas = "\n".join(
            f"  pid={s['pid']} usuário={s['usename']} app={s['application_name'] or '-'} "
            f"cliente={s['client_addr'] or 'local'} estado={s['state']} desde={s['backend_start']}"
            for s in sessoes
        )
        raise ConexoesAbertas(
            f"'{nome}' tem {len(sessoes)} conexão(ões) aberta(s); o Postgres só copia ou apaga "
            f"um banco sem ninguém conectado. Feche-as (PEC, DBeaver...) e rode de novo:\n{linhas}"
        )


def _protegido(nome: str) -> bool:
    return nome in {os.getenv("DB_NAME"), "postgres", "template0", "template1"}


def remover(admin: Engine, nome: str) -> None:
    """Apaga um banco de trabalho/restauração. Recusa a original e os bancos
    do sistema."""
    if _protegido(nome):
        raise ValueError(f"'{nome}' é protegido; recusando apagar.")
    exigir_livre(admin, nome)
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {_ident(nome)}"))


def restaurar(admin: Engine, nome_dump: str, destino: str, jobs: int = 4) -> None:
    """Recria `destino` a partir de `versoes/<nome_dump>.dump`, com a mesma
    codificação e locale da original (a base é SQL_ASCII)."""
    if _protegido(destino):
        raise ValueError(f"'{destino}' é protegido; recusando sobrescrever.")
    arquivo = caminho_dump(nome_dump)
    if not arquivo.exists():
        raise ErroDump(f"dump inexistente: {arquivo}")
    if existe(admin, destino):
        remover(admin, destino)
    with admin.connect() as c:
        enc, coll, ctype = c.execute(
            text(
                "SELECT pg_encoding_to_char(encoding), datcollate, datctype "
                "FROM pg_database WHERE datname = :n"
            ),
            {"n": os.environ["DB_NAME"]},
        ).one()
        c.execute(
            text(
                f"CREATE DATABASE {_ident(destino)} TEMPLATE template0 "
                f"ENCODING '{enc}' LC_COLLATE '{coll}' LC_CTYPE '{ctype}'"
            )
        )
    r = subprocess.run(
        ["pg_restore", "-d", destino, "-j", str(jobs), str(arquivo)],
        env=_env_pg(), capture_output=True, text=True,
    )
    if r.returncode != 0:
        erros = [
            linha for linha in r.stderr.splitlines()
            if linha.startswith("pg_restore: error:") and not any(p.search(linha) for p in ERROS_TOLERADOS)
        ]
        if erros:
            raise ErroDump(f"pg_restore em '{destino}' falhou:\n" + "\n".join(erros[:20]))


def gravar_meta_banco(admin: Engine, nome: str, meta: dict) -> None:
    literal = json.dumps(meta, ensure_ascii=False, default=str).replace("'", "''")
    with admin.connect() as c:
        c.execute(text(f"COMMENT ON DATABASE {_ident(nome)} IS '{literal}'"))


def ler_meta_banco(admin: Engine, nome: str) -> dict | None:
    with admin.connect() as c:
        r = c.execute(
            text("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname = :n"),
            {"n": nome},
        ).scalar()
    if not r:
        return None
    try:
        return json.loads(r)
    except json.JSONDecodeError:
        return None
