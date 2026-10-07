"""Os algoritmos ficam em `scripts/k_anonimato.py`, compartilhados com as
migrations; este módulo só os reexporta para os scripts do experimento."""

import sys

from _conexao import RAIZ

if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

from k_anonimato import *  # noqa: E402,F401,F403
from k_anonimato import NULO, SUPRIMIVEIS, _rotulo  # noqa: E402,F401
