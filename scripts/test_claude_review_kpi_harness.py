#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import claude_review_calibration_harness as harness


class TestClaudeReviewCalibrationHarness(unittest.TestCase):
    def test_harness_deterministic(self) -> None:
        fixtures = [
            "legacy_small",
            "structured_small",
            "wave2_lens_infra",
            "wave2_lens_order_status",
            "wave2_repeat_issue",
        ]
        first = harness.run_harness(fixtures, mode="structured")
        second = harness.run_harness(fixtures, mode="structured")
        self.assertEqual(first, second)
        self.assertEqual(first["overall"]["action_required_runs"], 3)

    @patch("urllib.request.urlopen", side_effect=AssertionError("network call"))
    def test_harness_offline(self, _mock_urlopen) -> None:
        fixtures = [
            "legacy_small",
            "structured_small",
            "wave2_lens_infra",
            "wave2_lens_order_status",
            "wave2_repeat_issue",
        ]
        harness.run_harness(fixtures, mode="structured")

    def test_custom_fixtures_dir_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixtures_dir = Path(temp_dir)
            fixture_dir = fixtures_dir / "custom_fixture"
            fixture_dir.mkdir()
            metadata = {
                "title": "Custom fixture",
                "body": "Custom fixture body",
                "labels": ["gate:claude", "risk:R2"],
                "files": [],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
            structured_response = {
                "version": "1.0",
                "verdict": "PASS",
                "risk": "risk:R2",
                "reviewers": [{"name": "primary", "model": "claude-opus-4-5", "findings": []}],
            }
            (fixture_dir / "fixture_pr_metadata.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
            (fixture_dir / "fixture_diff.txt").write_text("diff", encoding="utf-8")
            (fixture_dir / "fixture_anthropic_response_legacy.txt").write_text(
                "VERDICT: PASS\nFINDINGS:\n- No issues found.\n",
                encoding="utf-8",
            )
            (fixture_dir / "fixture_anthropic_response_structured.json").write_text(
                json.dumps(structured_response),
                encoding="utf-8",
            )
            results = harness.run_harness(
                ["custom_fixture"], mode="structured", fixtures_dir=fixtures_dir
            )
            self.assertEqual(results["overall"]["total_runs"], 1)
            self.assertEqual(results["results"][0]["risk"], "risk:R2")

    def test_render_scoreboard_output(self) -> None:
        fixtures = ["legacy_small", "structured_small"]
        results = harness.run_harness(fixtures, mode="structured")
        rendered = harness._render_scoreboard(
            results,
            fixtures=fixtures,
            mode="structured",
            start_date="2026-01-01",
            end_date="2026-01-02",
        )
        self.assertIn("Noise KPI Scoreboard", rendered)
        self.assertIn("Action Required rate", rendered)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
