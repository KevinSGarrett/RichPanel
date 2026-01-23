#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from typing import Any

import claude_review_kpi_snapshot as snapshot


class TestClaudeReviewKpiParser(unittest.TestCase):
    def test_parse_legacy_comment(self) -> None:
        body = """<!-- CLAUDE_REVIEW_CANONICAL -->
Claude Review (gate:claude)
Mode: LEGACY
CLAUDE_REVIEW: PASS
Risk: risk:R2
Model used: claude-opus-4-5-20251101
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
Model used: claude-opus-4-5-20251101
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
            raw_loaded: list[dict[str, Any]] = snapshot._load_comments_from_path(  # type: ignore[assignment]
                str(raw_path)
            )
            self.assertIsInstance(raw_loaded, list)
            assert isinstance(raw_loaded, list)
            first = next(iter(raw_loaded), {})
            self.assertEqual(first.get("body"), "raw comment")

            list_path = temp_path / "list.json"
            list_path.write_text(
                json.dumps([{"body": "one"}, {"body": "two"}]), encoding="utf-8"
            )
            list_loaded: list[dict[str, Any]] = snapshot._load_comments_from_path(  # type: ignore[assignment]
                str(list_path)
            )
            self.assertIsInstance(list_loaded, list)
            assert isinstance(list_loaded, list)
            self.assertEqual(len(list_loaded), 2)

            mapping_path = temp_path / "map.json"
            mapping_path.write_text(json.dumps({"153": [{"body": "mapped"}]}), encoding="utf-8")
            mapping_loaded: dict[int, list[dict[str, Any]]] = snapshot._load_comments_from_path(  # type: ignore[assignment]
                str(mapping_path)
            )
            self.assertIsInstance(mapping_loaded, dict)
            assert isinstance(mapping_loaded, dict)
            self.assertEqual(mapping_loaded[153][0].get("body"), "mapped")  # type: ignore[index]

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

    def test_parse_comment_structured_parse_failure(self) -> None:
        body = """<!-- CLAUDE_REVIEW_CANONICAL -->
Claude Review (gate:claude)
Mode: STRUCTURED
CLAUDE_REVIEW: PASS
WARNING: Structured output parse failure.
"""
        parsed = snapshot.parse_claude_review_comment(body)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertTrue(parsed["parse_error"])

    def test_count_bullets_after_stops_on_details(self) -> None:
        body = """Action Required:
- Item 1
- Item 2
<details>
<summary>FYI</summary>
"""
        count = snapshot._count_bullets_after("Action Required:", body)
        self.assertEqual(count, 2)

    def test_extract_header_value_missing(self) -> None:
        self.assertIsNone(snapshot._extract_header_value(snapshot._MODE_RE, "no mode here"))

    def test_count_bullets_after_missing_header(self) -> None:
        self.assertIsNone(snapshot._count_bullets_after("Action Required:", "no header"))

    def test_extract_action_required_count_summary(self) -> None:
        body = "Summary: action_required=3, total_points=5"
        self.assertEqual(snapshot._extract_action_required_count(body, None), 3)

    def test_extract_action_required_count_legacy(self) -> None:
        body = """Top findings:
- Issue 1
- Issue 2
"""
        self.assertEqual(snapshot._extract_action_required_count(body, "LEGACY"), 2)

    def test_parse_comment_without_tokens(self) -> None:
        body = """<!-- CLAUDE_REVIEW_CANONICAL -->
