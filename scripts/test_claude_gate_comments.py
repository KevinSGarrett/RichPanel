#!/usr/bin/env python3
"""Unit tests for claude_gate_comments.py"""
import json
import unittest
from pathlib import Path

import claude_gate_comments

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> list[dict]:
    path = FIXTURES_DIR / name
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


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


if __name__ == "__main__":
    unittest.main()
