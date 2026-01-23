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

    def test_helper_metrics(self) -> None:
        self.assertEqual(harness._format_rate(0, 0), "N/A")
        self.assertEqual(harness._format_int(None), "N/A")
        self.assertEqual(harness._format_count(None), "N/A")
        self.assertEqual(harness._percentile([1, 2, 3], 0.9), 3.0)
        self.assertEqual(harness._median([1, 2, 3, 4]), 2.5)
        self.assertEqual(harness._median([1, 2, 3]), 2.0)

    def test_false_positive_label_and_truncation(self) -> None:
        self.assertTrue(harness._detect_truncation({"diff_truncated": True}, ""))
        self.assertTrue(harness._detect_truncation({}, "abc\n[TRUNCATED]\n"))
        self.assertFalse(harness._detect_truncation({}, "no truncation"))
        self.assertEqual(harness._extract_false_positive_label({"kpi_labels": {"false_positive": True}}), True)
        self.assertEqual(
            harness._extract_false_positive_label({"kpi_labels": {"action_required_real": True}}),
            False,
        )

    def test_load_fixture_bundle_at_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(RuntimeError):
                harness._load_fixture_bundle_at(Path(temp_dir), "missing")

    def test_evaluate_fixture_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixtures_dir = Path(temp_dir)
            fixture_dir = fixtures_dir / "legacy_fixture"
            fixture_dir.mkdir()
            metadata = {
                "title": "Legacy fixture",
                "body": "Body",
                "labels": ["gate:claude", "risk:R2"],
                "files": [],
                "usage": {"input_tokens": 5, "output_tokens": 5},
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
                json.dumps({"version": "1.0", "verdict": "PASS", "risk": "risk:R2", "reviewers": []}),
                encoding="utf-8",
            )
            result = harness._evaluate_fixture(
                "legacy_fixture",
                mode="legacy",
                review_config={},
                fixtures_dir=fixtures_dir,
            )
            self.assertEqual(result["action_required_count"], 0)

    def test_evaluate_fixture_parse_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixtures_dir = Path(temp_dir)
            fixture_dir = fixtures_dir / "bad_structured"
            fixture_dir.mkdir()
            metadata = {
                "title": "Structured fixture",
                "body": "Body",
                "labels": ["gate:claude", "risk:R2"],
                "files": [],
                "usage": {"input_tokens": 5, "output_tokens": 5},
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
                "not-json", encoding="utf-8"
            )
            result = harness._evaluate_fixture(
                "bad_structured",
                mode="structured",
                review_config={},
                fixtures_dir=fixtures_dir,
            )
            self.assertTrue(result["parse_error"])

    def test_compute_metrics_duplicates(self) -> None:
        results = [
            {
                "action_required_count": 1,
                "action_required_ids": ["dup"],
                "token_total": 10,
                "diff_truncated": True,
                "parse_error": False,
            },
            {
                "action_required_count": 1,
                "action_required_ids": ["dup"],
                "token_total": 20,
                "diff_truncated": False,
                "parse_error": True,
            },
        ]
        metrics = harness._compute_metrics(results)
        self.assertEqual(metrics["duplicate_finding_total"], 1)
        self.assertEqual(metrics["parse_failures"], 1)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
