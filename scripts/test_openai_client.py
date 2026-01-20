from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Optional

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
        self.last_request: Optional[TransportRequest] = None

    def send(self, request: TransportRequest) -> TransportResponse:
        self.calls += 1
        self.last_request = request
        return self.response


class _StubSecretsClient:
    def __init__(
        self, response: Optional[dict] = None, exc: Optional[Exception] = None
    ):
        self.calls = 0
        self.response = response or {}
        self.exc = exc

    def get_secret_value(self, SecretId: str) -> dict:
        self.calls += 1
        if self.exc:
            raise self.exc
        return self.response


class OpenAIClientTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure host env flags do not leak into tests.
        os.environ.pop("OPENAI_ALLOW_NETWORK", None)
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY_SECRET_ID", None)
        os.environ.pop("OPENAI_MODEL", None)
        os.environ.pop("RICHPANEL_ENV", None)
        os.environ.pop("RICH_PANEL_ENV", None)
        os.environ.pop("MW_ENV", None)
        os.environ.pop("ENVIRONMENT", None)

    def test_safe_mode_short_circuits_transport(self) -> None:
        transport = _FailingTransport()
        client = OpenAIClient(
            api_key="test-key", allow_network=True, transport=transport
        )

        request = ChatCompletionRequest(
            model="gpt-5.2-chat-latest",
            messages=[ChatMessage(role="user", content="hi")],
        )
        response = client.chat_completion(
            request, safe_mode=True, automation_enabled=True
        )

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "safe_mode")
        self.assertEqual(transport.calls, 0)

    def test_automation_disabled_short_circuits_transport(self) -> None:
        transport = _FailingTransport()
        client = OpenAIClient(
            api_key="test-key", allow_network=True, transport=transport
        )

        request = ChatCompletionRequest(
            model="gpt-5.2-chat-latest",
            messages=[ChatMessage(role="user", content="hi there")],
        )
        response = client.chat_completion(
            request, safe_mode=False, automation_enabled=False
        )

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
        self.assertEqual(
            prompt_fingerprint(contract_one), prompt_fingerprint(contract_two)
        )

    def test_offline_eval_runs_without_network(self) -> None:
        fixtures = load_order_status_fixtures(FIXTURES)
        self.assertTrue(fixtures)

        transport = _FailingTransport()
        client = OpenAIClient(
            api_key="test-key", allow_network=True, transport=transport
        )
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
            model="gpt-5.2-chat-latest",
            messages=[ChatMessage(role="user", content="hello")],
        )
        response = client.chat_completion(
            request, safe_mode=False, automation_enabled=True
        )

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "network_blocked")
        self.assertEqual(transport.calls, 0)

    def test_secret_path_uses_lowercased_env(self) -> None:
        os.environ["RICHPANEL_ENV"] = "Staging"

        client = OpenAIClient()

        self.assertEqual(client.environment, "staging")
        self.assertEqual(client.api_key_secret_id, "rp-mw/staging/openai/api_key")

    def test_missing_secret_short_circuits_to_dry_run(self) -> None:
        secrets_client = _StubSecretsClient(response={})
        transport = _FailingTransport()
        client = OpenAIClient(
            allow_network=True, transport=transport, secrets_client=secrets_client
        )

        request = ChatCompletionRequest(
            model="gpt-5.2-chat-latest",
            messages=[ChatMessage(role="user", content="hello")],
        )
        response = client.chat_completion(
            request, safe_mode=False, automation_enabled=True
        )

        self.assertTrue(response.dry_run)
        self.assertEqual(response.reason, "missing_api_key")
        self.assertEqual(transport.calls, 0)
        self.assertEqual(secrets_client.calls, 1)

    def test_header_redaction_masks_sensitive_keys(self) -> None:
        headers = {
            "Authorization": "Bearer secret",
            "authorization": "Bearer secret-two",
            "api-key": "abc456",
            "x-api-key": "abc123",
            "other": "ok",
        }
        redacted = OpenAIClient.redact_headers(headers)

        self.assertEqual(redacted["Authorization"], "***")
        self.assertEqual(redacted["authorization"], "***")
        self.assertEqual(redacted["x-api-key"], "***")
        self.assertEqual(redacted["api-key"], "***")
        self.assertEqual(redacted["other"], "ok")
        # Ensure original dict is unchanged.
        self.assertEqual(headers["Authorization"], "Bearer secret")
        self.assertEqual(headers["authorization"], "Bearer secret-two")

    def test_integrations_namespace_alias(self) -> None:
        self.assertIs(OpenAIClient, BoundaryOpenAIClient)

    def test_gpt5_payload_uses_max_completion_tokens(self) -> None:
        response = TransportResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=(
                b'{"choices":[{"message":{"content":"{\\"body\\":\\"ok\\",\\"confidence\\":0.9,\\"risk_flags\\":[]}"}}]}'
            ),
        )
        transport = _RecordingTransport(response=response)
        client = OpenAIClient(api_key="test-key", allow_network=True, transport=transport)
        request = ChatCompletionRequest(
            model="gpt-5.2-chat-latest",
            messages=[ChatMessage(role="user", content="hello")],
            temperature=0.0,
            max_tokens=128,
            metadata={"conversation_id": "c-1", "event_id": "evt-1"},
        )
        client.chat_completion(request, safe_mode=False, automation_enabled=True)

        self.assertIsNotNone(transport.last_request)
        payload = json.loads(transport.last_request.body.decode("utf-8"))
        self.assertIn("max_completion_tokens", payload)
        self.assertNotIn("max_tokens", payload)
        self.assertNotIn("temperature", payload)
        self.assertNotIn("metadata", payload)

    def test_non_gpt5_payload_uses_max_tokens_and_metadata(self) -> None:
        response = TransportResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body=(
                b'{"choices":[{"message":{"content":"{\\"body\\":\\"ok\\",\\"confidence\\":0.9,\\"risk_flags\\":[]}"}}]}'
            ),
        )
        transport = _RecordingTransport(response=response)
        client = OpenAIClient(api_key="test-key", allow_network=True, transport=transport)
        request = ChatCompletionRequest(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="hello")],
            temperature=0.2,
            max_tokens=64,
            metadata={"conversation_id": "c-2", "event_id": "evt-2"},
        )
        client.chat_completion(request, safe_mode=False, automation_enabled=True)

        self.assertIsNotNone(transport.last_request)
        payload = json.loads(transport.last_request.body.decode("utf-8"))
        self.assertIn("max_tokens", payload)
        self.assertNotIn("max_completion_tokens", payload)
        self.assertEqual(payload.get("temperature"), 0.2)
        self.assertIn("metadata", payload)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OpenAIClientTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
