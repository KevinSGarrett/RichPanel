import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Minimal stand-in so offline tests can run without boto3/botocore."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

IDEMPOTENCY_TABLE_NAME = os.environ["IDEMPOTENCY_TABLE_NAME"]
SAFE_MODE_PARAM = os.environ["SAFE_MODE_PARAM"]
AUTOMATION_ENABLED_PARAM = os.environ["AUTOMATION_ENABLED_PARAM"]
FLAG_CACHE_TTL_SECONDS = int(os.environ.get("FLAG_CACHE_TTL_SECONDS", "30"))

_SSM_CLIENT = None
_DDB_RESOURCE = None
_IDEMPOTENCY_TABLE = None
_FLAG_CACHE: Dict[str, Any] = {
    "safe_mode": True,
    "automation_enabled": False,
    "expires_at": 0.0,
}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    failures: List[Dict[str, str]] = []
    safe_mode, automation_enabled = _load_kill_switches()

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        try:
            body = json.loads(record["body"])
        except (KeyError, json.JSONDecodeError):
            LOGGER.exception("worker.body_parse_failed", extra={"message_id": message_id})
            failures.append({"itemIdentifier": message_id})
            continue

        try:
            _persist_idempotency(body, safe_mode, automation_enabled)
            LOGGER.info(
                "worker.processed",
                extra={
                    "event_id": body.get("event_id"),
                    "safe_mode": safe_mode,
                    "automation_enabled": automation_enabled,
                },
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                LOGGER.info(
                    "worker.duplicate_event",
                    extra={"event_id": body.get("event_id")},
                )
            else:
                LOGGER.exception(
                    "worker.ddb_error",
                    extra={"event_id": body.get("event_id")},
                )
                failures.append({"itemIdentifier": message_id})
        except BotoCoreError:
            LOGGER.exception(
                "worker.aws_core_error",
                extra={"event_id": body.get("event_id")},
            )
            failures.append({"itemIdentifier": message_id})
        except Exception:
            LOGGER.exception(
                "worker.unexpected_failure",
                extra={"event_id": body.get("event_id")},
            )
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}


def _persist_idempotency(
    body: Dict[str, Any], safe_mode: bool, automation_enabled: bool
) -> None:
    event_id = str(body.get("event_id") or f"evt:{int(time.time() * 1000)}")
    received_at = body.get("received_at") or datetime.now(timezone.utc).isoformat()
    payload_excerpt = _truncate_payload(body.get("payload"))
    mode = "route_only" if safe_mode or not automation_enabled else "automation_candidate"

    _table().put_item(
        Item={
            "event_id": event_id,
            "received_at": received_at,
            "last_processed_at": datetime.now(timezone.utc).isoformat(),
            "safe_mode": safe_mode,
            "automation_enabled": automation_enabled,
            "mode": mode,
            "source": body.get("source", "richpanel_http_target"),
            "payload_excerpt": payload_excerpt,
        },
        ConditionExpression="attribute_not_exists(event_id)",
    )


def _truncate_payload(value: Any) -> str:
    serialized = value
    if not isinstance(value, str):
        try:
            serialized = json.dumps(value)
        except (TypeError, ValueError):
            serialized = str(value)
    return (serialized or "")[:2000]


def _load_kill_switches() -> tuple[bool, bool]:
    now = time.time()
    if now < _FLAG_CACHE.get("expires_at", 0):
        return _FLAG_CACHE["safe_mode"], _FLAG_CACHE["automation_enabled"]

    response = _ssm_client().get_parameters(
        Names=[SAFE_MODE_PARAM, AUTOMATION_ENABLED_PARAM], WithDecryption=False
    )

    values = {param["Name"]: param.get("Value") for param in response.get("Parameters", [])}
    if response.get("InvalidParameters"):
        LOGGER.warning(
            "worker.flag_missing",
            extra={"invalid": response.get("InvalidParameters")},
        )

    safe_mode = _to_bool(values.get(SAFE_MODE_PARAM), default=False)
    automation_enabled = _to_bool(values.get(AUTOMATION_ENABLED_PARAM), default=True)

    if safe_mode:
        automation_enabled = False

    _FLAG_CACHE.update(
        {
            "safe_mode": safe_mode,
            "automation_enabled": automation_enabled,
            "expires_at": now + FLAG_CACHE_TTL_SECONDS,
        }
    )

    return safe_mode, automation_enabled


def _to_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _table():
    global _IDEMPOTENCY_TABLE
    if _IDEMPOTENCY_TABLE is None:
        _IDEMPOTENCY_TABLE = _dynamodb_resource().Table(IDEMPOTENCY_TABLE_NAME)
    return _IDEMPOTENCY_TABLE


def _ssm_client():
    global _SSM_CLIENT
    if _SSM_CLIENT is None:
        if boto3 is None:
            raise RuntimeError("boto3 is required to create an ssm client.")
        _SSM_CLIENT = boto3.client("ssm")
    return _SSM_CLIENT


def _dynamodb_resource():
    global _DDB_RESOURCE
    if _DDB_RESOURCE is None:
        if boto3 is None:
            raise RuntimeError("boto3 is required to create a dynamodb resource.")
        _DDB_RESOURCE = boto3.resource("dynamodb")
    return _DDB_RESOURCE

