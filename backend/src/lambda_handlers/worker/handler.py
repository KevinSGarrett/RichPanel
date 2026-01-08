import json
import logging
import math
import os
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Minimal stand-in so offline tests can run without boto3/botocore."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore

if TYPE_CHECKING:
    from botocore.client import BaseClient
    from boto3.resources.base import ServiceResource
else:  # pragma: no cover
    BaseClient = Any
    ServiceResource = Any

from richpanel_middleware.automation.pipeline import (
    ActionPlan,
    ExecutionResult,
    execute_order_status_reply,
    execute_routing_tags,
    execute_plan,
    normalize_event,
    plan_actions,
)
from richpanel_middleware.ingest.envelope import EventEnvelope

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

IDEMPOTENCY_TABLE_NAME = os.environ["IDEMPOTENCY_TABLE_NAME"]
SAFE_MODE_PARAM = os.environ["SAFE_MODE_PARAM"]
AUTOMATION_ENABLED_PARAM = os.environ["AUTOMATION_ENABLED_PARAM"]
FLAG_CACHE_TTL_SECONDS = int(os.environ.get("FLAG_CACHE_TTL_SECONDS", "30"))
IDEMPOTENCY_TTL_SECONDS = int(os.environ.get("IDEMPOTENCY_TTL_SECONDS", str(30 * 24 * 60 * 60)))
CONVERSATION_STATE_TABLE_NAME = os.environ.get("CONVERSATION_STATE_TABLE_NAME")
CONVERSATION_STATE_TTL_SECONDS = int(
    os.environ.get("CONVERSATION_STATE_TTL_SECONDS", str(90 * 24 * 60 * 60))
)
AUDIT_TRAIL_TABLE_NAME = os.environ.get("AUDIT_TRAIL_TABLE_NAME")
AUDIT_TRAIL_TTL_SECONDS = int(os.environ.get("AUDIT_TRAIL_TTL_SECONDS", str(60 * 24 * 60 * 60)))

_SSM_CLIENT: BaseClient | None = None
_DDB_RESOURCE: ServiceResource | None = None
_FLAG_CACHE: Dict[str, Any] = {
    "safe_mode": True,
    "automation_enabled": False,
    "expires_at": 0.0,
}
_TABLE_CACHE: Dict[str, Any] = {}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    failures: List[Dict[str, str]] = []
    safe_mode, automation_enabled = _load_kill_switches()
    outbound_enabled = _to_bool(os.environ.get("RICHPANEL_OUTBOUND_ENABLED"), default=False)
    allow_network = bool(outbound_enabled)

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        try:
            body = json.loads(record["body"])
        except (KeyError, json.JSONDecodeError):
            LOGGER.exception("worker.body_parse_failed", extra={"message_id": message_id})
            failures.append({"itemIdentifier": message_id})
            continue

        try:
            envelope = normalize_event(body)
            plan = plan_actions(envelope, safe_mode=safe_mode, automation_enabled=automation_enabled)
            persisted = _persist_idempotency(envelope, plan)
            execution = _execute_and_record(envelope, plan)
            outbound_result = _maybe_execute_outbound_reply(
                envelope,
                plan,
                safe_mode=safe_mode,
                automation_enabled=automation_enabled,
                allow_network=allow_network,
                outbound_enabled=outbound_enabled,
            )
            LOGGER.info(
                "worker.processed",
                extra={
                    "event_id": envelope.event_id,
                    "conversation_id": envelope.conversation_id,
                    "safe_mode": plan.safe_mode,
                    "automation_enabled": plan.automation_enabled,
                    "mode": plan.mode,
                    "actions": [a.get("type") for a in plan.actions],
                    "dry_run": execution.dry_run,
                    "outbound_sent": outbound_result.get("sent"),
                    "outbound_reason": outbound_result.get("reason"),
                },
            )
        except ClientError as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if code == "ConditionalCheckFailedException":
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


def _maybe_execute_outbound_reply(
    envelope: EventEnvelope,
    plan: ActionPlan,
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
) -> Dict[str, Any]:
    try:
        routing_result = execute_routing_tags(
            envelope,
            plan,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
            allow_network=allow_network,
            outbound_enabled=outbound_enabled,
        )
        reply_result = execute_order_status_reply(
            envelope,
            plan,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
            allow_network=allow_network,
            outbound_enabled=outbound_enabled,
        )
        combined = dict(reply_result)
        combined["routing_tags"] = routing_result
        return combined
    except Exception:
        LOGGER.exception(
            "worker.outbound_unexpected_failure",
            extra={"event_id": envelope.event_id, "conversation_id": envelope.conversation_id},
        )
        return {"sent": False, "reason": "exception"}


