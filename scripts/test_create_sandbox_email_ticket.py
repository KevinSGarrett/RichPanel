#!/usr/bin/env python3
"""
Unit tests for create_sandbox_email_ticket.py emit-ticket-ref behavior.
"""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import create_sandbox_email_ticket as ticket_script  # type: ignore


class _DummyResponse:
    def __init__(self) -> None:
        self.status_code = 200
        self.dry_run = False

    def json(self) -> dict:
        return {"ticket": {"conversation_no": "T123", "id": "conv-123"}}


class _DummyClient:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def request(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
        return _DummyResponse()


class EmitTicketRefTests(unittest.TestCase):
    def test_emit_ticket_ref_outputs_json(self) -> None:
        fake_boto3 = SimpleNamespace(setup_default_session=lambda **_: None)
        with TemporaryDirectory() as tmpdir:
            proof_path = str(Path(tmpdir) / "created.json")
            argv = [
                "prog",
                "--env",
                "dev",
                "--region",
                "us-east-2",
                "--emit-ticket-ref",
                "--proof-path",
                proof_path,
            ]
            with patch.object(
                ticket_script, "RichpanelClient", _DummyClient
            ), patch.object(
                ticket_script, "boto3", fake_boto3
            ), patch.object(
                sys, "argv", argv
            ), redirect_stdout(
                io.StringIO()
            ) as buf:
                code = ticket_script.main()
        self.assertEqual(code, 0)
        output = buf.getvalue()
        self.assertIn("TICKET_REF_JSON:", output)
        self.assertIn("ticket_number", output)
        self.assertIn("conv-123", output)
        self.assertIn("redacted:", output)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
