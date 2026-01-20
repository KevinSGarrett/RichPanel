from __future__ import annotations

import json
import os
import sys
import unittest
from types import SimpleNamespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

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

    def test_load_jsonl_dataset_errors(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            dataset_path = Path(tmp_dir) / "bad.jsonl"
            dataset_path.write_text("{bad json}\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                intent_eval.load_jsonl_dataset(dataset_path)

            dataset_path.write_text(
                json.dumps({"id": "x", "expected": "order_status"}), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                intent_eval.load_jsonl_dataset(dataset_path)

            dataset_path.write_text(
                json.dumps({"id": "x", "text": "hello", "expected": "invalid"}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                intent_eval.load_jsonl_dataset(dataset_path)

    def test_coerce_ticket_list(self) -> None:
        payload = [{"id": "1"}, "bad", {"id": "2"}]
        self.assertEqual(len(intent_eval._coerce_ticket_list(payload)), 2)

        payload = {"tickets": [{"id": "t-1"}, {"id": "t-2"}]}
        self.assertEqual(len(intent_eval._coerce_ticket_list(payload)), 2)

        payload = {"data": ["bad"]}
        self.assertEqual(intent_eval._coerce_ticket_list(payload), [])

    def test_fetch_recent_ticket_ids_errors(self) -> None:
        class _StubResponse:
            def __init__(self, payload, status_code=200, dry_run=False):
                self.status_code = status_code
                self.dry_run = dry_run
                self._payload = payload

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, response):
                self.response = response

            def request(self, *args, **kwargs):
                return self.response

        with self.assertRaises(SystemExit):
            intent_eval._fetch_recent_ticket_ids(
                _StubClient(_StubResponse({}, status_code=200, dry_run=True)), limit=1
            )
        with self.assertRaises(SystemExit):
            intent_eval._fetch_recent_ticket_ids(
                _StubClient(_StubResponse({}, status_code=500, dry_run=False)), limit=1
            )
        with self.assertRaises(SystemExit):
            intent_eval._fetch_recent_ticket_ids(
                _StubClient(_StubResponse({"tickets": []}, status_code=200)), limit=1
            )

    def test_fetch_payload_helpers(self) -> None:
        class _StubResponse:
            def __init__(self, payload, status_code=200, dry_run=False):
                self.status_code = status_code
                self.dry_run = dry_run
                self._payload = payload

            def json(self):
                return self._payload

        class _StubClient:
            def __init__(self, response):
                self.response = response

            def request(self, *args, **kwargs):
                return self.response

        ticket = intent_eval._fetch_ticket_payload(
            _StubClient(_StubResponse({}, status_code=404)), "t-1"
        )
        self.assertEqual(ticket, {})

        ticket = intent_eval._fetch_ticket_payload(
            _StubClient(_StubResponse({"ticket": {"id": "t-1"}})), "t-1"
        )
        self.assertEqual(ticket.get("id"), "t-1")

        convo = intent_eval._fetch_conversation_payload(
            _StubClient(_StubResponse({}, status_code=404)), "t-1"
        )
        self.assertEqual(convo, {})

    def test_extract_message(self) -> None:
        ticket = {"customer_message": "where is my order"}
        self.assertEqual(
            intent_eval._extract_message(ticket, {}), "where is my order"
        )

        convo = {"message": "hello from convo"}
        self.assertEqual(intent_eval._extract_message({}, convo), "hello from convo")

        convo = {
            "messages": [
                {"sender_type": "agent", "body": "ignore"},
                {"sender_type": "customer", "body": "need tracking"},
            ]
        }
        self.assertEqual(intent_eval._extract_message({}, convo), "need tracking")

    def test_evaluate_examples_with_llm(self) -> None:
        examples = [
            intent_eval.EvalExample(
                example_id="1", text="where is my order", expected="order_status"
            )
        ]
        suggestion = SimpleNamespace(
            llm_called=True,
            model="gpt-test",
            confidence=0.95,
            intent="order_status_tracking",
        )
        with mock.patch.object(
            intent_eval, "suggest_llm_routing", return_value=suggestion
        ):
            summary = intent_eval._evaluate_examples(
                examples, use_openai=True, allow_network=True
            )
        self.assertEqual(summary["metrics"]["llm"]["tp"], 1)
        self.assertEqual(summary["counts"]["llm_called"], 1)

        suggestion.llm_called = False
        with mock.patch.object(
            intent_eval, "suggest_llm_routing", return_value=suggestion
        ):
            summary = intent_eval._evaluate_examples(
                examples, use_openai=True, allow_network=False
            )
        self.assertFalse(summary["metrics"]["llm"]["available"])

    def test_run_richpanel_eval_source_metadata(self) -> None:
        examples = [
            intent_eval.EvalExample(
                example_id="redacted:1", text="tracking", expected="order_status"
            )
        ]
        with TemporaryDirectory() as tmp_dir:
            with mock.patch.object(
                intent_eval, "_load_richpanel_examples", return_value=examples
            ):
                summary = intent_eval.run_richpanel_eval(
                    limit=1,
                    richpanel_secret_id=None,
                    base_url="https://example.com",
                    output_path=Path(tmp_dir) / "out.json",
                    use_openai=False,
                    allow_network=False,
                )
        self.assertEqual(summary["source"]["type"], "richpanel")
        self.assertEqual(summary["source"]["limit"], 1)

    def test_main_dataset_and_richpanel_paths(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            dataset_path = Path(tmp_dir) / "dataset.jsonl"
            dataset_path.write_text(
                json.dumps(
                    {"id": "1", "text": "where is my order", "expected": "order_status"}
                ),
                encoding="utf-8",
            )
            output_path = Path(tmp_dir) / "out.json"
            with mock.patch.object(
                sys, "argv", ["eval_order_status_intent.py", "--dataset", str(dataset_path), "--output", str(output_path)]
            ):
                self.assertEqual(intent_eval.main(), 0)

        with mock.patch.object(sys, "argv", ["eval_order_status_intent.py"]):
            with self.assertRaises(SystemExit):
                intent_eval.main()

        with mock.patch.object(intent_eval, "_is_prod_target", return_value=False):
            with mock.patch.object(
                intent_eval,
                "run_richpanel_eval",
                return_value={
                    "metrics": {"deterministic": {}, "llm": {"available": False}},
                    "counts": {"total": 0},
                    "source": {},
                },
            ):
                with mock.patch.object(
                    sys,
                    "argv",
                    [
                        "eval_order_status_intent.py",
                        "--from-richpanel",
                        "--limit",
                        "1",
                        "--output",
                        str(Path(tmp_dir) / "richpanel.json"),
                    ],
                ):
                    self.assertEqual(intent_eval.main(), 0)

    def test_require_env_flag(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                intent_eval._require_env_flag("RICHPANEL_WRITE_DISABLED", "true", context="test")
        with mock.patch.dict(os.environ, {"RICHPANEL_WRITE_DISABLED": "false"}, clear=True):
            with self.assertRaises(SystemExit):
                intent_eval._require_env_flag("RICHPANEL_WRITE_DISABLED", "true", context="test")


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        OrderStatusIntentEvalTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
