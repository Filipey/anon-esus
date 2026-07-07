"""Logging centralizado da pipeline.

Toda a pipeline escreve num único arquivo de texto (em `logs/`), além do
console. Migrations obtêm o logger com `get_logger(__nome__)`; o
orquestrador chama `setup_file_logging()` uma vez no início para anexar o
arquivo de log.

Hierarquia: todos os loggers ficam sob `"pipeline"`, então um único
`FileHandler` no logger raiz `"pipeline"` captura tudo (orquestrador +
migrations), por propagação.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
ROOT_LOGGER = "pipeline"

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str | None = None) -> logging.Logger:
    """Logger para um componente da pipeline (migration, orquestrador...)."""
    if not name:
        return logging.getLogger(ROOT_LOGGER)
    return logging.getLogger(f"{ROOT_LOGGER}.{name}")


def setup_file_logging(run_name: str = "pipeline") -> Path:
    """Configura arquivo + console. Retorna o caminho do log.

    Idempotente: limpa handlers anteriores antes de reanexar. O arquivo
    recebe tudo (DEBUG+); o console mostra INFO+.
    """
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"{run_name}_{timestamp}.log"

    logger = logging.getLogger(ROOT_LOGGER)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(_FORMAT, _DATEFMT)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Log iniciado em %s", log_file)
    return log_file
