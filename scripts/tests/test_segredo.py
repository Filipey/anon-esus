"""Testes do segredo da anonimização (scripts/segredo.py)."""

from __future__ import annotations

import pytest
from _helpers import load_migration

import segredo


def test_propositos_diferentes_dao_sais_diferentes():
    assert segredo.sal("cns") != segredo.sal("ine")
    assert segredo.sal("cns") == segredo.sal("cns")
    assert len(segredo.sal("cns")) == 64
    assert 0 <= segredo.semente("cpf") < 2**32


def test_trocar_o_segredo_muda_o_ficticio(monkeypatch):
    """O fictício depende do segredo: sem ele, não dá para recalcular."""
    m13 = load_migration("13_anon_ine.py")
    antes = m13._fake_ine("0000123456")
    monkeypatch.setenv("ANON_SEGREDO", "outro-segredo-" + "1" * 32)
    assert m13._fake_ine("0000123456") != antes


def test_segredo_ausente_ou_curto_falha(monkeypatch):
    monkeypatch.setattr(segredo, "load_dotenv", lambda: None)
    monkeypatch.setenv("ANON_SEGREDO", "curto")
    with pytest.raises(RuntimeError, match="ANON_SEGREDO"):
        segredo.sal("cns")
    monkeypatch.delenv("ANON_SEGREDO")
    with pytest.raises(RuntimeError, match="ANON_SEGREDO"):
        segredo.sal("cns")