def _persist_idempotency(
    envelope: EventEnvelope, plan: ActionPlan
) -> Dict[str, Any]:
    event_id = str(envelope.event_id or f"evt:{int(time.time() * 1000)}")
    received_at = envelope.received_at or datetime.now(timezone.utc).isoformat()
    payload = envelope.payload or {}
    payload_excerpt = _truncate_payload(payload)
    conversation_id = _safe_str(envelope.conversation_id or envelope.group_id or "unknown")
    source_message_id = _safe_str(envelope.message_id or envelope.dedupe_id)
    expires_at = _now_epoch_seconds() + max(IDEMPOTENCY_TTL_SECONDS, 0)

    item: Dict[str, Any] = {
        "event_id": event_id,
        "conversation_id": conversation_id or "unknown",
        "received_at": received_at,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_processed_at": datetime.now(timezone.utc).isoformat(),
        "safe_mode": plan.safe_mode,
        "automation_enabled": plan.automation_enabled,
        "mode": plan.mode,
        "source": envelope.source or "richpanel_http_target",
        "payload_excerpt": payload_excerpt,
        "expires_at": expires_at,
        "status": "processed",
    }

    if source_message_id:
        item["source_message_id"] = source_message_id
    intent = payload.get("intent")
    if intent:
        item["intent"] = str(intent)

    item = _ddb_sanitize(item)
    _table(IDEMPOTENCY_TABLE_NAME).put_item(
        Item=item,
        ConditionExpression="attribute_not_exists(event_id)",
    )

    return {"conversation_id": conversation_id, "mode": plan.mode}


def _execute_and_record(envelope: EventEnvelope, plan: ActionPlan) -> ExecutionResult:
    def _state_writer(record: Dict[str, Any]) -> None:
        if not CONVERSATION_STATE_TABLE_NAME:
            return
        item = dict(record)
        item["expires_at"] = _now_epoch_seconds() + max(CONVERSATION_STATE_TTL_SECONDS, 0)
        item = _ddb_sanitize(item)
        _table(CONVERSATION_STATE_TABLE_NAME).put_item(Item=item)

    def _audit_writer(record: Dict[str, Any]) -> None:
        if not AUDIT_TRAIL_TABLE_NAME:
            return
        item = dict(record)
        recorded_at = str(record.get("recorded_at") or datetime.now(timezone.utc).isoformat())
        event_id = str(record.get("event_id") or envelope.event_id)
        item["ts_action_id"] = f"{recorded_at}#{event_id}"
        item["expires_at"] = _now_epoch_seconds() + max(AUDIT_TRAIL_TTL_SECONDS, 0)
        item = _ddb_sanitize(item)
        _table(AUDIT_TRAIL_TABLE_NAME).put_item(Item=item)

    return execute_plan(
        envelope,
        plan,
        dry_run=True,
        state_writer=_state_writer,
        audit_writer=_audit_writer,
    )


def _truncate_payload(value: Any) -> str:
    serialized = value
    if not isinstance(value, str):
        try:
            serialized = json.dumps(value)
        except (TypeError, ValueError):
            serialized = str(value)
    return (serialized or "")[:2000]


def _safe_str(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _now_epoch_seconds() -> int:
    return int(time.time())


def _load_kill_switches() -> tuple[bool, bool]:
    now = time.time()
    if now < _FLAG_CACHE.get("expires_at", 0):
        return _FLAG_CACHE["safe_mode"], _FLAG_CACHE["automation_enabled"]

    if boto3 is None:
        LOGGER.info(
            "worker.flags_offline_default",
            extra={
                "safe_mode": _FLAG_CACHE["safe_mode"],
                "automation_enabled": _FLAG_CACHE["automation_enabled"],
            },
        )
        _FLAG_CACHE["expires_at"] = now + FLAG_CACHE_TTL_SECONDS
        return _FLAG_CACHE["safe_mode"], _FLAG_CACHE["automation_enabled"]

    try:
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
    except Exception:
        LOGGER.exception("worker.flag_load_failed")
        safe_mode = True
        automation_enabled = False

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


def _ddb_sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _ddb_sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_ddb_sanitize(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_ddb_sanitize(v) for v in value)
    if isinstance(value, set):
        return {_ddb_sanitize(v) for v in value}
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return Decimal(str(value))
    return value


def _table(name: str):
    if not name:
        raise RuntimeError("table name is required")
    if name in _TABLE_CACHE:
        return _TABLE_CACHE[name]
    _TABLE_CACHE[name] = _dynamodb_resource().Table(name)
    return _TABLE_CACHE[name]


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
            class _InMemoryTable:
                def __init__(self):
                    self.items: List[Dict[str, Any]] = []

                def put_item(self, Item: Dict[str, Any], ConditionExpression: Optional[str] = None):
                    # No-op for conditional expressions in offline mode; we only need deterministic behavior.
                    self.items.append(Item)
                    return {"ResponseMetadata": {"HTTPStatusCode": 200}}

            class _InMemoryDynamo:
                def __init__(self):
                    self.tables: Dict[str, _InMemoryTable] = {}

                def Table(self, name: str) -> _InMemoryTable:  # type: ignore
                    if name not in self.tables:
                        self.tables[name] = _InMemoryTable()
                    return self.tables[name]

            _DDB_RESOURCE = _InMemoryDynamo()
        else:
            _DDB_RESOURCE = boto3.resource("dynamodb")
    return _DDB_RESOURCE