Claude Review (gate:claude)
Mode: LEGACY
CLAUDE_REVIEW: PASS
Top findings:
- No issues found.
"""
        parsed = snapshot.parse_claude_review_comment(body)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertIsNone(parsed["token_input"])
        self.assertIsNone(parsed["token_output"])

    def test_parse_comment_empty_body(self) -> None:
        self.assertIsNone(snapshot.parse_claude_review_comment(""))

    @patch("claude_review_kpi_snapshot.gate_comments._github_request_json")
    @patch("claude_review_kpi_snapshot.gate_comments._parse_github_datetime")
    def test_fetch_pr_numbers_since(self, mock_parse, mock_request) -> None:
        mock_parse.return_value = snapshot.datetime.max.replace(tzinfo=snapshot.timezone.utc)
        mock_request.side_effect = [
            [{"number": 11, "updated_at": "now"}, {"number": 12, "updated_at": "now"}],
            [],
        ]
        numbers = snapshot._fetch_pr_numbers_since("owner/repo", 7, "token")
        self.assertEqual(numbers, [11, 12])

    @patch("claude_review_kpi_snapshot.gate_comments._github_request_json")
    def test_fetch_pr_numbers_since_empty_payload(self, mock_request) -> None:
        mock_request.return_value = []
        self.assertEqual(snapshot._fetch_pr_numbers_since("owner/repo", 7, "token"), [])

    def test_load_comments_from_path_dict_variants(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            comments_path = temp_path / "comments.json"
            comments_path.write_text(json.dumps({"comments": [{"body": "c1"}]}), encoding="utf-8")
            loaded = snapshot._load_comments_from_path(str(comments_path))
            self.assertIsInstance(loaded, list)

            body_path = temp_path / "body.json"
            body_path.write_text(json.dumps({"body": "b1"}), encoding="utf-8")
            loaded_body = snapshot._load_comments_from_path(str(body_path))
            self.assertIsInstance(loaded_body, list)

            empty_map = temp_path / "empty.json"
            empty_map.write_text(json.dumps({"nope": []}), encoding="utf-8")
            loaded_empty = snapshot._load_comments_from_path(str(empty_map))
            self.assertEqual(loaded_empty, [])

            json_string = temp_path / "string.json"
            json_string.write_text(json.dumps("hello"), encoding="utf-8")
            loaded_string = snapshot._load_comments_from_path(str(json_string))
            self.assertIsInstance(loaded_string, list)

    def test_select_canonical_comment_none(self) -> None:
        self.assertIsNone(snapshot._select_canonical_comment([{"body": "no marker"}]))

    def test_select_canonical_comment_latest(self) -> None:
        comments = [
            {
                "id": 1,
                "body": "<!-- CLAUDE_REVIEW_CANONICAL -->\nClaude Review (gate:claude)",
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": 2,
                "body": "<!-- CLAUDE_REVIEW_CANONICAL -->\nClaude Review (gate:claude)",
                "updated_at": "2025-01-02T00:00:00Z",
            },
        ]
        canonical = snapshot._select_canonical_comment(comments)
        self.assertIsNotNone(canonical)
        assert canonical is not None
        self.assertEqual(canonical["id"], 2)

    def test_format_helpers(self) -> None:
        self.assertEqual(snapshot._format_rate(1, 4), "25% (1/4)")
        self.assertIsNone(snapshot._percentile([], 0.9))
        self.assertEqual(snapshot._format_count(1.25), "1.2")

    def test_main_requires_prs_or_since(self) -> None:
        with patch.object(sys, "argv", ["prog", "--repo", "owner/repo"]):
            with self.assertRaises(SystemExit):
                snapshot.main()

    def test_main_rejects_prs_and_since(self) -> None:
        with patch.object(sys, "argv", ["prog", "--repo", "owner/repo", "--prs", "1", "--since-days", "7"]):
            with self.assertRaises(SystemExit):
                snapshot.main()

    def test_main_missing_token(self) -> None:
        with patch.object(sys, "argv", ["prog", "--repo", "owner/repo", "--prs", "1"]):
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(snapshot.main(), 2)

    def test_main_offline_comment_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            comment_path = Path(temp_dir) / "comments.json"
            comment_path.write_text(
                json.dumps(
                    {
                        "1": [
                            {
                                "body": "<!-- CLAUDE_REVIEW_CANONICAL -->\n"
                                "Claude Review (gate:claude)\n"
                                "Mode: LEGACY\n"
                                "CLAUDE_REVIEW: PASS\n"
                                "Top findings:\n"
                                "- No issues found."
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(
                sys,
                "argv",
                [
                    "prog",
                    "--repo",
                    "owner/repo",
                    "--prs",
                    "1",
                    "--comment-path",
                    str(comment_path),
                ],
            ):
                self.assertEqual(snapshot.main(), 0)

    def test_main_since_days_uses_fetch(self) -> None:
        comment = {
            "body": "<!-- CLAUDE_REVIEW_CANONICAL -->\nClaude Review (gate:claude)\nMode: LEGACY\nCLAUDE_REVIEW: PASS"
        }
        with patch.object(sys, "argv", ["prog", "--repo", "owner/repo", "--since-days", "7"]):
            with patch.dict(os.environ, {"GITHUB_TOKEN": "token"}):
                with patch(
                    "claude_review_kpi_snapshot._fetch_pr_numbers_since", return_value=[1]
                ), patch(
                    "claude_review_kpi_snapshot.gate_comments._list_issue_comments",
                    return_value=[comment],
                ):
                    self.assertEqual(snapshot.main(), 0)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
