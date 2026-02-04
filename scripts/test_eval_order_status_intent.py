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
                    {
                        "id",
                        "expected",
                        "predicted",
                        "llm_called",
                        "model",
                        "confidence",
                        "text_fingerprint",
                        "excerpt_redacted",
                    },
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
        suggestion.confidence = None
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
                output_csv_path=None,
                    use_openai=False,
                    allow_network=False,
                ticket_ids=None,
                )
        self.assertEqual(summary["source"]["type"], "richpanel")
        self.assertEqual(summary["source"]["limit"], 1)

    def test_load_ticket_ids_from_args_and_file(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            ticket_path = Path(tmp_dir) / "tickets.txt"
            ticket_path.write_text("a\nb\n\nc\n", encoding="utf-8")
            result = intent_eval._load_ticket_ids("x,y", str(ticket_path))
        self.assertEqual(result, ["x", "y", "a", "b", "c"])

    def test_redact_excerpt_masks_text(self) -> None:
        excerpt = intent_eval._redact_excerpt("Email test@example.com order 123456")
        self.assertIsNotNone(excerpt)
        self.assertNotIn("test@example.com", excerpt)
        self.assertNotIn("123456", excerpt)

    def test_write_csv_outputs_headers(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "out.csv"
            summary = {
                "results": [
                    {
                        "id": "redacted:1",
                        "expected": "order_status",
                        "predicted": "order_status",
                        "llm_called": False,
                        "model": "deterministic",
                        "confidence": None,
                        "text_fingerprint": "abc",
                        "excerpt_redacted": "xxx",
                    }
                ]
            }
            intent_eval.write_csv(output_path, summary)
            content = output_path.read_text(encoding="utf-8")
        self.assertIn("text_fingerprint", content)
        self.assertIn("excerpt_redacted", content)

    def test_load_ticket_ids_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            intent_eval._load_ticket_ids(None, "does_not_exist.txt")

    def test_redact_excerpt_empty_returns_none(self) -> None:
        self.assertIsNone(intent_eval._redact_excerpt(""))

    def test_extract_message_prefers_conversation(self) -> None:
        ticket = {"message": ""}
        convo = {"messages": [{"sender_type": "customer", "body": "Need status"}]}
        self.assertEqual(intent_eval._extract_message(ticket, convo), "Need status")

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

    def test_label_and_redaction_helpers(self) -> None:
        self.assertEqual(
            intent_eval._label_from_intent("order_status_tracking"), "order_status"
        )
        self.assertEqual(intent_eval._label_from_intent("refund_request"), "non_order_status")
        self.assertTrue(intent_eval._fingerprint("hello"))
        self.assertIsNone(intent_eval._redact_identifier(None))
        self.assertIsNone(intent_eval._redact_identifier("   "))
        self.assertTrue(intent_eval._redact_identifier("ticket-123").startswith("redacted:"))

    def test_compute_metrics_empty(self) -> None:
        metrics = intent_eval._compute_metrics([])
        self.assertEqual(metrics["precision"], 0.0)
        self.assertEqual(metrics["recall"], 0.0)

    def test_compute_metrics_non_empty(self) -> None:
        pairs = [("order_status", "order_status"), ("non_order_status", "order_status")]
        metrics = intent_eval._compute_metrics(pairs)
        self.assertEqual(metrics["tp"], 1)
        self.assertEqual(metrics["fp"], 1)

    def test_resolve_env_name_priority(self) -> None:
        env = {"RICHPANEL_ENV": "Staging", "MW_ENV": "prod"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(intent_eval._resolve_env_name(), "staging")

    def test_is_prod_target_variants(self) -> None:
        with mock.patch.dict(os.environ, {"MW_ENV": "prod"}, clear=True):
            self.assertTrue(
                intent_eval._is_prod_target(
                    richpanel_base_url=intent_eval.PROD_RICHPANEL_BASE_URL,
                    richpanel_secret_id=None,
                )
            )
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(
                intent_eval._is_prod_target(
                    richpanel_base_url="https://api.richpanel.com",
                    richpanel_secret_id="rp-mw/prod/richpanel/api_key",
                )
            )
        with mock.patch.dict(os.environ, {"PROD_RICHPANEL_API_KEY": "x"}, clear=True):
            self.assertTrue(
                intent_eval._is_prod_target(
                    richpanel_base_url=intent_eval.PROD_RICHPANEL_BASE_URL,
                    richpanel_secret_id=None,
                )
            )
        with mock.patch.dict(os.environ, {"MW_ENV": "dev"}, clear=True):
            self.assertFalse(
                intent_eval._is_prod_target(
                    richpanel_base_url="https://sandbox.richpanel.com",
                    richpanel_secret_id=None,
                )
            )

    def test_fetch_recent_ticket_ids_success(self) -> None:
        class _StubResponse:
            def __init__(self, payload):
                self.status_code = 200
                self.dry_run = False
                self._payload = payload

            def json(self):
                return self._payload

        class _StubClient:
            def request(self, *args, **kwargs):
                return _StubResponse({"tickets": [{"id": "t-1"}, {"id": "t-2"}]})

        ids = intent_eval._fetch_recent_ticket_ids(_StubClient(), limit=1)
        self.assertEqual(ids, ["t-1"])

    def test_load_richpanel_examples_success_and_skip(self) -> None:
        with mock.patch.object(
            intent_eval, "_fetch_recent_ticket_ids", return_value=["t-1", "t-2"]
        ):
            with mock.patch.object(intent_eval, "_fetch_ticket_payload", return_value={}):
                with mock.patch.object(
                    intent_eval, "_fetch_conversation_payload", return_value={}
                ):
                    with mock.patch.object(
                        intent_eval, "_extract_message", side_effect=["hello", ""]
                    ):
                        examples = intent_eval._load_richpanel_examples(
                            limit=2,
                            richpanel_secret_id=None,
                            base_url="https://example.com",
                        )
        self.assertEqual(len(examples), 1)
        self.assertTrue(examples[0].example_id.startswith("redacted:"))

        with mock.patch.object(
            intent_eval, "_fetch_recent_ticket_ids", return_value=["t-1"]
        ):
            with mock.patch.object(intent_eval, "_fetch_ticket_payload", return_value={}):
                with mock.patch.object(
                    intent_eval, "_fetch_conversation_payload", return_value={}
                ):
                    with mock.patch.object(intent_eval, "_extract_message", return_value=""):
                        with self.assertRaises(SystemExit):
                            intent_eval._load_richpanel_examples(
                                limit=1,
                                richpanel_secret_id=None,
                                base_url="https://example.com",
                            )

    def test_write_summary(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "summary.json"
            intent_eval.write_summary(path, {"ok": True})
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data["ok"])

    def test_print_metrics_available(self) -> None:
        intent_eval._print_metrics("det", {"precision": 1.0, "recall": 1.0, "tp": 1, "fp": 0, "fn": 0, "tn": 0})

    def test_main_requires_write_disabled_for_prod(self) -> None:
        with mock.patch.object(intent_eval, "_is_prod_target", return_value=True):
            with mock.patch.object(sys, "argv", ["eval_order_status_intent.py", "--from-richpanel"]):
                with mock.patch.dict(os.environ, {"RICHPANEL_WRITE_DISABLED": "false"}, clear=True):
                    with self.assertRaises(SystemExit):
                        intent_eval.main()


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        OrderStatusIntentEvalTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
