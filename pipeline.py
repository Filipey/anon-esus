"""Orquestrador da pipeline de migrations.

Descobre os scripts numerados em `scripts/` e os executa em ordem.

Metodologia: Testar antes de aplicar:
para cada migration `scripts/NN_*.py`, o orquestrador primeiro roda o
teste correspondente (`scripts/tests/test_NN_*.py`) contra um PostgreSQL
efêmero (em diretório temporário, descartável, ver
`scripts/tests/conftest.py`). A migration só é aplicada ao banco real se
o teste passar. Migration sem teste é tratada como falha.

Convenção:
- `scripts/00_connect_db.py` é o módulo de conexão e expõe a engine de conexão.
- Cada migration `scripts/NN_*.py` (NN >= 01) expõe `run(engine)` e é
  responsável pela própria atomicidade (transação com rollback no erro).
- Cada migration tem um teste `scripts/tests/test_<stem>.py`.

A pipeline para na primeira migration cujo teste falhe ou cuja aplicação
falhe; como cada migration é atômica, o banco permanece consistente.

**PIPELINE_SKIP_TESTS=1**: pula a etapa de teste (Postgres efêmero) e
aplica direto no banco real. Existe só para destravar quando não há
`initdb` disponível na máquina — nenhuma migration terá sido validada
antes de tocar o banco real. Cada migration continua atômica (rollback
individual em caso de erro), mas o comportamento em si não foi
verificado antes. Desligado por padrão; precisa ser setado explicitamente
a cada execução.

Auditoria: antes de aplicar qualquer migration, `scripts/pipeline_report.py`
tira uma "foto" (linhas totais, não-nulos, checksum agregado) de cada
coluna/tabela declarada nas migrations. Depois da execução (com sucesso ou
não), tira a foto de novo e escreve um relatório JSON ao lado do log de
texto (`logs/pipeline_<timestamp>_auditoria.json`), mostrando quais
colunas de fato tiveram conteúdo alterado — sem nunca expor um valor real.
"""

from __future__ import annotations

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


def _run_migrations(migrations: list[Path], engine) -> int:
    log.info("%d migration(s) a aplicar.", len(migrations))
    for path in migrations:
        log.info("--> %s", path.name)

        # 1) Testar antes de aplicar (a menos que SKIP_TESTS esteja ativo).
        if SKIP_TESTS:
            log.warning(
                "[teste] PULADO (PIPELINE_SKIP_TESTS=1) — %s será aplicada SEM "
                "validação prévia contra Postgres efêmero.",
                path.name,
            )
        else:
            test_path = _test_path_for(path)
            if not test_path.exists():
                log.error("migration sem teste: esperado %s. Abortando.", test_path.name)
                return 1
            if not _run_tests(test_path):
                log.error("testes de %s falharam. Migration NÃO aplicada.", path.name)
                log.error("Banco em estado seguro (nada foi alterado).")
                return 1
            log.info("[teste] OK")

        # 2) Aplicar no banco real.
        module = _load_module(path)
        run = getattr(module, "run", None)
        if not callable(run):
            log.error("%s não expõe uma função run(engine).", path.name)
            return 1
        try:
            run(engine)
        except Exception:
            log.exception("[FALHA] %s — migration revertida (rollback).", path.name)
            log.error("Banco em estado seguro.")
            return 1
        log.info("%s aplicada com sucesso.", path.name)

    return 0


def _write_audit_report(engine, log_file: Path, snapshot_before: dict, started_at: datetime) -> None:
    """Tira a foto 'depois' e escreve o relatório de auditoria (JSON) ao
    lado do log de texto. Roda mesmo se a pipeline falhou no meio, para
    documentar o que já tinha sido alterado até ali."""
    try:
        report_module = _load_module(SCRIPTS_DIR / REPORT_MODULE)
    except Exception:
        log.exception("falha ao carregar %s — relatório de auditoria não gerado.", REPORT_MODULE)
        return

    log.info("tirando foto do banco depois da execução (auditoria)...")
    try:
        snapshot_after = report_module.build_snapshot(engine)
        finished_at = datetime.now(timezone.utc)
        report = report_module.build_report(snapshot_before, snapshot_after, started_at, finished_at)
    except Exception:
        log.exception("falha ao montar o relatório de auditoria")
        return

    report_path = log_file.with_name(log_file.stem + "_auditoria.json")
    try:
        report_module.write_report(report, report_path)
    except Exception:
        log.exception("falha ao escrever o relatório de auditoria em %s", report_path)
        return

    report_module.log_summary(report)
    log.info("Relatório de auditoria (quantitativo/qualitativo) em %s", report_path)


def main() -> int:
    log_file = setup_file_logging()
    log.info("=== Pipeline de migrations ===")
    if SKIP_TESTS:
        log.warning(
            "=== PIPELINE_SKIP_TESTS=1: rodando SEM validação prévia (Postgres "
            "efêmero indisponível). Nenhuma migration foi testada antes de "
            "tocar o banco real. ==="
        )

    migrations = _discover_migrations()
    if not migrations:
        log.info("Nenhuma migration encontrada.")
        return 0

    # Conexão com o banco real só é estabelecida depois de descobrir as
    # migrations; cada migration é testada logo antes de ser aplicada.
    try:
        connect = _load_module(SCRIPTS_DIR / CONNECT_MODULE)
        engine = connect.engine
    except Exception:
        log.exception("Falha ao estabelecer a conexão com o banco. Abortando.")
        return 1

    started_at = datetime.now(timezone.utc)
    snapshot_before = None
    try:
        report_module = _load_module(SCRIPTS_DIR / REPORT_MODULE)
        log.info("tirando foto do banco antes de aplicar qualquer migration (auditoria)...")
        snapshot_before = report_module.build_snapshot(engine)
    except Exception:
        log.exception(
            "falha ao tirar a foto 'antes' — relatório de auditoria ficará incompleto, "
            "mas a pipeline continua."
        )

    exit_code = _run_migrations(migrations, engine)

    if snapshot_before is not None:
        _write_audit_report(engine, log_file, snapshot_before, started_at)

    if exit_code == 0:
        log.info("=== Pipeline concluída com sucesso ===")
    log.info("Log completo em %s", log_file)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
