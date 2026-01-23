#!/usr/bin/env python3
import unittest

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


if __name__ == "__main__":
    unittest.main()
