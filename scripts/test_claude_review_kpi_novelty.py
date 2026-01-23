#!/usr/bin/env python3
import unittest
from typing import Any
import claude_gate_review as gate


class TestClaudeReviewNoveltyExtraction(unittest.TestCase):
    def test_extract_failed_check_summaries(self) -> None:
        check_runs: list[dict[Any, Any]] = [
            {"name": "Lint", "status": "completed", "conclusion": "success"},
            {
                "name": "Bugbot",
                "status": "completed",
                "conclusion": "failure",
                "output": {"title": "Bugbot found 2 issues"},
            },
            {"name": "Codecov", "status": "completed", "conclusion": "action_required"},
            {"name": "CI", "status": "in_progress", "conclusion": None},
            {
                "name": "Bugbot",
                "status": "completed",
                "conclusion": "failure",
                "output": {"title": "Bugbot found 2 issues"},
            },
        ]
        summaries = gate._extract_failed_check_summaries(check_runs, limit=6)
        self.assertEqual(summaries, ["Bugbot: Bugbot found 2 issues", "Codecov"])


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
