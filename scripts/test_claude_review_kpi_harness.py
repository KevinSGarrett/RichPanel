#!/usr/bin/env python3
import unittest
from unittest.mock import patch

import claude_review_calibration_harness as harness


class TestClaudeReviewCalibrationHarness(unittest.TestCase):
    def test_harness_deterministic(self) -> None:
        fixtures = [
            "legacy_small",
            "structured_small",
            "wave2_lens_infra",
            "wave2_lens_order_status",
            "wave2_repeat_issue",
        ]
        first = harness.run_harness(fixtures, mode="structured")
        second = harness.run_harness(fixtures, mode="structured")
        self.assertEqual(first, second)
        self.assertEqual(first["overall"]["action_required_runs"], 3)

    @patch("urllib.request.urlopen", side_effect=AssertionError("network call"))
    def test_harness_offline(self, _mock_urlopen) -> None:
        fixtures = [
            "legacy_small",
            "structured_small",
            "wave2_lens_infra",
            "wave2_lens_order_status",
            "wave2_repeat_issue",
        ]
        harness.run_harness(fixtures, mode="structured")


if __name__ == "__main__":
    unittest.main()
