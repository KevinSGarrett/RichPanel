#!/usr/bin/env python3
"""Unit tests for claude_gate_review.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Import the module under test
import claude_gate_review


class TestClaudeGateReview(unittest.TestCase):
    """Test suite for Claude gate review script."""

    def test_normalize_risk_valid_labels(self):
        """Test risk label normalization with valid labels."""
        labels = ["gate:claude", "risk:R2", "some-other-label"]
        result = claude_gate_review._normalize_risk(labels)
        self.assertEqual(result, "risk:R2")

    def test_normalize_risk_with_suffix(self):
        """Test risk label normalization with suffix."""
        labels = ["gate:claude", "risk:R1-low", "other"]
        result = claude_gate_review._normalize_risk(labels)
        self.assertEqual(result, "risk:R1")

    def test_normalize_risk_missing(self):
        """Test that missing risk label raises error."""
        labels = ["gate:claude", "other"]
        with self.assertRaises(RuntimeError) as ctx:
            claude_gate_review._normalize_risk(labels)
        self.assertIn("Missing required risk label", str(ctx.exception))

    def test_normalize_risk_multiple(self):
        """Test that multiple risk labels raise error."""
        labels = ["gate:claude", "risk:R1", "risk:R2"]
        with self.assertRaises(RuntimeError) as ctx:
            claude_gate_review._normalize_risk(labels)
        self.assertIn("Multiple risk labels found", str(ctx.exception))

    def test_model_selection_r0(self):
        """Test that R0 selects Haiku."""
        model = claude_gate_review.MODEL_BY_RISK["risk:R0"]
        self.assertEqual(model, "claude-haiku-4-5-20251001")

    def test_model_selection_r1(self):
        """Test that R1 selects Sonnet."""
        model = claude_gate_review.MODEL_BY_RISK["risk:R1"]
        self.assertEqual(model, "claude-sonnet-4-5-20250929")

    def test_model_selection_r2(self):
        """Test that R2 selects Opus."""
        model = claude_gate_review.MODEL_BY_RISK["risk:R2"]
        self.assertEqual(model, "claude-opus-4-5-20251101")

    def test_model_selection_r3(self):
        """Test that R3 selects Opus."""
        model = claude_gate_review.MODEL_BY_RISK["risk:R3"]
        self.assertEqual(model, "claude-opus-4-5-20251101")

    def test_model_selection_r4(self):
        """Test that R4 selects Opus."""
        model = claude_gate_review.MODEL_BY_RISK["risk:R4"]
        self.assertEqual(model, "claude-opus-4-5-20251101")

    def test_select_model_override(self):
        """Test that model override env var is honored."""
        os.environ["CLAUDE_GATE_MODEL_OVERRIDE"] = "claude-opus-4-5-20251101"
        try:
            model = claude_gate_review._select_model("risk:R1")
            self.assertEqual(model, "claude-opus-4-5-20251101")
        finally:
            os.environ.pop("CLAUDE_GATE_MODEL_OVERRIDE", None)

    def test_select_model_override_rejects_unlisted(self):
        os.environ["CLAUDE_GATE_MODEL_OVERRIDE"] = "claude-custom"
        try:
            with self.assertRaises(RuntimeError) as ctx:
                claude_gate_review._select_model("risk:R1")
            self.assertIn("not allowlisted", str(ctx.exception))
        finally:
            os.environ.pop("CLAUDE_GATE_MODEL_OVERRIDE", None)

    def test_select_model_invalid_risk_defaults_opus(self):
        """Test that unsupported risk label defaults to Opus."""
        model = claude_gate_review._select_model("risk:R9")
        self.assertEqual(model, claude_gate_review.DEFAULT_FALLBACK_MODEL)

    def test_select_model_unknown_risk_warns(self):
        captured = io.StringIO()
        with contextlib.redirect_stderr(captured):
            model = claude_gate_review._select_model("risk:R9")
        self.assertEqual(model, claude_gate_review.DEFAULT_FALLBACK_MODEL)
        self.assertIn("Unknown risk label", captured.getvalue())

    def test_parse_verdict_pass(self):
        """Test verdict parsing for PASS."""
        text = "VERDICT: PASS\nFINDINGS:\n- No issues found."
        verdict = claude_gate_review._parse_verdict(text)
        self.assertEqual(verdict, "PASS")

    def test_parse_verdict_fail(self):
        """Test verdict parsing for FAIL."""
        text = "VERDICT: FAIL\nFINDINGS:\n- Critical security issue."
        verdict = claude_gate_review._parse_verdict(text)
        self.assertEqual(verdict, "FAIL")

    def test_parse_verdict_missing(self):
        """Test verdict parsing defaults to FAIL when missing."""
        text = "No clear verdict here."
        verdict = claude_gate_review._parse_verdict(text)
        self.assertEqual(verdict, "FAIL")

    def test_extract_findings(self):
        """Test findings extraction."""
        text = """VERDICT: FAIL
FINDINGS:
- Issue 1
- Issue 2
- Issue 3
"""
        findings = claude_gate_review._extract_findings(text, max_findings=5)
        self.assertEqual(len(findings), 3)
        self.assertEqual(findings[0], "Issue 1")
        self.assertEqual(findings[1], "Issue 2")
        self.assertEqual(findings[2], "Issue 3")

    def test_extract_findings_max_limit(self):
        """Test findings extraction respects max limit."""
        text = """FINDINGS:
