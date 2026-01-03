#!/usr/bin/env python3
"""
Minimal integration tests for the middleware ingress + worker Lambdas.

This script runs entirely offline with stubbed AWS clients so it can execute in CI.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

# Ensure Lambda modules see deterministic environment values at import time.
os.environ.setdefault("QUEUE_URL", "https://sqs.us-east-2.amazonaws.com/123456789012/rp-mw-dev-events.fifo")
os.environ.setdefault("WEBHOOK_SECRET_ARN", "arn:aws:secretsmanager:us-east-2:123456789012:secret:rp-mw/dev/richpanel/webhook_token")
os.environ.setdefault("DEFAULT_MESSAGE_GROUP_ID", "rp-mw-dev-default")
os.environ.setdefault("EVENT_SOURCE", "richpanel_http_target")
os.environ.setdefault("IDEMPOTENCY_TABLE_NAME", "rp_mw_dev_idempotency")
os.environ.setdefault("SAFE_MODE_PARAM", "/rp-mw/dev/safe_mode")
os.environ.setdefault("AUTOMATION_ENABLED_PARAM", "/rp-mw/dev/automation_enabled")

from lambda_handlers.ingress import handler as ingress_handler  # noqa: E402
from lambda_handlers.worker import handler as worker_handler  # noqa: E402


@dataclass
class StubSecretsClient:
    token: str
    calls: int = 0

    def get_secret_value(self, SecretId: str) -> Dict[str, Any]:  # noqa: N802 (AWS casing)
        self.calls += 1
        return {"SecretString": self.token}


@dataclass
class StubSqsClient:
    messages: List[Dict[str, Any]] = field(default_factory=list)

    def send_message(
        self,
        QueueUrl: str,
        MessageBody: str,
        MessageGroupId: str,
        MessageDeduplicationId: str,
    ) -> Dict[str, Any]:
        self.messages.append(
            {
                "QueueUrl": QueueUrl,
                "Body": MessageBody,
                "GroupId": MessageGroupId,
                "DedupId": MessageDeduplicationId,
            }
        )
        return {"MessageId": "stubbed"}


@dataclass
class StubSsmClient:
    safe_mode: str = "false"
    automation_enabled: str = "true"

    def get_parameters(self, Names: List[str], WithDecryption: bool = False) -> Dict[str, Any]:  # noqa: N802
        params = []
        for name in Names:
            if name.endswith("safe_mode"):
                params.append({"Name": name, "Value": self.safe_mode})
            elif name.endswith("automation_enabled"):
                params.append({"Name": name, "Value": self.automation_enabled})
        return {"Parameters": params, "InvalidParameters": []}


@dataclass
class StubDynamoTable:
    items: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def put_item(self, Item: Dict[str, Any], ConditionExpression: str | None = None) -> Dict[str, Any]:
        event_id = Item["event_id"]
        if ConditionExpression == "attribute_not_exists(event_id)" and event_id in self.items:
            raise RuntimeError("Duplicate event")
        self.items[event_id] = Item
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


def run_ingress_test(secret_token: str) -> Dict[str, Any]:
    ingress_handler._SECRETS_CLIENT = StubSecretsClient(secret_token)  # type: ignore[attr-defined]
    stub_sqs = StubSqsClient()
    ingress_handler._SQS_CLIENT = stub_sqs  # type: ignore[attr-defined]

    event_body = {
        "event_id": "evt:test-123",
        "conversation_id": "conv-1",
        "message_id": "msg-1",
        "payload_value": "hello",
    }
    event = {
        "headers": {"X-Richpanel-Webhook-Token": secret_token},
        "body": json.dumps(event_body),
        "isBase64Encoded": False,
    }

    response = ingress_handler.lambda_handler(event, None)
    assert response["statusCode"] == 200, "Ingress handler did not return 200."
    assert stub_sqs.messages, "Ingress handler did not enqueue message."

    message_body = json.loads(stub_sqs.messages[0]["Body"])
    assert message_body["event_id"] == event_body["event_id"]
    assert message_body["payload"]["payload_value"] == "hello"

    return {"sqs": stub_sqs, "message_body": message_body}


def run_worker_test(message_body: Dict[str, Any]) -> None:
    worker_handler._IDEMPOTENCY_TABLE = StubDynamoTable()  # type: ignore[attr-defined]
    worker_handler._SSM_CLIENT = StubSsmClient(safe_mode="false", automation_enabled="true")  # type: ignore[attr-defined]
    worker_handler._FLAG_CACHE["expires_at"] = 0  # type: ignore[attr-defined]

    sqs_event = {
        "Records": [
            {
                "body": json.dumps(message_body),
                "messageId": "msg-1",
            }
        ]
    }

    response = worker_handler.lambda_handler(sqs_event, None)
    assert response["batchItemFailures"] == [], "Worker reported unexpected failures."
    table: StubDynamoTable = worker_handler._IDEMPOTENCY_TABLE  # type: ignore
    assert message_body["event_id"] in table.items, "Worker did not persist idempotency record."


def main() -> int:
    secret = "test-token"
    ingress_result = run_ingress_test(secret)
    run_worker_test(ingress_result["message_body"])
    print("[OK] Pipeline handler smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

