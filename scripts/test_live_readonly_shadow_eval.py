from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock
from types import SimpleNamespace
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import live_readonly_shadow_eval as shadow_eval  # noqa: E402


class _StubResponse:
    def __init__(self, payload: dict, status_code: int = 200, dry_run: bool = False):
        self.status_code = status_code
        self.dry_run = dry_run
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _StubClient:
    def __init__(self) -> None:
        self.requests: list[tuple[str, str]] = []

    def request(self, method: str, path: str, **kwargs) -> _StubResponse:
        self.requests.append((method, path))
        if path.startswith("/v1/tickets/"):
            payload = {
                "ticket": {
                    "id": "t-123",
                    "order": {"order_id": "order-123", "tracking_number": "TN123"},
                    "customer": {"email": "customer@example.com", "name": "Test User"},
                }
            }
            return _StubResponse(payload)
        if path.startswith("/api/v1/conversations/"):
            payload = {"customer_profile": {"phone": "555-1212"}}
            return _StubResponse(payload)
        return _StubResponse({}, status_code=404)


class LiveReadonlyShadowEvalGuardTests(unittest.TestCase):
    def test_prod_requires_write_disabled(self) -> None:
        env = {
            "MW_ENV": "prod",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "true",
            "RICHPANEL_WRITE_DISABLED": "false",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            argv = ["live_readonly_shadow_eval.py", "--ticket-id", "123"]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit) as ctx:
                    shadow_eval.main()
        self.assertIn("RICHPANEL_WRITE_DISABLED", str(ctx.exception))


class LiveReadonlyShadowEvalHelpersTests(unittest.TestCase):
    def test_is_prod_target_detects_env(self) -> None:
        env = {"MW_ENV": "prod"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = shadow_eval._is_prod_target(
                richpanel_base_url=shadow_eval.PROD_RICHPANEL_BASE_URL,
                richpanel_secret_id=None,
            )
        self.assertTrue(result)

    def test_is_prod_target_detects_prod_key_and_base(self) -> None:
        env = {"PROD_RICHPANEL_API_KEY": "token-value"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = shadow_eval._is_prod_target(
                richpanel_base_url=shadow_eval.PROD_RICHPANEL_BASE_URL,
                richpanel_secret_id=None,
            )
        self.assertTrue(result)

    def test_is_prod_target_false_for_non_prod(self) -> None:
        env = {"MW_ENV": "dev"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = shadow_eval._is_prod_target(
                richpanel_base_url="https://sandbox.richpanel.com",
                richpanel_secret_id=None,
            )
        self.assertFalse(result)

    def test_redact_path_hashes_ids(self) -> None:
        redacted = shadow_eval._redact_path("/v1/tickets/91608")
        self.assertTrue(redacted.startswith("/v1/tickets/"))
        self.assertIn("redacted:", redacted)
        self.assertNotIn("91608", redacted)

    def test_require_env_flag_missing_raises(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                shadow_eval._require_env_flag(
                    "RICHPANEL_WRITE_DISABLED", "true", context="test"
                )
        self.assertIn("unset", str(ctx.exception))

    def test_http_trace_records_and_asserts(self) -> None:
        trace = shadow_eval._HttpTrace()
        trace.record("GET", "https://api.richpanel.com/v1/tickets/123")
        trace.assert_get_only(context="test", trace_path=Path("trace.json"))
        self.assertEqual(trace.entries[0]["method"], "GET")

        trace.record("POST", "https://api.richpanel.com/v1/tickets/123")
        with self.assertRaises(SystemExit):
            trace.assert_get_only(context="test", trace_path=Path("trace.json"))

    def test_http_trace_capture_wraps_urlopen(self) -> None:
        trace = shadow_eval._HttpTrace()
        calls = []

        def fake_urlopen(req, *args, **kwargs):
            calls.append(req)

            class _DummyResponse:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def read(self):
                    return b""

                @property
                def headers(self):
                    return {}

                def getcode(self):
                    return 200

            return _DummyResponse()

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            trace.capture()
            request = shadow_eval.urllib.request.Request(
                "https://api.richpanel.com/v1/tickets/123", method="GET"
            )
            shadow_eval.urllib.request.urlopen(request)
            trace.stop()

        self.assertTrue(calls)
        self.assertTrue(trace.entries)
        self.assertEqual(trace.entries[0]["service"], "richpanel")

    def test_main_runs_with_stubbed_client(self) -> None:
        env = {
            "MW_ENV": "dev",
            "MW_ALLOW_NETWORK_READS": "true",
            "RICHPANEL_OUTBOUND_ENABLED": "true",
            "RICHPANEL_WRITE_DISABLED": "true",
        }
        plan = SimpleNamespace(
            actions=[
                {
                    "type": "order_status_draft_reply",
                    "parameters": {
                        "order_summary": {
                            "order_id": "order-123",
                            "tracking_number": "TN123",
                        },
                        "delivery_estimate": {"eta_human": "2-4 days"},
                        "draft_reply": {"body": "stubbed"},
                    },
                }
            ],
            routing=SimpleNamespace(
                intent="order_status_tracking",
                department="Email Support Team",
                reason="stubbed",
            ),
            mode="automation_candidate",
            reasons=["stubbed"],
        )
        with TemporaryDirectory() as tmpdir, mock.patch.dict(
            os.environ, env, clear=True
        ):
            trace_path = Path(tmpdir) / "trace.json"
            artifact_path = Path(tmpdir) / "artifact.json"
            stub_client = _StubClient()
            argv = [
                "live_readonly_shadow_eval.py",
                "--ticket-id",
                "t-123",
                "--shop-domain",
                "example.myshopify.com",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                shadow_eval, "_build_richpanel_client", return_value=stub_client
            ), mock.patch.object(
                shadow_eval, "_build_trace_path", return_value=trace_path
            ), mock.patch.object(
                shadow_eval, "_build_artifact_path", return_value=artifact_path
            ), mock.patch.object(
                shadow_eval, "normalize_event", return_value=SimpleNamespace()
            ), mock.patch.object(
                shadow_eval, "plan_actions", return_value=plan
            ):
                result = shadow_eval.main()
                self.assertEqual(result, 0)
                self.assertTrue(trace_path.exists())
                self.assertTrue(artifact_path.exists())


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        LiveReadonlyShadowEvalGuardTests
    )
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            LiveReadonlyShadowEvalHelpersTests
        )
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
