"""Orquestrador da pipeline de migrations.

Descobre os scripts numerados em `scripts/` e os executa em ordem.

Versões incrementais: a pipeline **nunca escreve no banco `DB_NAME`** (a
base original). As migrations rodam em sequência num único banco de
trabalho no servidor, e depois de cada uma a pipeline grava um dump da
versão na máquina local (`versoes/vNN_<nome>.dump` + `.json` de
procedência). Qualquer versão pode ser restaurada para o PEC gerar
relatórios sobre ela. Ver `scripts/versionamento.py`.

Uma versão é reaproveitada se a cadeia de migrations que a gerou (nome e
SHA-256 de cada arquivo) bate com a atual. Numa nova execução a pipeline
retoma da última versão válida: se a migration NN mudou, as versões NN em
diante são refeitas. `--a-partir-de NN` força refazer de NN em diante.

Metodologia: Testar antes de aplicar:
para cada migration `scripts/NN_*.py`, o orquestrador primeiro roda o
teste correspondente (`scripts/tests/test_NN_*.py`) contra um PostgreSQL
efêmero (em diretório temporário, descartável, ver
`scripts/tests/conftest.py`). A migration só é aplicada se o teste passar.
Migration sem teste é tratada como falha.

Convenção:
- `scripts/00_connect_db.py` é o módulo de conexão.
- Cada migration `scripts/NN_*.py` (NN >= 01) expõe `run(engine)` e é
  responsável pela própria atomicidade (transação com rollback no erro).
- Cada migration tem um teste `scripts/tests/test_<stem>.py`.

A pipeline para na primeira migration cujo teste ou aplicação falhe. Como
a migration é atômica, o banco de trabalho continua na versão anterior, e a
próxima execução retoma dali.

**PIPELINE_SKIP_TESTS=1**: pula a etapa de teste (Postgres efêmero).
Existe só para destravar quando não há `initdb` disponível na máquina.
Desligado por padrão; precisa ser setado explicitamente a cada execução.

Auditoria: para cada versão, `scripts/pipeline_report.py` tira uma "foto"
(linhas totais, não-nulos, checksum agregado) das colunas/tabelas
declaradas nas migrations antes e depois da migration, e grava
`logs/pipeline_<timestamp>_vNN_auditoria.json` — sem nunca expor um valor
real. O caminho do relatório fica registrado na procedência da versão.

Uso:
    python pipeline.py                     # cria/retoma a cadeia de versões
    python pipeline.py --a-partir-de 6     # refaz da versão 06 em diante
    python pipeline.py --listar            # versões gravadas e estado do banco de trabalho
    python pipeline.py --restaurar 5       # restaura a v05 no banco de trabalho (para o PEC)
    python pipeline.py --restaurar 5 --banco esus_v05   # ... ou num banco à parte
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / "scripts"
TESTS_DIR = SCRIPTS_DIR / "tests"
CONNECT_MODULE = "00_connect_db.py"
REPORT_MODULE = "pipeline_report.py"
SKIP_TESTS = os.getenv("PIPELINE_SKIP_TESTS") == "1"

# `scripts/` no path para que pipeline_logging (e as migrations) importem.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import versionamento as v  # noqa: E402
from pipeline_logging import get_logger, setup_file_logging  # noqa: E402

log = get_logger()


def _load_module(path: Path) -> ModuleType:
    """Importa um arquivo .py cujo nome não é um identificador válido."""
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"não foi possível carregar {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _discover_migrations() -> list[Path]:
    return sorted(
        p
        for p in SCRIPTS_DIR.glob("[0-9][0-9]_*.py")
        if p.name != CONNECT_MODULE
    )


def _test_path_for(migration: Path) -> Path:
    return TESTS_DIR / f"test_{migration.stem}.py"


def _run_tests(test_path: Path) -> bool:
    """Roda o teste da migration (Postgres efêmero) via pytest.

    A saída completa do pytest é registrada no log. Retorna True somente
    se todos os testes passarem.
    """
    log.info("[teste] %s (Postgres efêmero)...", test_path.relative_to(ROOT))
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(test_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    saida = (result.stdout or "") + (result.stderr or "")
    log.info("saída do pytest:\n%s", saida.strip())
    return result.returncode == 0


def _audit(report_module, engine, before: dict, started_at: datetime, path: Path) -> dict | None:
    """Tira a foto 'depois' e grava o relatório de auditoria da versão.
    Devolve a foto 'depois', que serve de 'antes' da próxima versão."""
    try:
        after = report_module.build_snapshot(engine)
        report = report_module.build_report(before, after, started_at, datetime.now(timezone.utc))
        report_module.write_report(report, path)
        report_module.log_summary(report)
        log.info("relatório de auditoria em %s", path.relative_to(ROOT))
        return after
    except Exception:
        log.exception("falha ao gerar o relatório de auditoria em %s", path)
        return None


def _versao_valida(nome: str, cadeia_esperada: list[dict]) -> bool:
    meta = v.ler_meta_dump(nome)
    return meta is not None and meta.get("cadeia") == cadeia_esperada


def _ultima_valida(migrations: list[Path], a_partir_de: int | None) -> int:
    """Índice k da última versão reaproveitável (0 = só a v00), ou -1 se nem
    a v00 existe. Versões depois de k estão ausentes ou desatualizadas."""
    if not _versao_valida(v.NOME_V00, []):
        return -1
    k = 0
    for i, path in enumerate(migrations, start=1):
        if a_partir_de is not None and v.numero_migration(path) >= a_partir_de:
            break
        if not _versao_valida(v.nome_versao(path), v.cadeia(migrations[:i])):
            break
        k = i
    return k


def _preparar_banco_trabalho(admin, migrations: list[Path], k: int) -> None:
    """Deixa o banco de trabalho exatamente na versão k."""
    trabalho = v.BANCO_TRABALHO
    nome = v.NOME_V00 if k == 0 else v.nome_versao(migrations[k - 1])
    esperado = v.cadeia(migrations[:k])
    meta = v.ler_meta_banco(admin, trabalho) if v.existe(admin, trabalho) else None
    if meta and meta.get("versao") == k and meta.get("cadeia") == esperado:
        log.info("banco de trabalho %s já está na %s — reaproveitado.", trabalho, nome)
        return

    # Sempre a partir do dump, nunca copiando a original viva: o PEC continua
    # escrevendo nela, e a versão seguinte tem que derivar exatamente da
    # versão k gravada.
    log.info("restaurando %s no banco de trabalho %s a partir do dump local...", nome, trabalho)
    v.restaurar(admin, nome, trabalho)
    v.gravar_meta_banco(admin, trabalho, v.ler_meta_dump(nome))


def _run_pipeline(migrations: list[Path], connect, admin, log_file: Path, a_partir_de: int | None) -> int:
    original = os.environ["DB_NAME"]

    k = _ultima_valida(migrations, a_partir_de)
    obsoletas = [v.nome_versao(p) for p in migrations[max(k, 0):]]
    for nome in obsoletas:
        if v.caminho_dump(nome).exists():
            log.info("versão %s desatualizada — será refeita.", nome)
            v.apagar_dump(nome)

    if k < 0:
        log.info("v00: gravando dump da base original '%s' (o PEC pode continuar conectado)...", original)
        v.dump(original, v.NOME_V00)
        v.gravar_meta_dump(v.NOME_V00, v.meta_versao(0, v.NOME_V00, [], original))
        k = 0
    log.info("retomando da versão %02d; %d migration(s) a aplicar.", k, len(migrations) - k)
    if k == len(migrations):
        log.info("todas as versões estão atualizadas.")
        return 0

    _preparar_banco_trabalho(admin, migrations, k)

    report_module = _load_module(SCRIPTS_DIR / REPORT_MODULE)
    engine = connect.create_db_engine(v.BANCO_TRABALHO)
    foto_anterior: dict | None = None
    anterior = v.NOME_V00 if k == 0 else v.nome_versao(migrations[k - 1])
    try:
        for i, path in enumerate(migrations[k:], start=k + 1):
            numero = v.numero_migration(path)
            nome = v.nome_versao(path)
            log.info("--> %s  (%s -> %s)", path.name, anterior, nome)

            # 1) Testar antes de aplicar (a menos que SKIP_TESTS esteja ativo).
            if SKIP_TESTS:
                log.warning("[teste] PULADO (PIPELINE_SKIP_TESTS=1) — %s sem validação prévia.", path.name)
            else:
                test_path = _test_path_for(path)
                if not test_path.exists():
                    log.error("migration sem teste: esperado %s. Abortando.", test_path.name)
                    return 1
                if not _run_tests(test_path):
                    log.error("testes de %s falharam. Versão %s NÃO criada.", path.name, nome)
                    return 1
                log.info("[teste] OK")

            module = _load_module(path)
            run = getattr(module, "run", None)
            if not callable(run):
                log.error("%s não expõe uma função run(engine).", path.name)
                return 1

            # 2) Aplicar no banco de trabalho.
            started_at = datetime.now(timezone.utc)
            try:
                if foto_anterior is None:
                    log.info("tirando foto de auditoria antes da migration...")
                    foto_anterior = report_module.build_snapshot(engine)
                run(engine)
            except Exception:
                log.exception("[FALHA] %s — migration revertida; banco de trabalho segue na %s.",
                              path.name, anterior)
                return 1

            # UPDATE em massa deixa tupla morta; o VACUUM libera o espaço para
            # reuso antes da próxima etapa (o disco do servidor é justo).
            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
                c.exec_driver_sql("VACUUM")

            relatorio = log_file.with_name(f"{log_file.stem}_v{numero:02d}_auditoria.json")
            foto_anterior = _audit(report_module, engine, foto_anterior, started_at, relatorio)

            # 3) Gravar a versão: dump local + procedência, e marcar o banco.
            meta = v.meta_versao(numero, nome, v.cadeia(migrations[:i]), anterior, relatorio)
            log.info("gravando dump %s...", v.caminho_dump(nome))
            v.dump(v.BANCO_TRABALHO, nome)
            v.gravar_meta_dump(nome, meta)
            v.gravar_meta_banco(admin, v.BANCO_TRABALHO, meta)
            log.info("%s gravada.", nome)
            anterior = nome
    finally:
        engine.dispose()

    log.info("Versão final da cadeia: %s (banco de trabalho %s)", anterior, v.BANCO_TRABALHO)
    return 0


def _listar(admin) -> int:
    dumps = v.listar_dumps()
    if not dumps:
        print(f"Nenhuma versão em {v.DIR_VERSOES}.")
    for item in dumps:
        git = item.get("git") or {}
        print(
            f"{item['nome']:32} {item['bytes'] / 2**30:6.2f} GB  origem={item.get('origem')}  "
            f"commit={(git.get('commit') or '?')[:8]}{'*' if git.get('sujo') else ''}  "
            f"criado={item.get('criado_em')}"
        )
    if v.existe(admin, v.BANCO_TRABALHO):
        meta = v.ler_meta_banco(admin, v.BANCO_TRABALHO) or {}
        print(f"\nbanco de trabalho {v.BANCO_TRABALHO}: {meta.get('nome', 'versão desconhecida')}")
    else:
        print(f"\nbanco de trabalho {v.BANCO_TRABALHO}: não existe")
    return 0


def _restaurar(admin, numero: int, banco: str) -> int:
    alvo = next((d for d in v.listar_dumps() if d.get("versao") == numero), None)
    if alvo is None:
        log.error("não há dump da versão %02d em %s.", numero, v.DIR_VERSOES)
        return 1
    log.info("restaurando %s em %s...", alvo["nome"], banco)
    v.restaurar(admin, alvo["nome"], banco)
    v.gravar_meta_banco(admin, banco, {k: val for k, val in alvo.items() if k not in {"arquivo", "bytes"}})
    log.info("%s restaurada em %s.", alvo["nome"], banco)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Pipeline de anonimização com versões incrementais.")
    ap.add_argument("--a-partir-de", type=int, metavar="NN",
                    help="refaz a versão NN e todas as seguintes")
    ap.add_argument("--listar", action="store_true", help="lista as versões gravadas e sai")
    ap.add_argument("--restaurar", type=int, metavar="NN",
                    help="restaura a versão NN num banco do servidor e sai")
    ap.add_argument("--banco", default=None,
                    help=f"banco de destino do --restaurar (padrão: {v.BANCO_TRABALHO})")
    args = ap.parse_args()

    try:
        connect = _load_module(SCRIPTS_DIR / CONNECT_MODULE)
        admin = v.admin_engine(connect.create_db_engine)
    except Exception:
        log.exception("Falha ao preparar a conexão com o servidor. Abortando.")
        return 1

    if args.listar:
        return _listar(admin)

    log_file = setup_file_logging()
    try:
        if args.restaurar is not None:
            return _restaurar(admin, args.restaurar, args.banco or v.BANCO_TRABALHO)

        log.info("=== Pipeline de migrations (versões incrementais) ===")
        if SKIP_TESTS:
            log.warning("=== PIPELINE_SKIP_TESTS=1: rodando SEM validação prévia. ===")
        migrations = _discover_migrations()
        if not migrations:
            log.info("Nenhuma migration encontrada.")
            return 0
        exit_code = _run_pipeline(migrations, connect, admin, log_file, args.a_partir_de)
    except (v.ConexoesAbertas, v.ErroDump) as exc:
        log.error("%s", exc)
        exit_code = 1

    if exit_code == 0:
        log.info("=== Pipeline concluída com sucesso ===")
    log.info("Log completo em %s", log_file)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
