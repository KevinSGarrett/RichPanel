#!/usr/bin/env python3
"""Unit tests for claude_gate_comments.py"""
import contextlib
import io
import json
import os
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import claude_gate_comments

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> list[dict]:
    path = FIXTURES_DIR / name
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class _StubResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self._status = status

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self._status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _StubFP:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body


class TestClaudeGateComments(unittest.TestCase):
    """Test canonical comment selection for Claude gate."""

    def test_resolve_action_without_canonical(self):
        """No canonical comments should result in create action."""
        comments = _load_fixture("pr_comments_without_canonical.json")
        action, comment_id, count = claude_gate_comments.resolve_canonical_comment_action(comments)
        self.assertEqual(action, "create")
        self.assertIsNone(comment_id)
        self.assertEqual(count, 0)

    def test_resolve_action_with_single_canonical(self):
        """Single canonical comment should result in update action."""
        comments = _load_fixture("pr_comments_with_canonical.json")
        action, comment_id, count = claude_gate_comments.resolve_canonical_comment_action(comments)
        self.assertEqual(action, "update")
        self.assertEqual(comment_id, 2001)
        self.assertEqual(count, 1)

    def test_resolve_action_with_multiple_canonical(self):
        """Multiple canonical comments should update the oldest."""
        comments = _load_fixture("pr_comments_with_multiple_canonical.json")
        action, comment_id, count = claude_gate_comments.resolve_canonical_comment_action(comments)
        self.assertEqual(action, "update")
        self.assertEqual(comment_id, 3001)
        self.assertEqual(count, 2)

    def test_parse_github_datetime(self):
        value = "2025-01-01T10:00:00Z"
        parsed = claude_gate_comments._parse_github_datetime(value)
        self.assertEqual(parsed, datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc))

    def test_parse_github_datetime_invalid(self):
        parsed = claude_gate_comments._parse_github_datetime("not-a-date")
        self.assertEqual(parsed, datetime.max.replace(tzinfo=timezone.utc))

    def test_comment_has_marker(self):
        comment = {"body": f"hello {claude_gate_comments.CANONICAL_MARKER}"}
        self.assertTrue(claude_gate_comments._comment_has_marker(comment))
        self.assertFalse(claude_gate_comments._comment_has_marker({"body": "nope"}))

    def test_canonical_sort_key_invalid_id(self):
        comment = {"created_at": "2025-01-01T00:00:00Z", "id": "not-int"}
        sort_key = claude_gate_comments._canonical_sort_key(comment)
        self.assertEqual(sort_key[1], 0)

    def test_resolve_action_missing_id_raises(self):
        comments = [{"body": claude_gate_comments.CANONICAL_MARKER, "created_at": "2025-01-01T00:00:00Z"}]
        with self.assertRaises(RuntimeError):
            claude_gate_comments.resolve_canonical_comment_action(comments)

    def test_resolve_action_skips_invalid_id(self):
        comments = [
            {
                "id": "oops",
                "body": claude_gate_comments.CANONICAL_MARKER,
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": 42,
                "body": claude_gate_comments.CANONICAL_MARKER,
                "created_at": "2025-01-02T00:00:00Z",
            },
        ]
        action, comment_id, count = claude_gate_comments.resolve_canonical_comment_action(comments)
        self.assertEqual(action, "update")
        self.assertEqual(comment_id, 42)
        self.assertEqual(count, 2)

    def test_resolve_action_all_invalid_ids(self):
        comments = [
            {
                "id": "oops",
                "body": claude_gate_comments.CANONICAL_MARKER,
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": None,
                "body": claude_gate_comments.CANONICAL_MARKER,
                "created_at": "2025-01-02T00:00:00Z",
            },
        ]
        with self.assertRaises(RuntimeError):
            claude_gate_comments.resolve_canonical_comment_action(comments)

    @patch("claude_gate_comments.urllib.request.urlopen")
    def test_github_request_success(self, mock_urlopen):
        mock_urlopen.return_value = _StubResponse(b'{"ok": true}', status=200)
        data = claude_gate_comments._github_request("https://example.com", "token")
        self.assertEqual(data, b'{"ok": true}')

    @patch("claude_gate_comments.urllib.request.urlopen")
    def test_github_request_http_error(self, mock_urlopen):
        error = urllib.error.HTTPError(
            "https://example.com",
            500,
            "err",
            None,
            _StubFP(b"boom"),
        )
        mock_urlopen.side_effect = error
        with self.assertRaises(RuntimeError) as ctx:
            claude_gate_comments._github_request("https://example.com", "token")
        self.assertIn("GitHub API error 500", str(ctx.exception))

    @patch("claude_gate_comments.urllib.request.urlopen")
    def test_github_request_url_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("down")
        with self.assertRaises(RuntimeError) as ctx:
            claude_gate_comments._github_request("https://example.com", "token")
        self.assertIn("request failed", str(ctx.exception))

    @patch("claude_gate_comments._github_request")
    def test_github_request_json_invalid(self, mock_request):
        mock_request.return_value = b"{"
        with self.assertRaises(RuntimeError) as ctx:
            claude_gate_comments._github_request_json("https://example.com", "token")
        self.assertIn("invalid JSON", str(ctx.exception))

    @patch("claude_gate_comments._github_request_json")
    def test_list_issue_comments_pagination(self, mock_request_json):
        first_page = [{"id": idx} for idx in range(100)]
        second_page = [{"id": 101}]
        mock_request_json.side_effect = [first_page, second_page]
        comments = claude_gate_comments._list_issue_comments("repo", 123, "token")
        self.assertEqual(len(comments), 101)

    @patch("claude_gate_comments._github_request_json")
    def test_list_issue_comments_invalid_payload(self, mock_request_json):
        mock_request_json.return_value = {"id": 1}
        with self.assertRaises(RuntimeError):
            claude_gate_comments._list_issue_comments("repo", 123, "token")

    @patch("claude_gate_comments._github_request_json")
    def test_create_issue_comment_invalid_response(self, mock_request_json):
        mock_request_json.return_value = []
        with self.assertRaises(RuntimeError):
            claude_gate_comments._create_issue_comment("repo", 123, "token", "body")

    @patch("claude_gate_comments._github_request_json")
    def test_update_issue_comment_invalid_response(self, mock_request_json):
        mock_request_json.return_value = []
        with self.assertRaises(RuntimeError):
            claude_gate_comments._update_issue_comment("repo", 123, "token", "body")

    @patch("claude_gate_comments._create_issue_comment")
    @patch("claude_gate_comments._list_issue_comments")
    def test_upsert_comment_create_adds_marker(self, mock_list, mock_create):
        mock_list.return_value = []
        captured = {}

        def _capture(repo, pr, token, body):
            captured["body"] = body
            return {"id": 1, "html_url": "https://example.com/comment/1"}

        mock_create.side_effect = _capture
        result = claude_gate_comments.upsert_canonical_comment("repo", 1, "token", "body")
        self.assertEqual(result["action"], "create")
        self.assertIn(claude_gate_comments.CANONICAL_MARKER, captured["body"])

    @patch("claude_gate_comments._update_issue_comment")
    @patch("claude_gate_comments._list_issue_comments")
    def test_upsert_comment_update_with_duplicates(self, mock_list, mock_update):
        comments = _load_fixture("pr_comments_with_multiple_canonical.json")
        mock_list.return_value = comments
        mock_update.return_value = {"id": 3001, "html_url": "https://example.com/comment/3001"}
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = claude_gate_comments.upsert_canonical_comment("repo", 1, "token", "body")
        self.assertEqual(result["action"], "update")
        self.assertEqual(mock_update.call_args[0][1], 3001)
        self.assertIn("Found 2 canonical comments", stderr.getvalue())

    def test_main_missing_token(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as handle:
            comment_path = handle.name
        try:
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("GH_TOKEN", None)
            argv = [
                "claude_gate_comments.py",
                "--repo",
                "repo",
                "--pr-number",
                "1",
                "--comment-path",
                comment_path,
            ]
            with patch.object(os, "environ", dict(os.environ)):
                with patch("sys.argv", argv):
                    result = claude_gate_comments.main()
            self.assertEqual(result, 2)
        finally:
            os.unlink(comment_path)

    def test_main_missing_comment_file(self):
        os.environ["GITHUB_TOKEN"] = "token"
        try:
            argv = [
                "claude_gate_comments.py",
                "--repo",
                "repo",
                "--pr-number",
                "1",
                "--comment-path",
                "missing.txt",
            ]
            with patch("sys.argv", argv):
                result = claude_gate_comments.main()
            self.assertEqual(result, 2)
        finally:
            os.environ.pop("GITHUB_TOKEN", None)

    @patch("claude_gate_comments.upsert_canonical_comment")
    def test_main_success(self, mock_upsert):
        mock_upsert.return_value = {"action": "update", "comment_id": 1, "comment_url": "url"}
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as handle:
            handle.write("body")
            comment_path = handle.name
        os.environ["GITHUB_TOKEN"] = "token"
        try:
            argv = [
                "claude_gate_comments.py",
                "--repo",
                "repo",
                "--pr-number",
                "1",
                "--comment-path",
                comment_path,
            ]
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with patch("sys.argv", argv):
                    result = claude_gate_comments.main()
            self.assertEqual(result, 0)
            self.assertIn("Claude review comment update", stdout.getvalue())
        finally:
            os.environ.pop("GITHUB_TOKEN", None)
            os.unlink(comment_path)
