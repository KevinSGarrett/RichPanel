#!/usr/bin/env python3
"""
Integration tests for Claude Gate fail-closed behavior.

These tests intentionally trigger failure conditions to prove
the gate fails closed as expected. Each test runs the actual
claude_gate_review.py script with manipulated conditions.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, main


_STUB_SITECUSTOMIZE = """
import json
import os
import urllib.request


class _StubResponse:
    def __init__(self, status, body, headers=None):
        self._status = status
        self._body = body
        self.headers = headers or {}

    def read(self):
        return self._body

    def getcode(self):
        return self._status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _as_bytes(value):
    if isinstance(value, bytes):
        return value
    return str(value).encode("utf-8")


def _stub_urlopen(request, timeout=60):
    url = request.full_url if hasattr(request, "full_url") else request
    headers = {}
    try:
        headers = {k.lower(): v for k, v in request.headers.items()}
    except Exception:
        headers = {}
    accept = headers.get("accept", "")
    scenario = os.environ.get("CLAUDE_GATE_TEST_SCENARIO", "")

    def _pr_payload():
        labels = [{"name": "risk:R2"}]
        if scenario != "missing_gate_label":
            labels.append({"name": "gate:claude"})
        return {
            "title": "Test PR",
            "body": "Test body",
            "labels": labels,
        }

    if url.startswith("https://api.github.com/repos/test/repo/pulls/1/files"):
        return _StubResponse(200, b"[]")

    if url.startswith("https://api.github.com/repos/test/repo/pulls/1"):
        if "application/vnd.github.v3.diff" in accept:
            return _StubResponse(200, b"diff --git a/a b/a\\n")
        return _StubResponse(200, _as_bytes(json.dumps(_pr_payload())))

    if url == "https://api.anthropic.com/v1/messages":
        if scenario in ("invalid_api_key", "http_500"):
            return _StubResponse(401, b"unauthorized", headers={"request-id": "req_test"})
        if scenario == "missing_response_id":
            body = {
                "model": "claude-opus-4-5",
                "content": [{"type": "text", "text": "VERDICT: PASS\\nFINDINGS:\\n- No issues."}],
                "usage": {"input_tokens": 100, "output_tokens": 20},
            }
            return _StubResponse(200, _as_bytes(json.dumps(body)), headers={"request-id": "req_test"})
        if scenario == "missing_request_id":
            body = {
                "id": "msg_test",
                "model": "claude-opus-4-5",
                "content": [{"type": "text", "text": "VERDICT: PASS\\nFINDINGS:\\n- No issues."}],
                "usage": {"input_tokens": 100, "output_tokens": 20},
            }
            return _StubResponse(200, _as_bytes(json.dumps(body)), headers={})
        if scenario == "zero_usage":
            body = {
                "id": "msg_test",
                "model": "claude-opus-4-5",
                "content": [{"type": "text", "text": "VERDICT: PASS\\nFINDINGS:\\n- No issues."}],
                "usage": {"input_tokens": 0, "output_tokens": 0},
            }
            return _StubResponse(200, _as_bytes(json.dumps(body)), headers={"request-id": "req_test"})
        body = {
            "id": "msg_test",
            "model": "claude-opus-4-5",
            "content": [{"type": "text", "text": "VERDICT: PASS\\nFINDINGS:\\n- No issues."}],
            "usage": {"input_tokens": 100, "output_tokens": 20},
        }
        return _StubResponse(200, _as_bytes(json.dumps(body)), headers={"request-id": "req_test"})

    raise RuntimeError(f"Unexpected URL in stub: {url}")


urllib.request.urlopen = _stub_urlopen
"""


def _run_gate(scenario: str, *, api_key: str | None) -> subprocess.CompletedProcess[str]:
    """Run claude_gate_review.py in a subprocess with a stubbed network layer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sitecustomize_path = Path(tmpdir) / "sitecustomize.py"
        sitecustomize_path.write_text(_STUB_SITECUSTOMIZE, encoding="utf-8")

        script_path = (
            Path(__file__).resolve().parents[1] / "scripts" / "claude_gate_review.py"
        )
        if not script_path.exists():
            raise AssertionError(f"Missing claude_gate_review.py at {script_path}")

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{tmpdir}{os.pathsep}{env.get('PYTHONPATH', '')}"
        env["GITHUB_TOKEN"] = "test-token"
        env["CLAUDE_GATE_TEST_SCENARIO"] = scenario
        if api_key is None:
            env.pop("ANTHROPIC_API_KEY", None)
        else:
            env["ANTHROPIC_API_KEY"] = api_key

        return subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--repo",
                "test/repo",
                "--pr-number",
                "1",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )


class ClaudeGateNegativeTests(TestCase):
    """Test fail-closed behavior with real script execution."""

    def test_missing_api_key_fails(self):
        """Gate should fail when ANTHROPIC_API_KEY is missing."""
        result = _run_gate("missing_api_key", api_key=None)
        self.assertEqual(result.returncode, 2)
        self.assertIn("ANTHROPIC_API_KEY", result.stderr)

    def test_invalid_api_key_fails(self):
        """Gate should fail with invalid API key."""
        result = _run_gate("invalid_api_key", api_key="invalid-key")
        self.assertEqual(result.returncode, 1)

    def test_missing_gate_label_fails(self):
        """Workflow should fail when gate:claude label is missing."""
        result = _run_gate("missing_gate_label", api_key="valid-key")
        self.assertEqual(result.returncode, 1)
        self.assertIn("gate:claude", result.stderr)

    def test_http_500_fails(self):
        """Gate should fail on Anthropic HTTP 500 response."""
        result = _run_gate("http_500", api_key="valid-key")
        self.assertEqual(result.returncode, 1)

    def test_missing_response_id_fails(self):
        """Gate should fail when response id is missing."""
        result = _run_gate("missing_response_id", api_key="valid-key")
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing id", result.stderr.lower())

    def test_missing_request_id_fails(self):
        """Gate should fail when request id is missing."""
        result = _run_gate("missing_request_id", api_key="valid-key")
        self.assertEqual(result.returncode, 1)
        self.assertIn("request id", result.stderr.lower())

    def test_zero_usage_fails(self):
        """Gate should fail when token usage is zero."""
        result = _run_gate("zero_usage", api_key="valid-key")
        self.assertEqual(result.returncode, 1)
        self.assertIn("token usage", result.stderr.lower())


if __name__ == "__main__":
    main()
