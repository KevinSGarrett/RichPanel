#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import claude_review_kpi_snapshot as snapshot


class TestClaudeReviewKpiParser(unittest.TestCase):
    def test_parse_legacy_comment(self) -> None:
        body = """<!-- CLAUDE_REVIEW_CANONICAL -->
Claude Review (gate:claude)
Mode: LEGACY
CLAUDE_REVIEW: PASS
Risk: risk:R2
Model used: claude-opus-4-5
skip=false
Token Usage: input=21814, output=18

Top findings:
- No issues found.
"""
        parsed = snapshot.parse_claude_review_comment(body)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["mode"], "LEGACY")
        self.assertEqual(parsed["verdict"], "PASS")
        self.assertEqual(parsed["action_required_count"], 0)
        self.assertEqual(parsed["token_input"], 21814)
        self.assertEqual(parsed["token_output"], 18)

    def test_parse_structured_comment(self) -> None:
        body = """<!-- CLAUDE_REVIEW_CANONICAL -->
Claude Review (gate:claude)
Mode: STRUCTURED
CLAUDE_REVIEW: FAIL
Risk: risk:R3
Model used: claude-opus-4-5
Token Usage: input=2222, output=111

Summary: action_required=2, total_points=6, highest_severity_action_required=4

Action Required:
- [S4/C85, pts=12] Timeout missing (app.py) evidence="timeout=None"
- [S3/C80, pts=9] Idempotency gap (app.py) evidence="retry()"
"""
        parsed = snapshot.parse_claude_review_comment(body)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["mode"], "STRUCTURED")
        self.assertEqual(parsed["verdict"], "FAIL")
        self.assertEqual(parsed["action_required_count"], 2)
        self.assertEqual(parsed["token_input"], 2222)
        self.assertEqual(parsed["token_output"], 111)

    def test_load_comments_from_path_variants(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            raw_path = temp_path / "raw.txt"
            raw_path.write_text("raw comment", encoding="utf-8")
            self.assertEqual(snapshot._load_comments_from_path(str(raw_path))[0]["body"], "raw comment")

            list_path = temp_path / "list.json"
            list_path.write_text(
                json.dumps([{"body": "one"}, {"body": "two"}]), encoding="utf-8"
            )
            list_loaded = snapshot._load_comments_from_path(str(list_path))
            self.assertEqual(len(list_loaded), 2)

            mapping_path = temp_path / "map.json"
            mapping_path.write_text(json.dumps({"153": [{"body": "mapped"}]}), encoding="utf-8")
            mapping_loaded = snapshot._load_comments_from_path(str(mapping_path))
            self.assertIsInstance(mapping_loaded, dict)
            assert isinstance(mapping_loaded, dict)
            self.assertEqual(mapping_loaded[153][0]["body"], "mapped")

    def test_select_canonical_comment(self) -> None:
        comments = [
            {"id": 1, "body": "no marker", "created_at": "2025-01-01T00:00:00Z"},
            {
                "id": 2,
                "body": "<!-- CLAUDE_REVIEW_CANONICAL -->\nClaude Review (gate:claude)",
                "created_at": "2025-01-02T00:00:00Z",
            },
        ]
        canonical = snapshot._select_canonical_comment(comments)
        self.assertIsNotNone(canonical)
        assert canonical is not None
        self.assertEqual(canonical["id"], 2)

    def test_extract_action_required_section(self) -> None:
        body = """<!-- CLAUDE_REVIEW_CANONICAL -->
Claude Review (gate:claude)
Mode: STRUCTURED
CLAUDE_REVIEW: PASS

Action Required:
- None
"""
        parsed = snapshot.parse_claude_review_comment(body)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["action_required_count"], 0)

    def test_render_snapshot_block(self) -> None:
        parsed = [
            {"mode": "LEGACY", "verdict": "PASS", "action_required_count": 0, "token_input": 10, "token_output": 1},
            {"mode": "STRUCTURED", "verdict": "FAIL", "action_required_count": 1, "token_input": 20, "token_output": 2},
        ]
        block = snapshot._render_snapshot(
            repo="example/repo", pr_numbers=[1, 2], parsed_results=parsed, missing_comments=0
        )
        self.assertIn("Claude Review KPI Snapshot", block)
        self.assertIn("Action Required rate", block)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
