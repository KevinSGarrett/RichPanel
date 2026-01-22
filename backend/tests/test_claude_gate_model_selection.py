from pathlib import Path
import os
import sys
import unittest


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import claude_gate_review


class TestClaudeGateModelSelection(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("CLAUDE_GATE_MODEL_OVERRIDE", None)

    def test_select_model_defaults(self):
        cases = {
            "risk:R0": "claude-haiku-4-5",
            "risk:R1": "claude-sonnet-4-5",
            "risk:R2": "claude-opus-4-5",
            "risk:R3": "claude-opus-4-5",
            "risk:R4": "claude-opus-4-5",
        }
        for risk, expected in cases.items():
            os.environ.pop("CLAUDE_GATE_MODEL_OVERRIDE", None)
            with self.subTest(risk=risk):
                self.assertEqual(claude_gate_review._select_model(risk), expected)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