- Issue 1
- Issue 2
- Issue 3
- Issue 4
- Issue 5
- Issue 6
"""
        findings = claude_gate_review._extract_findings(text, max_findings=3)
        self.assertEqual(len(findings), 3)

    def test_extract_text_from_response(self):
        """Test text extraction from Anthropic response."""
        response = {
            "content": [
                {"type": "text", "text": "First chunk"},
                {"type": "text", "text": "Second chunk"},
            ]
        }
        text = claude_gate_review._extract_text(response)
        self.assertEqual(text, "First chunk\nSecond chunk")

    def test_extract_text_empty(self):
        """Test text extraction with empty content."""
        response = {"content": []}
        text = claude_gate_review._extract_text(response)
        self.assertEqual(text, "")

    def test_extract_request_id_prefers_primary(self):
        """Test request id extraction prefers primary header."""
        headers = {"x-request-id": "req_secondary", "request-id": "req_primary"}
        request_id = claude_gate_review._extract_request_id(headers)
        self.assertEqual(request_id, "req_primary")

    def test_extract_request_id_case_insensitive(self):
        """Test request id extraction handles mixed-case headers."""
        headers = {"Request-Id": "req_caps"}
        request_id = claude_gate_review._extract_request_id(headers)
        self.assertEqual(request_id, "req_caps")

    def test_extract_request_id_missing(self):
        """Test request id extraction returns empty when missing."""
        request_id = claude_gate_review._extract_request_id({})
        self.assertEqual(request_id, "")

    def test_normalize_headers_handles_none(self):
        self.assertEqual(claude_gate_review._normalize_headers(None), {})

    def test_normalize_headers_handles_non_mapping(self):
        self.assertEqual(claude_gate_review._normalize_headers(123), {})

    def test_normalize_headers_empty_dict(self):
        self.assertEqual(claude_gate_review._normalize_headers({}), {})

    def test_normalize_headers_skips_none_key(self):
        self.assertEqual(
            claude_gate_review._normalize_headers({None: "value", "Ok": "yes"}),
            {"ok": "yes"},
        )

    def test_coerce_token_count_invalid(self):
        """Test token count coercion for invalid values."""
        self.assertEqual(claude_gate_review._coerce_token_count("oops"), 0)
        self.assertEqual(claude_gate_review._coerce_token_count(None), 0)

    def test_format_comment_with_response_id(self):
        """Test comment formatting includes response ID."""
        comment = claude_gate_review._format_comment(
            verdict="PASS",
            risk="risk:R2",
            model="claude-opus-4-5-20251101",
            findings=["No issues found."],
            response_id="msg_abc123xyz",
            request_id="req_789xyz",
            usage={"input_tokens": 1000, "output_tokens": 200},
            response_model="claude-opus-4-5-20251101",
        )
        self.assertTrue(comment.startswith(claude_gate_review.CANONICAL_MARKER))
        self.assertIn("Mode: LEGACY", comment)
        self.assertIn("CLAUDE_REVIEW: PASS", comment)
        self.assertIn("Risk: risk:R2", comment)
        self.assertIn("Model used: claude-opus-4-5-20251101", comment)
        self.assertIn("Response model: claude-opus-4-5-20251101", comment)
        self.assertIn("skip=false", comment)
        self.assertIn("Anthropic Response ID: msg_abc123xyz", comment)
        self.assertIn("Anthropic Request ID: req_789xyz", comment)
        self.assertIn("Token Usage: input=1000, output=200", comment)
        self.assertIn("- No issues found.", comment)

    def test_format_comment_without_response_id(self):
        """Test comment formatting without response ID (backward compat)."""
        comment = claude_gate_review._format_comment(
            verdict="FAIL",
            risk="risk:R1",
            model="claude-sonnet-4-5-20250929",
            findings=["Issue 1", "Issue 2"],
        )
        self.assertTrue(comment.startswith(claude_gate_review.CANONICAL_MARKER))
        self.assertIn("Mode: LEGACY", comment)
        self.assertIn("CLAUDE_REVIEW: FAIL", comment)
        self.assertIn("Risk: risk:R1", comment)
        self.assertIn("Model used: claude-sonnet-4-5-20250929", comment)
        self.assertIn("skip=false", comment)
        self.assertNotIn("Response model", comment)
        self.assertNotIn("Anthropic Response ID", comment)
        self.assertNotIn("Token Usage", comment)
        self.assertIn("- Issue 1", comment)
        self.assertIn("- Issue 2", comment)

    def test_truncate_text(self):
        """Test text truncation."""
        text = "a" * 100
        truncated = claude_gate_review._truncate(text, 50)
        self.assertTrue(len(truncated) < len(text))
        self.assertIn("[TRUNCATED]", truncated)

    def test_truncate_short_text(self):
        """Test truncation doesn't affect short text."""
        text = "short"
        truncated = claude_gate_review._truncate(text, 100)
        self.assertEqual(text, truncated)

    def test_build_prompt_includes_failed_checks(self):
        """Ensure failed checks are injected into the prompt."""
        prompt = claude_gate_review._build_prompt(
            "Title",
            "Body",
            "risk:R2",
            "- file.py (modified, +1 -0)",
            "diff",
            failed_checks=["Bugbot: issue", "Codecov"],
        )
        self.assertIn("FAILED CHECKS", prompt)
        self.assertIn("Bugbot: issue", prompt)
        self.assertIn("do not repeat them", prompt)

    def test_build_prompt_without_failed_checks(self):
        prompt = claude_gate_review._build_prompt(
            "Title",
            "Body",
            "risk:R2",
            "- file.py (modified, +1 -0)",
            "diff",
        )
        self.assertNotIn("FAILED CHECKS", prompt)

    def test_fetch_failed_check_summaries(self):
        """Fetch failed check summaries from mocked API payload."""
        payload = {
            "check_runs": [
                {"name": "Lint", "status": "completed", "conclusion": "success"},
                {"name": "Bugbot", "status": "completed", "conclusion": "failure"},
                {
                    "name": "Codecov",
                    "status": "completed",
                    "conclusion": "action_required",
                    "output": {"title": "Coverage drop"},
                },
            ]
        }
        with patch("claude_gate_review._fetch_json", return_value=payload):
            summaries = claude_gate_review._fetch_failed_check_summaries(
                "owner/repo", "deadbeef", "token"
            )
        self.assertEqual(summaries, ["Bugbot", "Codecov: Coverage drop"])

    def test_extract_failed_check_summaries_filters(self):
        runs = [
            {"name": "Build", "status": "in_progress", "conclusion": "failure"},
            {"name": "Docs", "status": "completed", "conclusion": "success"},
            {"name": "CI", "status": "completed", "conclusion": "cancelled"},
            {"name": "", "status": "completed", "conclusion": "failure", "output": {"title": "Only title"}},
            {"name": "CI", "status": "completed", "conclusion": "cancelled"},
        ]
        summaries = claude_gate_review._extract_failed_check_summaries(runs, limit=3)
        self.assertEqual(summaries, ["CI", "Only title"])

    def test_extract_failed_check_summaries_title_equals_name(self):
        runs = [
            {
                "name": "Codecov",
                "status": "",
                "conclusion": "failure",
                "output": {"title": "Codecov"},
            },
            {
                "name": "Docs",
                "status": "completed",
                "conclusion": "failure",
                "output": [],
            },
        ]
        summaries = claude_gate_review._extract_failed_check_summaries(runs, limit=2)
        self.assertEqual(summaries, ["Codecov", "Docs"])

    def test_fetch_failed_check_summaries_empty(self):
        self.assertEqual(claude_gate_review._fetch_failed_check_summaries("owner/repo", "", "token"), [])
        with patch("claude_gate_review._fetch_json", return_value=[]):
            self.assertEqual(
                claude_gate_review._fetch_failed_check_summaries("owner/repo", "deadbeef", "token"),
                [],
            )
        with patch("claude_gate_review._fetch_json", return_value={"check_runs": "nope"}):
            self.assertEqual(
                claude_gate_review._fetch_failed_check_summaries("owner/repo", "deadbeef", "token"),
                [],
            )

        with patch("claude_gate_review._fetch_json", return_value=["unexpected"]):
            self.assertEqual(
                claude_gate_review._fetch_failed_check_summaries("owner/repo", "deadbeef", "token"),
                [],
            )

    def test_extract_failed_check_summaries_skips_empty(self):
        runs = [
            {"status": "completed", "conclusion": "failure"},
            {"status": "completed", "conclusion": "timed_out"},
        ]
        summaries = claude_gate_review._extract_failed_check_summaries(runs, limit=5)
        self.assertEqual(summaries, [])

    def test_coerce_json_text(self):
        fenced = """```json
{"version":"1.0"}
```"""
        self.assertEqual(claude_gate_review._coerce_json_text(fenced), '{"version":"1.0"}')
        wrapped = "prefix {\"version\":\"1.0\"} suffix"
        self.assertEqual(claude_gate_review._coerce_json_text(wrapped), '{"version":"1.0"}')
        disclaimer = "Heads up:\n```json\n{\"version\":\"1.0\"}\n```\nThanks"
        self.assertEqual(claude_gate_review._coerce_json_text(disclaimer), '{"version":"1.0"}')
        balanced = 'prefix {"version":"1.0","note":"brace } inside"} suffix'
        self.assertEqual(
            claude_gate_review._coerce_json_text(balanced),
            '{"version":"1.0","note":"brace } inside"}',
        )
        escaped = (
            'prefix {"version":"1.0","note":"escaped \\\\\"quote\\\\\" and brace } '
            'inside","unicode":"\\u2603"} suffix'
        )
        self.assertEqual(
            claude_gate_review._coerce_json_text(escaped),
            '{"version":"1.0","note":"escaped \\\\\"quote\\\\\" and brace } inside","unicode":"\\u2603"}',
        )

    def test_extract_first_json_object_none(self):
        self.assertIsNone(claude_gate_review._extract_first_json_object("no json here"))

    def test_extract_first_json_object_unbalanced(self):
        self.assertIsNone(claude_gate_review._extract_first_json_object("{\"a\": 1"))

    def test_extract_json_candidate_empty(self):
        self.assertIsNone(claude_gate_review._extract_json_candidate(""))

    def test_extract_json_candidate_empty_fence(self):
        raw = "```json\nnot-json\n```"
        self.assertIsNone(claude_gate_review._extract_json_candidate(raw))

    def test_extract_json_candidate_no_json(self):
        self.assertIsNone(claude_gate_review._extract_json_candidate("prefix only"))

    def test_parse_structured_output_with_fence(self):
        raw = """```json
{"version":"1.0","verdict":"PASS","risk":"risk:R2","reviewers":[]}
```"""
        payload, findings, errors = claude_gate_review._parse_structured_output(raw, "")
        self.assertEqual(payload.get("version"), "1.0")
        self.assertEqual(findings, [])
        self.assertEqual(errors, [])

    def test_parse_structured_output_with_disclaimer(self):
        raw = """Here is the JSON:
```json
{"version":"1.0","verdict":"PASS","risk":"risk:R2","reviewers":[]}
```
Let me know if you need more."""
        payload, findings, errors = claude_gate_review._parse_structured_output(raw, "")
        self.assertEqual(payload.get("verdict"), "PASS")
        self.assertEqual(findings, [])
        self.assertEqual(errors, [])

    def test_build_prompt(self):
        """Test prompt building includes all required sections."""
        prompt = claude_gate_review._build_prompt(
            title="Test PR",
            body="This is a test",
            risk="risk:R2",
            files_summary="- file1.py (modified, +10 -5)",
            diff_text="diff content here",
            lens_text="LENSES_APPLIED: [BASELINE_CODE_SAFETY]",
        )
        self.assertIn("PR TITLE (untrusted input):", prompt)
        self.assertIn("Test PR", prompt)
        self.assertIn("PR BODY (untrusted input):", prompt)
        self.assertIn("This is a test", prompt)
        self.assertIn("RISK LABEL: risk:R2", prompt)
        self.assertIn("LENSES_APPLIED: [BASELINE_CODE_SAFETY]", prompt)
        self.assertIn("CHANGED FILES:", prompt)
        self.assertIn("- file1.py (modified, +10 -5)", prompt)
        self.assertIn("UNIFIED DIFF (untrusted input):", prompt)
        self.assertIn("diff content here", prompt)

    def test_load_review_config_missing(self):
        missing_path = Path(tempfile.gettempdir()) / "missing_claude_review.yml"
        missing_path.write_text("version: 1\n", encoding="utf-8")
        self.assertTrue(missing_path.exists())
        missing_path.unlink()
        config = claude_gate_review._load_review_config(missing_path)
        self.assertEqual(config, {})

    def test_load_review_config_valid(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yml") as handle:
            handle.write("version: 1\nrisk_defaults:\n  R2:\n    max_findings: 4\n")
            path = Path(handle.name)
        try:
            config = claude_gate_review._load_review_config(path)
            self.assertIn("risk_defaults", config)
            self.assertEqual(config["risk_defaults"]["R2"]["max_findings"], 4)
        finally:
            if path.exists():
                path.unlink()

    def test_load_review_config_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yml") as handle:
            handle.write("risk_defaults: [")
            path = Path(handle.name)
        try:
            config = claude_gate_review._load_review_config(path)
            self.assertEqual(config, {})
        finally:
            if path.exists():
                path.unlink()

    def test_get_risk_defaults_merge(self):
        config = {
            "risk_defaults": {
                "R2": {
                    "max_findings": 7,
                    "action_required_min_confidence": 80,
                }
            }
        }
        defaults = claude_gate_review._get_risk_defaults(config, "risk:R2")
        self.assertEqual(defaults["max_findings"], 7)
        self.assertEqual(defaults["action_required_min_confidence"], 80)
        self.assertEqual(defaults["action_required_min_severity"], 3)

    def test_select_lenses_matches_paths(self):
        config = {
            "lenses": {
                "A": {"paths": ["backend/src/**"], "invariants": ["A1"]},
                "B": {"paths": ["infra/**"], "invariants": ["B1"]},
            }
        }
        selected = claude_gate_review._select_lenses(["backend/src/orders.py"], config)
        self.assertEqual(selected[0][0], "A")
        selected_nested = claude_gate_review._select_lenses(["backend/src/models/order.py"], config)
        self.assertEqual(selected_nested[0][0], "A")

    def test_select_lenses_default_when_none(self):
        config = {"lenses": {"A": {"paths": ["backend/src/**"], "invariants": ["A1"]}}}
        selected = claude_gate_review._select_lenses(["docs/readme.md"], config)
        self.assertEqual(selected[0][0], claude_gate_review.DEFAULT_LENS_NAME)

    def test_select_lenses_caps_max(self):
        config = {
            "lenses": {
                "L1": {"paths": ["backend/**"], "invariants": []},
                "L2": {"paths": ["backend/**"], "invariants": []},
                "L3": {"paths": ["backend/**"], "invariants": []},
                "L4": {"paths": ["backend/**"], "invariants": []},
                "L5": {"paths": ["backend/**"], "invariants": []},
            }
        }
        selected = claude_gate_review._select_lenses(["backend/src/orders.py"], config)
        self.assertEqual(len(selected), claude_gate_review.MAX_LENSES)

    def test_build_lens_prompt_caps_invariants(self):
        lenses = [
            (
                "LENS_A",
                {"invariants": [f"inv-{idx}" for idx in range(6)]},
            )
        ]
        prompt = claude_gate_review._build_lens_prompt(lenses)
        self.assertIn("LENSES_APPLIED: [LENS_A]", prompt)
        self.assertIn("- inv-0", prompt)
        self.assertIn("- inv-4", prompt)
        self.assertNotIn("- inv-5", prompt)

    def test_apply_budgets_truncates(self):
        findings = [
            {
                "finding_id": "c",
                "severity": 5,
                "confidence": 90,
                "file": "c.py",
                "evidence": "line",
                "points": 5,
            },
            {
                "finding_id": "a",
                "severity": 3,
                "confidence": 80,
                "file": "a.py",
                "evidence": "line",
                "points": 3,
            },
            {
                "finding_id": "b",
                "severity": 2,
                "confidence": 90,
                "file": "",
                "evidence": "",
                "points": 2,
            },
        ]
        action_required, fyi = claude_gate_review._apply_budgets(
            findings,
            {"max_findings": 2, "action_required_min_severity": 3, "action_required_min_confidence": 70},
        )
        self.assertEqual(len(action_required), 2)
        self.assertEqual([item["finding_id"] for item in action_required], ["c", "a"])
        self.assertEqual(fyi, [])

    def test_apply_budgets_keeps_fyi(self):
        findings = [
            {
                "finding_id": "a",
                "severity": 3,
                "confidence": 80,
                "file": "a.py",
                "evidence": "line",
                "points": 3,
            },
            {
                "finding_id": "b",
                "severity": 2,
                "confidence": 90,
                "file": "",
                "evidence": "",
                "points": 2,
            },
        ]
        action_required, fyi = claude_gate_review._apply_budgets(
            findings,
            {"max_findings": 2, "action_required_min_severity": 3, "action_required_min_confidence": 70},
        )
        self.assertEqual(len(action_required), 1)
        self.assertEqual(len(fyi), 1)

    def test_apply_budgets_zero_max(self):
        action_required, fyi = claude_gate_review._apply_budgets(
            [],
            {"max_findings": 0, "action_required_min_severity": 3, "action_required_min_confidence": 70},
        )
        self.assertEqual(action_required, [])
        self.assertEqual(fyi, [])

    def test_extract_state_from_comment(self):
        payload = {"version": 1, "run_index": 2, "findings": {"a": {"occurrences": 1}}}
        comment = f"{claude_gate_review.STATE_MARKER}\n```json\n{json.dumps(payload)}\n```\n"
        payload = claude_gate_review._extract_state_from_comment(comment)
        self.assertEqual(payload["run_index"], 2)

    def test_extract_state_from_comment_invalid(self):
        comment = f"{claude_gate_review.STATE_MARKER}\n```json\nnot-json\n```\n"
        payload = claude_gate_review._extract_state_from_comment(comment)
        self.assertIsNone(payload)

    def test_find_canonical_comment_latest(self):
        comments = [
            {
                "id": 2,
                "created_at": "2024-01-02T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "body": claude_gate_review.CANONICAL_MARKER,
            },
            {
                "id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-03T00:00:00Z",
                "body": claude_gate_review.CANONICAL_MARKER,
            },
        ]
        selected = claude_gate_review._find_canonical_comment(comments)
        self.assertEqual(selected["id"], 1)

    @patch("claude_gate_review._fetch_json")
    def test_fetch_issue_comments_paginates(self, mock_fetch_json):
        mock_fetch_json.side_effect = [
            [{"id": 1}],
            [],
        ]
        comments = claude_gate_review._fetch_issue_comments("owner/repo", 1, "token")
        self.assertEqual(len(comments), 1)

    def test_build_state_payload_increments_occurrences(self):
        prev_state = {
            "version": 1,
            "run_index": 1,
            "findings": {
                "abc": {"occurrences": 1, "last_seen": 1},
                "old": {"occurrences": 1, "last_seen": -1},
            },
        }
        findings = [{"finding_id": "abc", "severity": 2}]
        state_payload, updated = claude_gate_review._build_state_payload(prev_state, findings)
        self.assertEqual(state_payload["run_index"], 2)
        self.assertIn("abc", state_payload["findings"])
        self.assertNotIn("old", state_payload["findings"])
        self.assertEqual(updated[0]["occurrences"], 2)
        self.assertEqual(updated[0]["points"], 4)

    def test_build_state_payload_retains_two_runs(self):
        prev_state = {
            "version": 1,
            "run_index": 2,
            "findings": {
                "recent": {"occurrences": 1, "last_seen": 2},
                "older": {"occurrences": 1, "last_seen": 1},
                "stale": {"occurrences": 1, "last_seen": 0},
            },
        }
        state_payload, _ = claude_gate_review._build_state_payload(prev_state, [])
        self.assertIn("recent", state_payload["findings"])
        self.assertIn("older", state_payload["findings"])
        self.assertNotIn("stale", state_payload["findings"])

    def test_evaluate_structured_response_parse_error_keeps_state(self):
        previous_state = {"version": 1, "run_index": 1, "findings": {"abc": {"occurrences": 1, "last_seen": 1}}}
        warnings: list[str] = []
        verdict, _, _, _, summary, state_payload, parse_error = claude_gate_review._evaluate_structured_response(
            "{",
            diff_text="",
            mode=claude_gate_review.MODE_SHADOW,
            bypass_enabled=False,
            warnings=warnings,
            risk_defaults=claude_gate_review.DEFAULT_RISK_DEFAULTS["R2"],
            previous_state=previous_state,
        )
        self.assertEqual(verdict, "PASS")
        self.assertIsNotNone(parse_error)
        self.assertEqual(summary["action_required_count"], 0)
        self.assertEqual(state_payload["findings"]["abc"]["occurrences"], 1)

    def test_evaluate_structured_response_explicit_blocker(self):
        payload = {
            "version": "1.0",
            "verdict": "PASS",
            "risk": "risk:R2",
            "reviewers": [
                {
                    "name": "primary",
                    "model": "claude-opus-4-5-20251101",
                    "findings": [
                        {
                            "finding_id": "blocker",
                            "category": "security",
                            "severity": 5,
                            "confidence": 90,
                            "title": "Critical",
                            "summary": "Critical issue",
                            "file": "app.py",
                            "evidence": "bad()",
                            "suggested_test": "Add test",
                        }
                    ],
                }
            ],
        }
        warnings: list[str] = []
        verdict, _, _, _, _, _, _ = claude_gate_review._evaluate_structured_response(
            json.dumps(payload),
            diff_text="bad()",
            mode=claude_gate_review.MODE_STRUCTURED,
            bypass_enabled=False,
            warnings=warnings,
            risk_defaults={"fail_min_points": 999, "action_required_min_severity": 3, "action_required_min_confidence": 70},
            previous_state=None,
        )
        self.assertEqual(verdict, "FAIL")

    def test_structured_verdict_uses_points_threshold(self):
        payload = {
            "version": "1.0",
            "verdict": "PASS",
            "risk": "risk:R2",
            "reviewers": [
                {
                    "name": "primary",
                    "model": "claude-opus-4-5-20251101",
                    "findings": [
                        {
                            "finding_id": "abc123",
                            "category": "reliability",
                            "severity": 3,
                            "confidence": 80,
                            "title": "Timeout missing",
                            "summary": "Timeout is None",
                            "file": "app.py",
                            "evidence": "timeout=None",
                            "suggested_test": "Add timeout test",
                        }
                    ],
                }
            ],
        }
        warnings: list[str] = []
        verdict, _, action_required, _, summary, _, parse_error = claude_gate_review._evaluate_structured_response(
            json.dumps(payload),
            diff_text="timeout=None",
            mode=claude_gate_review.MODE_STRUCTURED,
            bypass_enabled=False,
            warnings=warnings,
            risk_defaults={"fail_min_points": 2, "action_required_min_severity": 3, "action_required_min_confidence": 70},
            previous_state=None,
        )
        self.assertEqual(verdict, "FAIL")
        self.assertIsNone(parse_error)
        self.assertEqual(summary["total_points"], 3)
        self.assertEqual(len(action_required), 1)

    def test_is_approved_false_positive_all_approved(self):
        """Test approved false positive detection."""
        findings = [
            "anthropic_api_key is required",
            "rate limiting not configured",
        ]
        result = claude_gate_review._is_approved_false_positive(findings)
        self.assertTrue(result)

    def test_is_approved_false_positive_mixed(self):
        """Test approved false positive with real issue."""
        findings = [
            "anthropic_api_key is required",
            "SQL injection vulnerability detected",
        ]
        result = claude_gate_review._is_approved_false_positive(findings)
        self.assertFalse(result)

    def test_write_output(self):
        """Test GitHub Actions output writing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_path = f.name
        
        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            claude_gate_review._write_output("test_key", "test_value")
            
            with open(output_path, "r") as f:
                content = f.read()
            self.assertIn("test_key=test_value", content)
        finally:
            os.environ.pop("GITHUB_OUTPUT", None)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_require_env_present(self):
        """Test _require_env returns value when present."""
        os.environ["TEST_VAR"] = "test_value"
        try:
            result = claude_gate_review._require_env("TEST_VAR")
            self.assertEqual(result, "test_value")
        finally:
            os.environ.pop("TEST_VAR", None)

    def test_require_env_missing(self):
        """Test _require_env exits when missing."""
        os.environ.pop("MISSING_VAR", None)
        with self.assertRaises(SystemExit) as ctx:
            claude_gate_review._require_env("MISSING_VAR")
        self.assertEqual(ctx.exception.code, 2)

    @patch("urllib.request.urlopen")
    def test_anthropic_request_success(self, mock_urlopen):
        """Test successful Anthropic API request."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "id": "msg_test123",
            "content": [{"type": "text", "text": "VERDICT: PASS\nFINDINGS:\n- No issues."}],
            "usage": {"input_tokens": 500, "output_tokens": 100},
        }).encode("utf-8")
        mock_response.getcode.return_value = 200
        mock_response.headers = {"request-id": "req_test123"}
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result, request_id = claude_gate_review._anthropic_request(
            {"model": "claude-haiku-4-5-20251001", "messages": []},
            "test-api-key"
        )
        
        self.assertEqual(result["id"], "msg_test123")
        self.assertIn("content", result)
        self.assertIn("usage", result)
        self.assertEqual(request_id, "req_test123")

    @patch("urllib.request.urlopen")
    def test_anthropic_request_non_200(self, mock_urlopen):
        """Test Anthropic API non-200 response raises."""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 500
        mock_response.read.return_value = b"server error"
        mock_response.headers = {"request-id": "req_test123"}
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with self.assertRaises(RuntimeError) as ctx:
            claude_gate_review._anthropic_request(
                {"model": "claude-haiku-4-5-20251001", "messages": []},
                "test-api-key",
            )
        self.assertIn("unexpected status", str(ctx.exception).lower())

    @patch("urllib.request.urlopen")
    def test_anthropic_request_invalid_json(self, mock_urlopen):
        """Test Anthropic API invalid JSON raises."""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b"{invalid"
        mock_response.headers = {"request-id": "req_test123"}
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with self.assertRaises(RuntimeError) as ctx:
            claude_gate_review._anthropic_request(
                {"model": "claude-haiku-4-5-20251001", "messages": []},
                "test-api-key",
            )
        self.assertIn("invalid json", str(ctx.exception).lower())

    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_skip_without_gate_label(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json
    ):
        """Test that script fails when gate:claude label is missing."""
        # Mock PR data without gate:claude label
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "risk:R1"}],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_path = f.name
        
        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            # Don't set ANTHROPIC_API_KEY to prove we fail before checking it
            
            sys.argv = [
                "claude_gate_review.py",
                "--repo", "test/repo",
                "--pr-number", "123",
            ]
            
            with self.assertRaises(RuntimeError) as ctx:
                claude_gate_review.main()
            self.assertIn("gate:claude label missing", str(ctx.exception))

            # Verify Anthropic was NOT called
            mock_anthropic.assert_not_called()
        finally:
            os.environ.pop("GITHUB_OUTPUT", None)
            os.environ.pop("GITHUB_TOKEN", None)
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch("claude_gate_review._fetch_json")
    def test_main_fails_without_anthropic_key(self, mock_fetch_json):
        """Test that script fails when ANTHROPIC_API_KEY is missing."""
        # Mock PR data with gate:claude label
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "gate:claude"}, {"name": "risk:R2"}],
        }
        
        try:
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ.pop("ANTHROPIC_API_KEY", None)
            
            sys.argv = [
                "claude_gate_review.py",
                "--repo", "test/repo",
                "--pr-number", "123",
            ]
            
            result = claude_gate_review.main()
            # Should exit with code 2 (missing required env)
            self.assertEqual(result, 2)
        finally:
            os.environ.pop("GITHUB_TOKEN", None)

    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_fails_without_gate_label_even_if_force_set(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json
    ):
        """Test that missing gate:claude label fails even if CLAUDE_GATE_FORCE is set."""
        # Mock PR data WITHOUT gate:claude label
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "risk:R1"}],  # No gate:claude
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            comment_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            audit_path = f.name

        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["CLAUDE_GATE_COMMENT_PATH"] = comment_path
            os.environ["CLAUDE_GATE_AUDIT_PATH"] = audit_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ["ANTHROPIC_API_KEY"] = "fake-key"
            os.environ["CLAUDE_GATE_FORCE"] = "true"

            sys.argv = [
                "claude_gate_review.py",
                "--repo", "test/repo",
                "--pr-number", "123",
            ]

            with self.assertRaises(RuntimeError) as ctx:
                claude_gate_review.main()
            self.assertIn("gate:claude label missing", str(ctx.exception))

            mock_anthropic.assert_not_called()
        finally:
            os.environ.pop("GITHUB_OUTPUT", None)
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("CLAUDE_GATE_FORCE", None)
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_raises_when_response_id_missing(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json
    ):
        """Test that missing Anthropic response id raises an error."""
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "gate:claude"}, {"name": "risk:R2"}],
        }
        mock_fetch_files.return_value = []
        mock_fetch_raw.return_value = b"diff content"
        mock_anthropic.return_value = (
            {
                "model": "claude-opus-4-5-20251101",
                "content": [{"type": "text", "text": "VERDICT: PASS\nFINDINGS:\n- No issues."}],
                "usage": {"input_tokens": 100, "output_tokens": 20},
            },
            "req_test123",
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            comment_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            audit_path = f.name

        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["CLAUDE_GATE_COMMENT_PATH"] = comment_path
            os.environ["CLAUDE_GATE_AUDIT_PATH"] = audit_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ["ANTHROPIC_API_KEY"] = "fake-key"

            sys.argv = [
                "claude_gate_review.py",
                "--repo",
                "test/repo",
                "--pr-number",
                "123",
            ]

            with self.assertRaises(RuntimeError) as ctx:
                claude_gate_review.main()
            self.assertIn("missing id", str(ctx.exception).lower())
        finally:
            os.environ.pop("GITHUB_OUTPUT", None)
            os.environ.pop("CLAUDE_GATE_COMMENT_PATH", None)
            os.environ.pop("CLAUDE_GATE_AUDIT_PATH", None)
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            if os.path.exists(output_path):
                os.unlink(output_path)
            if os.path.exists(comment_path):
                os.unlink(comment_path)
            if os.path.exists(audit_path):
                os.unlink(audit_path)

    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_raises_when_request_id_missing(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json
    ):
        """Test that missing Anthropic request id raises an error."""
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "gate:claude"}, {"name": "risk:R2"}],
        }
        mock_fetch_files.return_value = []
        mock_fetch_raw.return_value = b"diff content"
        mock_anthropic.return_value = (
            {
                "id": "msg_test123",
                "model": "claude-opus-4-5-20251101",
                "content": [{"type": "text", "text": "VERDICT: PASS\nFINDINGS:\n- No issues."}],
                "usage": {"input_tokens": 100, "output_tokens": 20},
            },
            "",
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            comment_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            audit_path = f.name

        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["CLAUDE_GATE_COMMENT_PATH"] = comment_path
            os.environ["CLAUDE_GATE_AUDIT_PATH"] = audit_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ["ANTHROPIC_API_KEY"] = "fake-key"

            sys.argv = [
                "claude_gate_review.py",
                "--repo",
                "test/repo",
                "--pr-number",
                "123",
            ]

            with self.assertRaises(RuntimeError) as ctx:
                claude_gate_review.main()
            self.assertIn("request id", str(ctx.exception).lower())
        finally:
            os.environ.pop("GITHUB_OUTPUT", None)
            os.environ.pop("CLAUDE_GATE_COMMENT_PATH", None)
            os.environ.pop("CLAUDE_GATE_AUDIT_PATH", None)
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            if os.path.exists(output_path):
                os.unlink(output_path)
            if os.path.exists(comment_path):
                os.unlink(comment_path)
            if os.path.exists(audit_path):
                os.unlink(audit_path)

    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_raises_when_usage_missing(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json
    ):
        """Test that missing usage raises an error."""
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "gate:claude"}, {"name": "risk:R2"}],
        }
        mock_fetch_files.return_value = []
        mock_fetch_raw.return_value = b"diff content"
        mock_anthropic.return_value = (
            {
                "id": "msg_test123",
                "model": "claude-opus-4-5-20251101",
                "content": [{"type": "text", "text": "VERDICT: PASS\nFINDINGS:\n- No issues."}],
                "usage": None,
            },
            "req_test123",
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            comment_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            audit_path = f.name

        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["CLAUDE_GATE_COMMENT_PATH"] = comment_path
            os.environ["CLAUDE_GATE_AUDIT_PATH"] = audit_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ["ANTHROPIC_API_KEY"] = "fake-key"

            sys.argv = [
                "claude_gate_review.py",
                "--repo",
                "test/repo",
                "--pr-number",
                "123",
            ]

            with self.assertRaises(RuntimeError) as ctx:
                claude_gate_review.main()
            self.assertIn("token usage", str(ctx.exception).lower())
        finally:
            os.environ.pop("GITHUB_OUTPUT", None)
            os.environ.pop("CLAUDE_GATE_COMMENT_PATH", None)
            os.environ.pop("CLAUDE_GATE_AUDIT_PATH", None)
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            if os.path.exists(output_path):
                os.unlink(output_path)
            if os.path.exists(comment_path):
                os.unlink(comment_path)
            if os.path.exists(audit_path):
                os.unlink(audit_path)

    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_raises_when_usage_zero(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json
    ):
        """Test that zero token usage raises an error."""
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "gate:claude"}, {"name": "risk:R2"}],
        }
        mock_fetch_files.return_value = []
        mock_fetch_raw.return_value = b"diff content"
        mock_anthropic.return_value = (
            {
                "id": "msg_test123",
                "model": "claude-opus-4-5-20251101",
                "content": [{"type": "text", "text": "VERDICT: PASS\nFINDINGS:\n- No issues."}],
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
            "req_test123",
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            comment_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            audit_path = f.name

        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["CLAUDE_GATE_COMMENT_PATH"] = comment_path
            os.environ["CLAUDE_GATE_AUDIT_PATH"] = audit_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ["ANTHROPIC_API_KEY"] = "fake-key"

            sys.argv = [
                "claude_gate_review.py",
                "--repo",
                "test/repo",
                "--pr-number",
                "123",
            ]

            with self.assertRaises(RuntimeError) as ctx:
                claude_gate_review.main()
            self.assertIn("token usage", str(ctx.exception).lower())
        finally:
            os.environ.pop("GITHUB_OUTPUT", None)
            os.environ.pop("CLAUDE_GATE_COMMENT_PATH", None)
            os.environ.pop("CLAUDE_GATE_AUDIT_PATH", None)
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            if os.path.exists(output_path):
                os.unlink(output_path)
            if os.path.exists(comment_path):
                os.unlink(comment_path)
            if os.path.exists(audit_path):
                os.unlink(audit_path)

    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_warns_on_response_model_mismatch(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json
    ):
        """Test that model mismatch logs a warning and still completes."""
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "gate:claude"}, {"name": "risk:R1"}],
        }
        mock_fetch_files.return_value = []
        mock_fetch_raw.return_value = b"diff content"
        mock_anthropic.return_value = (
            {
                "id": "msg_test123",
                "model": "claude-opus-4-5-20251101",
                "content": [{"type": "text", "text": "VERDICT: PASS\nFINDINGS:\n- No issues."}],
                "usage": {"input_tokens": 100, "output_tokens": 20},
            },
            "req_test123",
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_path = f.name

        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ["ANTHROPIC_API_KEY"] = "fake-key"

            sys.argv = [
                "claude_gate_review.py",
                "--repo",
                "test/repo",
                "--pr-number",
                "123",
            ]

            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                result = claude_gate_review.main()
            self.assertEqual(result, 0)
            self.assertIn("model mismatch", captured.getvalue().lower())

            with open(output_path, "r") as f:
                content = f.read()
            self.assertIn("model_used=claude-sonnet-4-5-20250929", content)
            self.assertIn("response_model=claude-opus-4-5-20251101", content)
            self.assertIn("request_id=req_test123", content)
            self.assertIn("response_id=msg_test123", content)
        finally:
            os.environ.pop("GITHUB_OUTPUT", None)
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            if os.path.exists(output_path):
                os.unlink(output_path)


    def test_fetch_graphql_success(self):
        payload = {"data": {"repository": {"pullRequest": {"title": "PR"}}}}

        class _Response:
            def __init__(self, data):
                self._data = data

            def read(self):
                return json.dumps(self._data).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("urllib.request.urlopen", return_value=_Response(payload)):
            data = claude_gate_review._fetch_graphql("query", {"n": 1}, "token")
        self.assertEqual(data, payload["data"])

    def test_fetch_graphql_raises_on_errors(self):
        payload = {"errors": [{"message": "boom"}]}

        class _Response:
            def __init__(self, data):
                self._data = data

            def read(self):
                return json.dumps(self._data).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("urllib.request.urlopen", return_value=_Response(payload)):
            with self.assertRaises(RuntimeError):
                claude_gate_review._fetch_graphql("query", {"n": 1}, "token")

    def test_fetch_pr_metadata_fallback_uses_graphql(self):
        graphql_payload = {
            "repository": {
                "pullRequest": {
                    "title": "PR title",
                    "body": "PR body",
                    "labels": {"nodes": [{"name": "gate:claude"}]},
                }
            }
        }
        with patch.object(
            claude_gate_review,
            "_fetch_json",
            side_effect=RuntimeError("too many files changed"),
        ), patch.object(
            claude_gate_review, "_fetch_graphql", return_value=graphql_payload
        ):
            result = claude_gate_review._fetch_pr_metadata("owner/repo", 123, "token")
        self.assertEqual(result["title"], "PR title")
        self.assertEqual(result["labels"], [{"name": "gate:claude"}])

    def test_fetch_pr_metadata_reraises_other_errors(self):
        with patch.object(
            claude_gate_review, "_fetch_json", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                claude_gate_review._fetch_pr_metadata("owner/repo", 123, "token")

    def test_mode_normalization(self):
        self.assertEqual(claude_gate_review._normalize_mode("legacy"), "legacy")
        self.assertEqual(claude_gate_review._normalize_mode("SHADOW"), "shadow")
        self.assertEqual(claude_gate_review._normalize_mode("Structured"), "structured")
        self.assertEqual(claude_gate_review._normalize_mode("unknown"), "legacy")

    def test_break_glass_forces_pass(self):
        warnings = []
        verdict = claude_gate_review._apply_break_glass("FAIL", True, warnings)
        self.assertEqual(verdict, "PASS")
        self.assertTrue(any("bypass" in warning.lower() for warning in warnings))

    def test_break_glass_noop_when_pass(self):
        warnings = []
        verdict = claude_gate_review._apply_break_glass("PASS", True, warnings)
        self.assertEqual(verdict, "PASS")
        self.assertTrue(any("already pass" in warning.lower() for warning in warnings))

    def test_redact_evidence_secret(self):
        self.assertEqual(claude_gate_review._redact_evidence("api_key=123"), "[REDACTED]")

    def test_redact_evidence_empty(self):
        self.assertEqual(claude_gate_review._redact_evidence(""), "")

    def test_redact_evidence_email(self):
        self.assertEqual(
            claude_gate_review._redact_evidence("Contact me at user@example.com"),
            "[REDACTED]",
        )

    def test_redact_evidence_long_number(self):
        self.assertEqual(
            claude_gate_review._redact_evidence("order=1234567890"),
            "[REDACTED]",
        )

    def test_redact_evidence_phone(self):
        self.assertEqual(
            claude_gate_review._redact_evidence("call 415-555-1212"),
            "[REDACTED]",
        )

    def test_redact_evidence_address(self):
        self.assertEqual(
            claude_gate_review._redact_evidence("ship to 123 Main St"),
            "[REDACTED]",
        )

    def test_redact_evidence_truncates(self):
        long_text = "a" * 250
        redacted = claude_gate_review._redact_evidence(long_text)
        self.assertTrue(redacted.endswith("[TRUNCATED]"))

    def test_redact_evidence_no_false_positive(self):
        self.assertEqual(claude_gate_review._redact_evidence("timeout=None"), "timeout=None")

    def test_summarize_parse_error_redacts(self):
        snippet, length = claude_gate_review._summarize_parse_error("user@example.com")
        self.assertEqual(snippet, "[REDACTED]")
        self.assertEqual(length, len("user@example.com"))

    def test_summarize_parse_error_empty(self):
        snippet, length = claude_gate_review._summarize_parse_error("")
        self.assertEqual(snippet, "")
        self.assertEqual(length, 0)

    def test_summarize_parse_error_whitespace(self):
        snippet, length = claude_gate_review._summarize_parse_error("   \n\t  ")
        self.assertEqual(snippet, "")
        self.assertEqual(length, len("   \n\t  "))

    def test_format_parse_error_includes_length(self):
        message = claude_gate_review._format_parse_error("Invalid JSON: oops.", "abc")
        self.assertIn("len=3", message)

    def test_format_parse_error_empty_snippet(self):
        message = claude_gate_review._format_parse_error("Invalid JSON: oops.", "")
        self.assertIn("len=0", message)

    def test_stable_finding_id_uses_raw_evidence(self):
        finding = {
            "category": "security",
            "title": "Leaked secret",
            "summary": "Secret in diff",
            "file": "app.py",
            "evidence": "[REDACTED]",
        }
        id_one = claude_gate_review._stable_finding_id(finding, "api_key=123")
        id_two = claude_gate_review._stable_finding_id(finding, "password=456")
        self.assertNotEqual(id_one, id_two)

    def test_parse_structured_output_finding_id_uses_raw_evidence(self):
        payload_one = {
            "version": "1.0",
            "verdict": "FAIL",
            "risk": "risk:R3",
            "reviewers": [
                {
                    "name": "primary",
                    "model": "claude-opus-4-5-20251101",
                    "findings": [
                        {
                            "category": "security",
                            "severity": 3,
                            "confidence": 80,
                            "title": "Secret",
                            "summary": "Secret in diff",
                            "file": "app.py",
                            "evidence": "api_key=123",
                            "suggested_test": "Add secret scan",
                        }
                    ],
                }
            ],
        }
        payload_two = json.loads(json.dumps(payload_one))
        payload_two["reviewers"][0]["findings"][0]["evidence"] = "password=456"
        diff_text = "api_key=123\npassword=456"
        _, findings_one, _ = claude_gate_review._parse_structured_output(
            json.dumps(payload_one), diff_text
        )
        _, findings_two, _ = claude_gate_review._parse_structured_output(
            json.dumps(payload_two), diff_text
        )
        self.assertEqual(findings_one[0]["evidence"], "[REDACTED]")
        self.assertEqual(findings_two[0]["evidence"], "[REDACTED]")
        self.assertNotEqual(findings_one[0]["finding_id"], findings_two[0]["finding_id"])

    def test_default_model_mapping_locked(self):
        expected = {
            "risk:R0": "claude-haiku-4-5-20251001",
            "risk:R1": "claude-sonnet-4-5-20250929",
            "risk:R2": "claude-opus-4-5-20251101",
            "risk:R3": "claude-opus-4-5-20251101",
            "risk:R4": "claude-opus-4-5-20251101",
        }
        self.assertEqual(claude_gate_review._DEFAULT_MODELS, expected)

    def test_action_required_classification(self):
        finding = {"severity": 3, "confidence": 70, "file": "a.py", "evidence": "line"}
        self.assertTrue(claude_gate_review._is_action_required(finding))
        finding["confidence"] = 60
        self.assertFalse(claude_gate_review._is_action_required(finding))

    def test_normalize_verdict(self):
        self.assertEqual(claude_gate_review._normalize_verdict("PASS"), "PASS")
        self.assertEqual(claude_gate_review._normalize_verdict("fail"), "FAIL")
        self.assertEqual(claude_gate_review._normalize_verdict("unknown"), "FAIL")

    def test_format_mode_label(self):
        self.assertEqual(claude_gate_review._format_mode_label("shadow"), "SHADOW")
        self.assertEqual(claude_gate_review._format_mode_label("invalid"), "LEGACY")

    def test_structured_parse_failure_payload(self):
        payload = claude_gate_review._structured_parse_failure_payload(["oops"], "raw")
        self.assertEqual(payload["errors"], ["oops"])
        self.assertEqual(payload["verdict"], "FAIL")

    def test_structured_parse_failure_payload_empty_raw(self):
        payload = claude_gate_review._structured_parse_failure_payload(["oops"], "")
        self.assertEqual(payload["raw_length"], 0)
        self.assertNotIn("raw", payload)

    def test_step_summary_written(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as summary_file:
            summary_path = summary_file.name
        os.environ["GITHUB_STEP_SUMMARY"] = summary_path
        try:
            summary = claude_gate_review._build_step_summary(
                mode_label="STRUCTURED",
                verdict="PASS",
                bypass=False,
                action_required_count=0,
                warnings=["note"],
                mode="structured",
                risk="risk:R2",
                model_used="claude-opus-4-5-20251101",
                request_id="req_123",
                response_id="msg_123",
            )
            claude_gate_review._write_step_summary(summary)
            with open(summary_path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("Claude gate mode: structured", content)
            self.assertIn("Mode: STRUCTURED", content)
            self.assertIn("Risk label: risk:R2", content)
            self.assertIn("Model used: claude-opus-4-5-20251101", content)
            self.assertIn("Anthropic Request ID: req_123", content)
            self.assertIn("Anthropic Response ID: msg_123", content)
            self.assertIn("Warning: note", content)
        finally:
            os.environ.pop("GITHUB_STEP_SUMMARY", None)
            if os.path.exists(summary_path):
                os.unlink(summary_path)

    def test_parse_structured_output_valid(self):
        raw = json.dumps(
            {
                "version": "1.0",
                "verdict": "FAIL",
                "risk": "risk:R3",
                "reviewers": [
                    {
                        "name": "primary",
                        "model": "claude-opus-4-5-20251101",
                        "findings": [
                            {
                                "finding_id": "abc123",
                                "category": "reliability",
                                "severity": 4,
                                "confidence": 85,
                                "title": "Timeout disabled",
                                "summary": "Outbound timeout is None",
                                "file": "app.py",
                                "evidence": "send_request(data, timeout=None)",
                                "suggested_test": "Add a timeout test",
                            }
                        ],
                    }
                ],
            }
        )
        payload, findings, errors = claude_gate_review._parse_structured_output(
            raw, "send_request(data, timeout=None)"
        )
        self.assertFalse(errors)
        self.assertEqual(payload["verdict"], "FAIL")
        self.assertEqual(len(findings), 1)

    def test_parse_structured_output_invalid_json(self):
        payload, findings, errors = claude_gate_review._parse_structured_output("{", "")
        self.assertTrue(errors)
        self.assertEqual(findings, [])
        self.assertEqual(payload, {})
        self.assertTrue(any("len=" in error for error in errors))

    def test_parse_structured_output_non_dict_payload(self):
        payload, findings, errors = claude_gate_review._parse_structured_output("42", "")
        self.assertEqual(payload, 42)
        self.assertEqual(findings, [])
        self.assertTrue(any("JSON object" in error for error in errors))

    def test_parse_structured_output_missing_reviewers_reports_all(self):
        raw = json.dumps({"version": "0.9", "verdict": "MAYBE"})
        _, _, errors = claude_gate_review._parse_structured_output(raw, "")
        self.assertTrue(any("version" in error.lower() for error in errors))
        self.assertTrue(any("verdict" in error.lower() for error in errors))
        self.assertTrue(any("reviewers" in error.lower() for error in errors))

    def test_parse_structured_output_findings_not_list(self):
        raw = json.dumps(
            {
                "version": "1.0",
                "verdict": "PASS",
                "risk": "risk:R1",
                "reviewers": [{"name": "primary", "model": "claude-opus-4-5-20251101", "findings": 42}],
            }
        )
        _, _, errors = claude_gate_review._parse_structured_output(raw, "")
        self.assertTrue(any("Findings must be a list" in error for error in errors))

    def test_parse_structured_output_summary_none(self):
        raw = json.dumps(
            {
                "version": "1.0",
                "verdict": "PASS",
                "risk": "risk:R1",
                "reviewers": [
                    {
                        "name": "primary",
                        "model": "claude-opus-4-5-20251101",
                        "findings": [
                            {
                                "finding_id": "abc",
                                "category": "tests",
                                "severity": 1,
                                "confidence": 50,
                                "title": None,
                                "summary": None,
                                "file": "",
                                "evidence": "",
                            }
                        ],
                    }
                ],
            }
        )
        _, findings, errors = claude_gate_review._parse_structured_output(raw, "")
        self.assertTrue(any("title must be a string" in error.lower() for error in errors))
        self.assertTrue(any("summary must be a string" in error.lower() for error in errors))
        self.assertEqual(findings[0]["title"], "")
        self.assertEqual(findings[0]["summary"], "")
    def test_parse_structured_output_missing_evidence(self):
        raw = json.dumps(
            {
                "version": "1.0",
                "verdict": "FAIL",
                "risk": "risk:R3",
                "reviewers": [
                    {
                        "name": "primary",
                        "model": "claude-opus-4-5-20251101",
                        "findings": [
                            {
                                "finding_id": "abc123",
                                "category": "reliability",
                                "severity": 3,
                                "confidence": 80,
                                "title": "Missing evidence",
                                "summary": "No evidence",
                                "file": "app.py",
                                "evidence": "",
                            }
                        ],
                    }
                ],
            }
        )
        _, _, errors = claude_gate_review._parse_structured_output(raw, "")
        self.assertTrue(any("Severity >= 3 requires file and evidence" in error for error in errors))

    def test_invalid_structured_json_blocks_in_structured_mode(self):
        bundle = claude_gate_review._load_fixture_bundle("legacy_small")
        bundle["structured_response"] = "{"
        os.environ["CLAUDE_REVIEW_MODE"] = "structured"
        try:
            argv = ["claude_gate_review.py", "--dry-run", "--fixture", "legacy_small"]
            with patch("claude_gate_review._load_fixture_bundle", return_value=bundle):
                captured = io.StringIO()
                with contextlib.redirect_stdout(captured):
                    with patch.object(sys, "argv", argv):
                        result = claude_gate_review.main()
            self.assertEqual(result, 0)
            self.assertIn("CLAUDE_REVIEW: PASS", captured.getvalue())
            self.assertIn("Structured output parse failure", captured.getvalue())
        finally:
            os.environ.pop("CLAUDE_REVIEW_MODE", None)

    def test_invalid_structured_json_does_not_block_shadow_mode(self):
        bundle = claude_gate_review._load_fixture_bundle("legacy_small")
        bundle["structured_response"] = "{"
        os.environ["CLAUDE_REVIEW_MODE"] = "shadow"
        try:
            argv = ["claude_gate_review.py", "--dry-run", "--fixture", "legacy_small"]
            with patch("claude_gate_review._load_fixture_bundle", return_value=bundle):
                captured = io.StringIO()
                with contextlib.redirect_stdout(captured):
                    with patch.object(sys, "argv", argv):
                        result = claude_gate_review.main()
            self.assertEqual(result, 0)
            self.assertIn("CLAUDE_REVIEW: PASS", captured.getvalue())
            self.assertIn("Structured output parse failure", captured.getvalue())
        finally:
            os.environ.pop("CLAUDE_REVIEW_MODE", None)

    def test_dry_run_does_not_call_network(self):
        with patch("claude_gate_review._fetch_json") as mock_fetch, patch(
            "claude_gate_review._anthropic_request"
        ) as mock_anthropic:
            argv = [
                "claude_gate_review.py",
                "--dry-run",
                "--fixture",
                "legacy_small",
            ]
            with patch.object(sys, "argv", argv):
                result = claude_gate_review.main()
            self.assertEqual(result, 0)
            mock_fetch.assert_not_called()
            mock_anthropic.assert_not_called()

    def test_golden_legacy_output_matches(self):
        golden_path = Path(__file__).resolve().parents[1] / "13_GOLDEN_LEGACY_OUTPUT.md"
        text = golden_path.read_text(encoding="utf-8")
        marker = "### A2) Example *PR comment body* (what the script posts)"
        block_start = text.index(marker)
        block_start = text.index("```text", block_start) + len("```text")
        block_end = text.index("```", block_start)
        expected = text[block_start:block_end].strip("\n") + "\n"
        comment = claude_gate_review._format_comment(
            verdict="PASS",
            risk="risk:R2",
            model="claude-opus-4-5-20251101",
            findings=["No issues found."],
            response_id="msg_0123456789abcdef",
            request_id="req_0123456789abcdef",
            usage={"input_tokens": 21814, "output_tokens": 18},
            mode_label="LEGACY",
            response_model="claude-opus-4-5-20251101",
        )
        self.assertEqual(comment, expected)

    @patch("claude_gate_review._fetch_issue_comments", return_value=[])
    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_structured_mode_end_to_end(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json, _mock_fetch_comments
    ):
        structured_payload = {
            "version": "1.0",
            "verdict": "FAIL",
            "risk": "risk:R3",
            "reviewers": [
                {
                    "name": "primary",
                    "model": "claude-opus-4-5-20251101",
                    "findings": [
                        {
                            "finding_id": "abc123",
                            "category": "reliability",
                            "severity": 3,
                            "confidence": 80,
                            "title": "Timeout missing",
                            "summary": "Outbound timeout is None",
                            "file": "app.py",
                            "evidence": "send_request(data, timeout=None)",
                            "suggested_test": "Add timeout test",
                        }
                    ],
                }
            ],
        }
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Body",
            "labels": [{"name": "gate:claude"}, {"name": "risk:R3"}],
        }
        mock_fetch_files.return_value = [
            {"filename": "backend/src/orders.py", "status": "modified", "additions": 1, "deletions": 0}
        ]
        mock_fetch_raw.return_value = b"send_request(data, timeout=None)"
        mock_anthropic.return_value = (
            {
                "id": "msg_structured",
                "model": "claude-opus-4-5-20251101",
                "content": [{"type": "text", "text": json.dumps(structured_payload)}],
                "usage": {"input_tokens": 100, "output_tokens": 20},
            },
            "req_structured",
        )
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as output_file:
            output_path = output_file.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as comment_file:
            comment_path = comment_file.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as audit_file:
            audit_path = audit_file.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as summary_file:
            summary_path = summary_file.name
        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["CLAUDE_GATE_COMMENT_PATH"] = comment_path
            os.environ["CLAUDE_GATE_AUDIT_PATH"] = audit_path
            os.environ["GITHUB_STEP_SUMMARY"] = summary_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ["ANTHROPIC_API_KEY"] = "fake-key"
            os.environ["CLAUDE_REVIEW_MODE"] = "structured"
            sys.argv = [
                "claude_gate_review.py",
                "--repo",
                "test/repo",
                "--pr-number",
                "123",
            ]
            result = claude_gate_review.main()
            self.assertEqual(result, 0)
            with open(comment_path, "r", encoding="utf-8") as handle:
                comment_body = handle.read()
            self.assertIn("Mode: STRUCTURED", comment_body)
            self.assertIn("CLAUDE_REVIEW: PASS", comment_body)
            self.assertIn("Action Required", comment_body)
            self.assertIn("Structured JSON", comment_body)
            self.assertIn("Lenses applied:", comment_body)
            self.assertIn("ORDER_STATUS_SAFETY", comment_body)
            self.assertIn(claude_gate_review.STATE_MARKER, comment_body)
        finally:
            for var in (
                "GITHUB_OUTPUT",
                "CLAUDE_GATE_COMMENT_PATH",
                "CLAUDE_GATE_AUDIT_PATH",
                "GITHUB_STEP_SUMMARY",
                "GITHUB_TOKEN",
                "ANTHROPIC_API_KEY",
                "CLAUDE_REVIEW_MODE",
            ):
                os.environ.pop(var, None)
            for path in (output_path, comment_path, audit_path, summary_path):
                if os.path.exists(path):
                    os.unlink(path)

    @patch("claude_gate_review._fetch_issue_comments", return_value=[])
    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_shadow_mode_non_blocking(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json, _mock_fetch_comments
    ):
        structured_payload = {
            "version": "1.0",
            "verdict": "FAIL",
            "risk": "risk:R2",
            "reviewers": [
                {
                    "name": "primary",
                    "model": "claude-opus-4-5-20251101",
                    "findings": [],
                }
            ],
        }
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Body",
            "labels": [{"name": "gate:claude"}, {"name": "risk:R2"}],
        }
        mock_fetch_files.return_value = []
        mock_fetch_raw.return_value = b"diff content"
        mock_anthropic.return_value = (
            {
                "id": "msg_shadow",
                "model": "claude-opus-4-5-20251101",
                "content": [{"type": "text", "text": json.dumps(structured_payload)}],
                "usage": {"input_tokens": 50, "output_tokens": 10},
            },
            "req_shadow",
        )
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as output_file:
            output_path = output_file.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as comment_file:
            comment_path = comment_file.name
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as audit_file:
            audit_path = audit_file.name
        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["CLAUDE_GATE_COMMENT_PATH"] = comment_path
            os.environ["CLAUDE_GATE_AUDIT_PATH"] = audit_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ["ANTHROPIC_API_KEY"] = "fake-key"
            os.environ["CLAUDE_REVIEW_MODE"] = "shadow"
            sys.argv = [
                "claude_gate_review.py",
                "--repo",
                "test/repo",
                "--pr-number",
                "123",
            ]
            result = claude_gate_review.main()
            self.assertEqual(result, 0)
            with open(output_path, "r", encoding="utf-8") as handle:
                output = handle.read()
            self.assertIn("verdict=PASS", output)
        finally:
            for var in (
                "GITHUB_OUTPUT",
                "CLAUDE_GATE_COMMENT_PATH",
                "CLAUDE_GATE_AUDIT_PATH",
                "GITHUB_TOKEN",
                "ANTHROPIC_API_KEY",
                "CLAUDE_REVIEW_MODE",
            ):
                os.environ.pop(var, None)
            for path in (output_path, comment_path, audit_path):
                if os.path.exists(path):
                    os.unlink(path)

    def test_format_structured_comment_no_duplicate_summary(self):
        comment = claude_gate_review._format_structured_comment(
            verdict="PASS",
            risk="risk:R1",
            model="claude-opus-4-5-20251101",
            action_required=[
                {
                    "severity": 2,
                    "confidence": 60,
                    "points": 2,
                    "title": "",
                    "summary": "Timeout missing",
                    "file": "app.py",
                }
            ],
            fyi=[],
            payload={"version": "1.0", "reviewers": [], "verdict": "PASS"},
            response_model="claude-opus-4-5-20251101",
            response_id="msg_test",
            request_id="req_test",
            usage={"input_tokens": 1, "output_tokens": 1},
            mode_label="STRUCTURED",
            bypass=False,
            warnings=None,
            summary={
                "action_required_count": 1,
                "total_points": 2,
                "highest_severity_action_required": 2,
            },
            state_payload={"version": 1, "run_index": 1, "findings": {}},
            lens_names=[],
        )
        self.assertIn("Timeout missing (app.py)", comment)
        self.assertNotIn("Timeout missing: Timeout missing", comment)
