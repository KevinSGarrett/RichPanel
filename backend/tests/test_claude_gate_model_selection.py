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
            "risk:R0": "claude-haiku-4-5-20251001",
            "risk:R1": "claude-sonnet-4-5-20250929",
            "risk:R2": "claude-opus-4-5-20251101",
            "risk:R3": "claude-opus-4-5-20251101",
            "risk:R4": "claude-opus-4-5-20251101",
        }
        for risk, expected in cases.items():
            os.environ.pop("CLAUDE_GATE_MODEL_OVERRIDE", None)
            with self.subTest(risk=risk):
                self.assertEqual(claude_gate_review._select_model(risk), expected)

    def test_normalize_risk_accepts_all_levels(self):
        for risk in ["risk:R0", "risk:R1", "risk:R2", "risk:R3", "risk:R4"]:
            with self.subTest(risk=risk):
                result = claude_gate_review._normalize_risk(["gate:claude", risk])
                self.assertEqual(result, risk)

    def test_select_model_override_allowlisted(self):
        os.environ["CLAUDE_GATE_MODEL_OVERRIDE"] = "claude-opus-4-5-20251101"
        self.assertEqual(claude_gate_review._select_model("risk:R0"), "claude-opus-4-5-20251101")

    def test_select_model_override_rejects_unlisted(self):
        os.environ["CLAUDE_GATE_MODEL_OVERRIDE"] = "claude-custom"
        with self.assertRaises(RuntimeError) as ctx:
            claude_gate_review._select_model("risk:R1")
        self.assertIn("not allowlisted", str(ctx.exception))

    def test_select_model_unknown_defaults_opus(self):
        self.assertEqual(
            claude_gate_review._select_model("risk:R9"),
            claude_gate_review.DEFAULT_FALLBACK_MODEL,
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
