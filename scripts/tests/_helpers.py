"""Utilitários compartilhados pelos testes das migrations."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SCRIPTS_DIR = Path(__file__).resolve().parent.parent

# Garante que módulos como `pipeline_logging` sejam importáveis pelas
# migrations quando os testes as carregam isoladamente.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_migration(filename: str) -> ModuleType:
    """Carrega uma migration `scripts/NN_*.py` (nome não é identificador)."""
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"não foi possível carregar {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module
