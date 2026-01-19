#!/usr/bin/env python3
"""Unit tests for claude_gate_review.py"""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

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
        self.assertEqual(model, "claude-haiku-4-5-20251015")

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

    def test_format_comment_with_response_id(self):
        """Test comment formatting includes response ID."""
        comment = claude_gate_review._format_comment(
            verdict="PASS",
            risk="risk:R2",
            model="claude-opus-4-5-20251101",
            findings=["No issues found."],
            response_id="msg_abc123xyz",
            usage={"input_tokens": 1000, "output_tokens": 200},
        )
        self.assertIn("CLAUDE_REVIEW: PASS", comment)
        self.assertIn("Risk: risk:R2", comment)
        self.assertIn("Model: claude-opus-4-5-20251101", comment)
        self.assertIn("Anthropic Response ID: msg_abc123xyz", comment)
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
        self.assertIn("CLAUDE_REVIEW: FAIL", comment)
        self.assertIn("Risk: risk:R1", comment)
        self.assertIn("Model: claude-sonnet-4-5-20250929", comment)
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

    def test_build_prompt(self):
        """Test prompt building includes all required sections."""
        prompt = claude_gate_review._build_prompt(
            title="Test PR",
            body="This is a test",
            risk="risk:R2",
            files_summary="- file1.py (modified, +10 -5)",
            diff_text="diff content here",
        )
        self.assertIn("PR TITLE (untrusted input):", prompt)
        self.assertIn("Test PR", prompt)
        self.assertIn("PR BODY (untrusted input):", prompt)
        self.assertIn("This is a test", prompt)
        self.assertIn("RISK LABEL: risk:R2", prompt)
        self.assertIn("CHANGED FILES:", prompt)
        self.assertIn("- file1.py (modified, +10 -5)", prompt)
        self.assertIn("UNIFIED DIFF (untrusted input):", prompt)
        self.assertIn("diff content here", prompt)

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
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = claude_gate_review._anthropic_request(
            {"model": "claude-haiku-4-5-20251015", "messages": []},
            "test-api-key"
        )
        
        self.assertEqual(result["id"], "msg_test123")
        self.assertIn("content", result)
        self.assertIn("usage", result)

    @patch("claude_gate_review._fetch_json")
    @patch("claude_gate_review._fetch_all_files")
    @patch("claude_gate_review._fetch_raw")
    @patch("claude_gate_review._anthropic_request")
    def test_main_skip_without_gate_label(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json
    ):
        """Test that script skips when gate:claude label is missing."""
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
            # Don't set ANTHROPIC_API_KEY to prove we skip before checking it
            
            sys.argv = [
                "claude_gate_review.py",
                "--repo", "test/repo",
                "--pr-number", "123",
            ]
            
            result = claude_gate_review.main()
            self.assertEqual(result, 0)
            
            # Verify skip=true was written
            with open(output_path, "r") as f:
                content = f.read()
            self.assertIn("skip=true", content)
            
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
    def test_main_runs_when_forced_even_without_label(
        self, mock_anthropic, mock_fetch_raw, mock_fetch_files, mock_fetch_json
    ):
        """Test that script runs when CLAUDE_GATE_FORCE=true even if label not in API response."""
        # Mock PR data WITHOUT gate:claude label (race condition scenario)
        mock_fetch_json.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "risk:R1"}],  # No gate:claude
        }
        mock_fetch_files.return_value = []
        mock_fetch_raw.return_value = b"diff content"
        mock_anthropic.return_value = {
            "id": "msg_test123",
            "content": [{"type": "text", "text": "VERDICT: PASS\nFINDINGS:\n- No issues."}],
            "usage": {"input_tokens": 100, "output_tokens": 20},
        }
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_path = f.name
        
        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            os.environ["GITHUB_TOKEN"] = "fake-token"
            os.environ["ANTHROPIC_API_KEY"] = "fake-key"
            os.environ["CLAUDE_GATE_FORCE"] = "true"
            
            sys.argv = [
                "claude_gate_review.py",
                "--repo", "test/repo",
                "--pr-number", "123",
            ]
            
            result = claude_gate_review.main()
            self.assertEqual(result, 0)
            
            # Verify it did NOT skip
            with open(output_path, "r") as f:
                content = f.read()
            self.assertIn("skip=false", content)
            self.assertIn("verdict=PASS", content)
            
            # Verify Anthropic was called despite missing label
            mock_anthropic.assert_called_once()
        finally:
            os.environ.pop("GITHUB_OUTPUT", None)
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("CLAUDE_GATE_FORCE", None)
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == "__main__":
    unittest.main()
