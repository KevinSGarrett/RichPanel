from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import eval_order_status_intent as intent_eval  # noqa: E402


class OrderStatusIntentEvalTests(unittest.TestCase):
    def test_eval_output_structure_and_no_raw_text(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            dataset_path = Path(tmp_dir) / "dataset.jsonl"
            output_path = Path(tmp_dir) / "results.json"
            dataset_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "id": "t-1",
                                "text": "Super secret message 123",
                                "expected": "order_status",
                            }
                        ),
                        json.dumps(
                            {
                                "id": "t-2",
                                "text": "Refund my order please",
                                "expected": "non_order_status",
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            summary = intent_eval.run_dataset_eval(
                dataset_path,
                output_path=output_path,
                use_openai=False,
                allow_network=False,
            )

            self.assertTrue(output_path.exists())
            loaded = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("results", loaded)
            self.assertIn("metrics", loaded)
            self.assertEqual(summary["counts"]["total"], 2)

            for item in loaded["results"]:
                self.assertEqual(
                    set(item.keys()),
                    {"id", "expected", "predicted", "llm_called", "model", "confidence"},
                )

            raw_output = output_path.read_text(encoding="utf-8")
            self.assertNotIn("Super secret message 123", raw_output)

    def test_deterministic_baseline_min_score(self) -> None:
        fixture_path = (
            ROOT
            / "scripts"
            / "fixtures"
            / "intent_eval"
            / "order_status_golden.jsonl"
        )
        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "results.json"
            summary = intent_eval.run_dataset_eval(
                fixture_path,
                output_path=output_path,
                use_openai=False,
                allow_network=False,
            )
            metrics = summary["metrics"]["deterministic"]
            self.assertGreaterEqual(metrics["precision"], 0.9)
            self.assertGreaterEqual(metrics["recall"], 0.9)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        OrderStatusIntentEvalTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
