#!/usr/bin/env python3
"""
Unit tests for the B62 sandbox golden path wrapper helpers.
"""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b62_sandbox_golden_path import (  # type: ignore  # noqa: E402
    main,
    _ensure_parent,
    _extract_ticket_ref,
    _git_diffstat,
    _iso_timestamp,
    _proof_excerpt,
    _run_command,
    _read_proof,
    _redact_command,
    _write_changes,
    _write_evidence,
    _write_run_report,
)


class RedactionTests(unittest.TestCase):
    def test_redact_command_masks_sensitive_flags(self) -> None:
        cmd = [
            "python",
            "scripts/b62_sandbox_golden_path.py",
            "--ticket-number",
            "12345",
            "--allowlist-email",
            "test.user@example.com",
            "--order-number",
            "98765",
            "--ticket-id",
            "conv-abc",
        ]
        redacted = _redact_command(cmd)
        self.assertNotIn("12345", redacted)
        self.assertNotIn("test.user@example.com", redacted)
        self.assertNotIn("98765", redacted)
        self.assertNotIn("conv-abc", redacted)
        self.assertIn("<redacted>", redacted)
        redacted = _redact_command(
            ["python", "scripts/b62_sandbox_golden_path.py", "--ticket-id=conv-xyz"]
        )
        self.assertIn("--ticket-id=<redacted>", redacted)


