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
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / "scripts"
TESTS_DIR = SCRIPTS_DIR / "tests"
CONNECT_MODULE = "00_connect_db.py"

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


def main() -> int:
    log_file = setup_file_logging()
    log.info("=== Pipeline de migrations ===")

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

    log.info("%d migration(s) a aplicar.", len(migrations))
    for path in migrations:
        log.info("--> %s", path.name)

        # 1) Testar antes de aplicar.
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

    log.info("=== Pipeline concluída com sucesso ===")
    log.info("Log completo em %s", log_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
