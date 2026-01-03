from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from integrations.openai import OpenAIClient as BoundaryOpenAIClient  # noqa: E402
from richpanel_middleware.automation.prompts import (  # noqa: E402
    ORDER_STATUS_SYSTEM_PROMPT,
    build_order_status_contract,
    load_order_status_fixtures,
    prompt_fingerprint,
    run_offline_order_status_eval,
)
from richpanel_middleware.integrations.openai import (  # noqa: E402
    ChatCompletionRequest,
    ChatMessage,
    OpenAIClient,
    TransportRequest,
    TransportResponse,
)

FIXTURES = ROOT / "scripts" / "fixtures" / "order_status_samples.json"


class _FailingTransport:
    def __init__(self):
        self.calls = 0

    def send(self, request: TransportRequest) -> TransportResponse:
        self.calls += 1
        raise AssertionError("transport should not be used when automation is disabled")


class _RecordingTransport:
    def __init__(self, response: TransportResponse):
        self.calls = 0
        self.response = response

    def send(self, request: TransportRequest) -> TransportResponse:
        self.calls += 1
        return self.response


class OpenAIClientTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure host env flags do not leak into tests.
        os.environ.pop("OPENAI_ALLOW_NETWORK", None)
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("OPENAI_MODEL", None)

    def test_safe_mode_short_circuits_transport(self) -> None:
        transport = _FailingTransport()
        client = OpenAIClient(api_key="test-key", allow_network=True, transport=transport)

        request = ChatCompletionRequest(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="hi")],
        )
        response = client.chat_completion(request, safe_mode=True, automation_enabled=True)

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "safe_mode")
        self.assertEqual(transport.calls, 0)

    def test_automation_disabled_short_circuits_transport(self) -> None:
        transport = _FailingTransport()
        client = OpenAIClient(api_key="test-key", allow_network=True, transport=transport)

        request = ChatCompletionRequest(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="hi there")],
        )
        response = client.chat_completion(request, safe_mode=False, automation_enabled=False)

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "automation_disabled")
        self.assertEqual(transport.calls, 0)

    def test_prompt_builder_is_deterministic(self) -> None:
        fixtures = load_order_status_fixtures(FIXTURES)
        self.assertTrue(fixtures)
        fixture = fixtures[0]

        contract_one = build_order_status_contract(fixture)
        contract_two = build_order_status_contract(fixture)

        expected_context = (
            '{"customer_profile":{"email":"ava@example.com","name":"Ava"},'
            '"order_summary":{"eta":"2024-12-01","id":"ord-001","status":"shipped"}}'
        )
        expected_system = ORDER_STATUS_SYSTEM_PROMPT.format(context=expected_context)

        self.assertEqual(contract_one.messages, contract_two.messages)
        self.assertEqual(contract_one.messages[0].content, expected_system)
        self.assertEqual(prompt_fingerprint(contract_one), prompt_fingerprint(contract_two))

    def test_offline_eval_runs_without_network(self) -> None:
        fixtures = load_order_status_fixtures(FIXTURES)
        self.assertTrue(fixtures)

        transport = _FailingTransport()
        client = OpenAIClient(api_key="test-key", allow_network=True, transport=transport)
        results = run_offline_order_status_eval(
            fixtures, client=client, safe_mode=True, automation_enabled=False
        )

        self.assertTrue(results)
        self.assertTrue(all(result.response.dry_run for result in results))
        self.assertEqual(transport.calls, 0)

    def test_network_blocked_short_circuits(self) -> None:
        transport = _FailingTransport()
        client = OpenAIClient(allow_network=False, transport=transport)

        request = ChatCompletionRequest(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="hello")],
        )
        response = client.chat_completion(request, safe_mode=False, automation_enabled=True)

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "network_blocked")
        self.assertEqual(transport.calls, 0)

    def test_header_redaction_masks_sensitive_keys(self) -> None:
        headers = {
            "Authorization": "Bearer secret",
            "x-api-key": "abc123",
            "other": "ok",
        }
        redacted = OpenAIClient.redact_headers(headers)

        self.assertEqual(redacted["Authorization"], "***")
        self.assertEqual(redacted["x-api-key"], "***")
        self.assertEqual(redacted["other"], "ok")
        # Ensure original dict is unchanged.
        self.assertEqual(headers["Authorization"], "Bearer secret")

    def test_integrations_namespace_alias(self) -> None:
        self.assertIs(OpenAIClient, BoundaryOpenAIClient)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OpenAIClientTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