class HelperTests(unittest.TestCase):
    def test_iso_timestamp_and_ensure_parent(self) -> None:
        stamp = _iso_timestamp()
        self.assertIn("T", stamp)
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "nested" / "file.txt"
            _ensure_parent(target)
            self.assertTrue((Path(tmpdir) / "nested").exists())

    def test_extract_ticket_ref_success_and_failure(self) -> None:
        payload = {
            "ticket_number": "T123",
            "ticket_id": "conv-123",
            "ticket_number_fingerprint": "abc",
            "ticket_id_fingerprint": "def",
        }
        output = f"TICKET_REF_JSON:{json.dumps(payload)}"
        result = _extract_ticket_ref(output)
        self.assertEqual(result["ticket_number"], "T123")
        with self.assertRaises(RuntimeError):
            _extract_ticket_ref("no ticket")

    def test_run_command_wrapper(self) -> None:
        with patch("b62_sandbox_golden_path.subprocess.run") as mocked:
            mocked.return_value = CompletedProcess(["cmd"], 0, "ok", "")
            result = _run_command(["cmd"])
            self.assertEqual(result.stdout, "ok")

    def test_read_proof_variants(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "proof.json"
            self.assertIsNone(_read_proof(path))
            path.write_text("{invalid", encoding="utf-8")
            self.assertIsNone(_read_proof(path))
            path.write_text(json.dumps({"ok": True}), encoding="utf-8")
            self.assertEqual(_read_proof(path), {"ok": True})

    def test_git_diffstat_branches(self) -> None:
        with patch("b62_sandbox_golden_path.subprocess.run") as mocked:
            mocked.side_effect = FileNotFoundError()
            self.assertEqual(_git_diffstat(ROOT), "(git not available)")
        with patch("b62_sandbox_golden_path.subprocess.run") as mocked:
            mocked.return_value = CompletedProcess([], 1, "", "boom")
            self.assertIn("git diff failed", _git_diffstat(ROOT))
        with patch("b62_sandbox_golden_path.subprocess.run") as mocked:
            mocked.return_value = CompletedProcess([], 0, "", "")
            self.assertEqual(_git_diffstat(ROOT), "(no changes)")

    def test_wrapper_imports(self) -> None:
        import sandbox_golden_path_proof  # type: ignore

        self.assertTrue(callable(sandbox_golden_path_proof.main))

    def test_write_run_report_and_evidence(self) -> None:
        proof = {
            "result": {"status": "PASS", "classification": "PASS_STRONG"},
            "proof_fields": {"outbound_failure_classification": None},
            "inputs": {"ticket_ref_fingerprint": "abc"},
        }
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            report_path = tmp / "RUN_REPORT.md"
            _write_run_report(report_path, proof=proof, error=None)
            content = report_path.read_text(encoding="utf-8")
            self.assertIn("PASS", content)
            _write_run_report(report_path, proof=proof, error="boom")
            self.assertIn("boom", report_path.read_text(encoding="utf-8"))
            evidence_path = tmp / "EVIDENCE.md"
            _write_evidence(
                evidence_path,
                root=ROOT,
                wrapper_cmd=["python", "script.py", "--ticket-id", "123"],
                create_cmds=[["python", "create.py"]],
                recent_cmds=[["python", "recent.py"]],
                smoke_cmds=[["python", "smoke.py"]],
                proof=proof,
            )
            evidence = evidence_path.read_text(encoding="utf-8")
            self.assertIn("Internal command — create ticket", evidence)
            self.assertIn("Internal command — find recent ticket", evidence)
            self.assertIn("Internal command — smoke proof", evidence)

    def test_write_changes(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir) / "CHANGES.md"
            with patch("b62_sandbox_golden_path._git_diffstat") as mocked:
                mocked.return_value = "diffstat"
                _write_changes(tmp)
            self.assertIn("diffstat", tmp.read_text(encoding="utf-8"))


class ProofExcerptTests(unittest.TestCase):
    def test_proof_excerpt_contains_required_keys(self) -> None:
        proof = {
            "proof_fields": {
                "openai_routing_used": True,
                "openai_rewrite_used": True,
                "order_match_by_number": True,
                "outbound_send_message_status": 200,
                "send_message_path_confirmed": True,
                "send_message_tag_present": True,
                "latest_comment_is_operator": True,
                "closed_after": True,
                "followup_reply_sent": False,
                "followup_routed_support": True,
            }
        }
        excerpt = json.loads(_proof_excerpt(proof))
        self.assertIn("openai_routing_used", excerpt)
        self.assertIn("openai_rewrite_used", excerpt)
        self.assertIn("order_match_by_number", excerpt)
        self.assertIn("outbound_send_message_status", excerpt)
        self.assertIn("latest_comment_is_operator", excerpt)
        self.assertIn("followup_reply_sent", excerpt)
        missing = json.loads(_proof_excerpt(None))
        self.assertEqual(missing["error"], "proof not available")


class MainFlowTests(unittest.TestCase):
    def test_main_successful_flow(self) -> None:
        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            if "create_sandbox_email_ticket.py" in " ".join(cmd):
                payload = {
                    "ticket_number": "T123",
                    "ticket_id": "conv-123",
                    "ticket_number_fingerprint": "abc",
                    "ticket_id_fingerprint": "def",
                }
                return CompletedProcess(cmd, 0, f"TICKET_REF_JSON:{json.dumps(payload)}", "")
            return CompletedProcess(cmd, 0, "", "")

        proof = {"proof_fields": {"outbound_failure_classification": None}}
        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ), patch("b62_sandbox_golden_path._read_proof", return_value=proof):
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--profile",
                "test-profile",
                "--allowlist-email",
                "test@example.com",
                "--run-id",
                "RUN_ID",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 0)

    def test_main_includes_order_number(self) -> None:
        captured = {"smoke": None}

        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            joined = " ".join(cmd)
            if "create_sandbox_email_ticket.py" in joined:
                payload = {
                    "ticket_number": "T123",
                    "ticket_id": "conv-123",
                    "ticket_number_fingerprint": "abc",
                    "ticket_id_fingerprint": "def",
                }
                return CompletedProcess(cmd, 0, f"TICKET_REF_JSON:{json.dumps(payload)}", "")
            if "dev_e2e_smoke.py" in joined:
                captured["smoke"] = cmd
            return CompletedProcess(cmd, 0, "", "")

        proof = {"proof_fields": {"outbound_failure_classification": None}}
        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ), patch("b62_sandbox_golden_path._read_proof", return_value=proof):
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
                "--order-number",
                "ORDER-123",
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 0)

        self.assertIsNotNone(captured["smoke"])
        self.assertIn("--order-number", captured["smoke"])
        self.assertIn("ORDER-123", captured["smoke"])

    def test_main_fallback_to_recent(self) -> None:
        calls = {"create": 0, "recent": 0}

        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            joined = " ".join(cmd)
            if "create_sandbox_email_ticket.py" in joined:
                calls["create"] += 1
                return CompletedProcess(cmd, 1, "", "fail")
            if "find_recent_sandbox_ticket.py" in joined:
                calls["recent"] += 1
                payload = [{"ticket_number": "T9", "ticket_id": "conv-9"}]
                return CompletedProcess(cmd, 0, json.dumps(payload), "")
            return CompletedProcess(cmd, 0, "", "")

        proof = {"proof_fields": {"outbound_failure_classification": None}}
        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ), patch("b62_sandbox_golden_path._read_proof", return_value=proof):
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--profile",
                "test-profile",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 0)
        self.assertEqual(calls["create"], 1)
        self.assertEqual(calls["recent"], 1)

    def test_main_recent_errors(self) -> None:
        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            joined = " ".join(cmd)
            if "create_sandbox_email_ticket.py" in joined:
                return CompletedProcess(cmd, 1, "", "fail")
            if "find_recent_sandbox_ticket.py" in joined:
                return CompletedProcess(cmd, 1, "", "fail")
            return CompletedProcess(cmd, 0, "", "")

        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ):
            fake_run(["noop"])
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 1)

    def test_main_recent_invalid_payload(self) -> None:
        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            joined = " ".join(cmd)
            if "create_sandbox_email_ticket.py" in joined:
                return CompletedProcess(cmd, 1, "", "fail")
            if "find_recent_sandbox_ticket.py" in joined:
                return CompletedProcess(cmd, 0, "not-json", "")
            return CompletedProcess(cmd, 0, "", "")

        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ):
            fake_run(["noop"])
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 1)

    def test_main_recent_empty_payload(self) -> None:
        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            joined = " ".join(cmd)
            if "create_sandbox_email_ticket.py" in joined:
                return CompletedProcess(cmd, 1, "", "fail")
            if "find_recent_sandbox_ticket.py" in joined:
                return CompletedProcess(cmd, 0, "[]", "")
            return CompletedProcess(cmd, 0, "", "")

        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ):
            fake_run(["noop"])
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 1)

    def test_main_smoke_failure_with_explicit_ticket_id(self) -> None:
        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            return CompletedProcess(cmd, 1, "", "fail")

        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ):
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--ticket-id",
                "conv-xyz",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 1)

    def test_main_retry_skips_tried_recent(self) -> None:
        state = {"smoke_calls": 0}

        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            joined = " ".join(cmd)
            if "create_sandbox_email_ticket.py" in joined:
                return CompletedProcess(cmd, 1, "", "fail")
            if "find_recent_sandbox_ticket.py" in joined:
                payload = [
                    "bad-entry",
                    {"ticket_number": "T1", "ticket_id": "C1"},
                    {"ticket_number": "T2", "ticket_id": "C2"},
                ]
                return CompletedProcess(cmd, 0, json.dumps(payload), "")
            if "dev_e2e_smoke.py" in joined:
                state["smoke_calls"] += 1
                return CompletedProcess(cmd, 1 if state["smoke_calls"] == 1 else 0, "", "")
            return CompletedProcess(cmd, 0, "", "")

        proof = {"proof_fields": {"outbound_failure_classification": None}}
        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ), patch("b62_sandbox_golden_path._read_proof", return_value=proof):
            fake_run(["noop"])
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 0)

    def test_main_recent_all_tried(self) -> None:
        state = {"smoke_calls": 0}

        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            joined = " ".join(cmd)
            if "create_sandbox_email_ticket.py" in joined:
                return CompletedProcess(cmd, 1, "", "fail")
            if "find_recent_sandbox_ticket.py" in joined:
                payload = [{"ticket_number": "T1", "ticket_id": "C1"}]
                return CompletedProcess(cmd, 0, json.dumps(payload), "")
            if "dev_e2e_smoke.py" in joined:
                state["smoke_calls"] += 1
                return CompletedProcess(cmd, 1, "", "fail")
            return CompletedProcess(cmd, 0, "", "")

        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ):
            fake_run(["noop"])
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 1)

    def test_main_smoke_failure_retries_exhausted(self) -> None:
        state = {"recent_calls": 0}

        def fake_run(cmd, **_kwargs):  # type: ignore[override]
            joined = " ".join(cmd)
            if "create_sandbox_email_ticket.py" in joined:
                return CompletedProcess(cmd, 1, "", "fail")
            if "find_recent_sandbox_ticket.py" in joined:
                state["recent_calls"] += 1
                payload = [
                    {
                        "ticket_number": f"T{state['recent_calls']}",
                        "ticket_id": f"C{state['recent_calls']}",
                    }
                ]
                return CompletedProcess(cmd, 0, json.dumps(payload), "")
            return CompletedProcess(cmd, 1, "", "fail")

        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command", side_effect=fake_run
        ):
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(main(), 1)

    def test_main_reports_allowlist_block(self) -> None:
        proof = {
            "proof_fields": {"outbound_failure_classification": "blocked_by_allowlist"}
        }
        with TemporaryDirectory() as tmpdir, patch(
            "b62_sandbox_golden_path._run_command",
            return_value=CompletedProcess([], 0, "", ""),
        ), patch("b62_sandbox_golden_path._read_proof", return_value=proof):
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--stack-name",
                "Stack",
                "--ticket-number",
                "T1",
                "--artifacts-dir",
                tmpdir,
                "--proof-path",
                str(Path(tmpdir) / "proof.json"),
            ]
            with patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()) as buf:
                self.assertEqual(main(), 0)
            self.assertIn("Outbound blocked by allowlist", buf.getvalue())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
