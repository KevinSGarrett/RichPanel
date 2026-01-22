from pathlib import Path
import sys

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import claude_gate_review


@pytest.mark.parametrize(
    ("risk", "expected"),
    [
        ("risk:R0", "claude-haiku-4-5"),
        ("risk:R1", "claude-sonnet-4-5"),
        ("risk:R2", "claude-opus-4-5"),
        ("risk:R3", "claude-opus-4-5"),
        ("risk:R4", "claude-opus-4-5"),
    ],
)
def test_select_model_defaults(monkeypatch, risk, expected):
    monkeypatch.delenv("CLAUDE_GATE_MODEL_OVERRIDE", raising=False)
    assert claude_gate_review._select_model(risk) == expected
