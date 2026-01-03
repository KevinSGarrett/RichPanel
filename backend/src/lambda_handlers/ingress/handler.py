import base64
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Minimal stand-in so local tests can run without boto3/botocore."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore

from richpanel_middleware.ingest.envelope import build_event_envelope

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

QUEUE_URL = os.environ["QUEUE_URL"]
WEBHOOK_SECRET_ARN = os.environ["WEBHOOK_SECRET_ARN"]
DEFAULT_MESSAGE_GROUP_ID = os.environ.get("DEFAULT_MESSAGE_GROUP_ID", "rp-mw-default")
EVENT_SOURCE = os.environ.get("EVENT_SOURCE", "richpanel_http_target")
TOKEN_HEADER = "x-richpanel-webhook-token"
TOKEN_CACHE_TTL_SECONDS = int(os.environ.get("WEBHOOK_TOKEN_CACHE_TTL", "300"))

_SECRETS_CLIENT = None
_SQS_CLIENT = None
_TOKEN_CACHE: Dict[str, Any] = {"token": None, "expires_at": 0.0}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """Validate webhook token, enqueue payload, and ACK quickly."""
    try:
        expected_token = _load_expected_token()
    except Exception:
        LOGGER.exception("ingress.secret_load_failed")
        return _error_response(500, "internal_error")

    provided_token = _extract_token(event.get("headers") or {})
    if not provided_token:
        LOGGER.warning("ingress.missing_token")
        return _error_response(401, "missing_token")

    if provided_token != expected_token:
        LOGGER.warning("ingress.invalid_token")
        return _error_response(401, "invalid_token")

    payload = _parse_payload(event)
    message_envelope = build_event_envelope(
        payload, default_group_id=DEFAULT_MESSAGE_GROUP_ID, source=EVENT_SOURCE
    )

    try:
        _sqs_client().send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message_envelope.to_message()),
            MessageGroupId=message_envelope.group_id,
            MessageDeduplicationId=message_envelope.dedupe_id,
        )
    except (BotoCoreError, ClientError):
        LOGGER.exception(
            "ingress.enqueue_failed",
            extra={"event_id": message_envelope.event_id},
        )
        return _error_response(500, "enqueue_failed")

    LOGGER.info(
        "ingress.accepted",
        extra={
            "event_id": message_envelope.event_id,
            "group_id": message_envelope.group_id,
            "conversation_id": message_envelope.conversation_id,
        },
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "status": "accepted",
                "event_id": message_envelope.event_id,
            }
        ),
    }


def _load_expected_token() -> str:
    now = time.time()
    cached = _TOKEN_CACHE.get("token")
    expires_at = _TOKEN_CACHE.get("expires_at", 0.0)
    if cached and now < expires_at:
        return cached

    response = _secrets_client().get_secret_value(SecretId=WEBHOOK_SECRET_ARN)
    secret_value = response.get("SecretString")
    if secret_value is None and response.get("SecretBinary") is not None:
        secret_value = base64.b64decode(response["SecretBinary"]).decode("utf-8")

    if not secret_value:
        raise RuntimeError("Webhook token secret is empty.")

    _TOKEN_CACHE["token"] = secret_value
    _TOKEN_CACHE["expires_at"] = now + TOKEN_CACHE_TTL_SECONDS
    return secret_value


def _parse_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    try:
        payload = json.loads(body)
    except (TypeError, json.JSONDecodeError):
        LOGGER.warning("ingress.payload_parse_failed")
        payload = {"raw_body": body}

    return payload if isinstance(payload, dict) else {"data": payload}


def _extract_token(headers: Dict[str, Any]) -> str | None:
    for key, value in headers.items():
        if key and key.lower() == TOKEN_HEADER:
            return value
    return None


def _error_response(status: int, code: str) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "error", "code": code}),
    }


def _secrets_client():
    global _SECRETS_CLIENT
    if _SECRETS_CLIENT is None:
        if boto3 is None:
            raise RuntimeError("boto3 is required to create a secretsmanager client.")
        _SECRETS_CLIENT = boto3.client("secretsmanager")
    return _SECRETS_CLIENT


def _sqs_client():
    global _SQS_CLIENT
    if _SQS_CLIENT is None:
        if boto3 is None:
            raise RuntimeError("boto3 is required to create an sqs client.")
        _SQS_CLIENT = boto3.client("sqs")
    return _SQS_CLIENT

