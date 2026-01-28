#!/usr/bin/env python3
"""
Unit tests for the B62 sandbox golden path wrapper helpers.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from b62_sandbox_golden_path import _proof_excerpt, _redact_command  # type: ignore  # noqa: E402


class RedactionTests(unittest.TestCase):
    def test_redact_command_masks_sensitive_flags(self) -> None:
        cmd = [
            "python",
            "scripts/b62_sandbox_golden_path.py",
            "--ticket-number",
            "12345",
            "--allowlist-email",
            "test.user@example.com",
            "--ticket-id",
            "conv-abc",
        ]
        redacted = _redact_command(cmd)
        self.assertNotIn("12345", redacted)
        self.assertNotIn("test.user@example.com", redacted)
        self.assertNotIn("conv-abc", redacted)
        self.assertIn("<redacted>", redacted)


class ProofExcerptTests(unittest.TestCase):
    def test_proof_excerpt_contains_required_keys(self) -> None:
        proof = {
            "proof_fields": {
                "openai_routing_used": True,
                "openai_rewrite_used": True,
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
        self.assertIn("outbound_send_message_status", excerpt)
        self.assertIn("latest_comment_is_operator", excerpt)
        self.assertIn("followup_reply_sent", excerpt)


if __name__ == "__main__":
    unittest.main()
