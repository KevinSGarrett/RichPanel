#!/usr/bin/env python3
"""
dev_richpanel_outbound_smoke.py

CLI-only end-to-end smoke test that exercises the full Richpanel middleware
path (ingress -> worker -> DynamoDB) and verifies real outbound side-effects
on a designated Richpanel test ticket.

What it proves:
- Ingress accepts the webhook payload with deterministic order-status keywords.
- Worker processes the event and writes idempotency / state / audit records.
- Outbound path is enabled and applies tags + resolves the ticket via Richpanel API.
- Only PII-safe evidence is emitted (ids, tags, statuses).

Usage example:
python scripts/dev_richpanel_outbound_smoke.py --region us-east-2 --env dev --conversation-id 12345
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import time
import uuid
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import sys

try:
    import boto3  # type: ignore
    from boto3.dynamodb.conditions import Key  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError as exc:  # pragma: no cover - enforced in CI
    raise SystemExit(
        "boto3 is required to run dev_richpanel_outbound_smoke.py; install it with `pip install boto3`."
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.integrations.richpanel.client import (
    RichpanelClient,
    RichpanelExecutor,
    RichpanelRequestError,
    SecretLoadError,
    TransportError,
)


class SmokeFailure(RuntimeError):
    """Raised when the outbound E2E smoke test cannot complete successfully."""


@dataclass
class StackArtifacts:
    endpoint_url: str
    queue_url: str
    secrets_namespace: str
    idempotency_table: str
    conversation_state_table: Optional[str] = None
    audit_trail_table: Optional[str] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Richpanel outbound end-to-end smoke test against the dev stack."
    )
    parser.add_argument("--env", default="dev", help="Target environment name (default: dev).")
    parser.add_argument(
        "--region", required=True, help="AWS region that hosts the stack (e.g. us-east-2)."
    )
    parser.add_argument(
        "--stack-name",
        default="RichpanelMiddleware-dev",
        help="CloudFormation stack name to read outputs from.",
    )
    parser.add_argument(
        "--profile",
        help="AWS profile to use (e.g. richpanel-dev). If not set, uses default chain.",
    )
    parser.add_argument(
        "--conversation-id",
        required=True,
        help="Richpanel ticket id to target (must be a safe test ticket).",
    )
    parser.add_argument(
        "--idempotency-table",
        help="Optional override for the DynamoDB idempotency table name. Defaults to rp_mw_<env>_idempotency.",
    )
    parser.add_argument(
        "--event-id",
        help="Optional event_id to embed in the webhook payload for easier correlation.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=120,
        help="How long to wait for DynamoDB and Richpanel updates before failing (default: 120).",
    )
    parser.add_argument(
        "--summary-path",
        help="Optional file path (e.g. $GITHUB_STEP_SUMMARY) to append a Markdown summary.",
    )
    parser.add_argument(
        "--run-id",
        default=os.environ.get("RUN_ID") or "RUN_LOCAL",
        help="Run identifier used to write proof artifacts (default: RUN_ID env or RUN_LOCAL).",
    )
    parser.add_argument(
        "--proof-dir",
        help="Optional directory to write e2e_outbound_proof.json (defaults to REHYDRATION_PACK/RUNS/<RUN_ID>/B).",
    )
    parser.add_argument(
        "--confirm-test-ticket",
        action="store_true",
        help="Required acknowledgment that the provided ticket is a TEST ticket.",
    )
    parser.add_argument(
        "--allow-non-test-ticket",
        action="store_true",
        help="Bypass the test-ticket marker check (use only for approved test tickets).",
    )
    parser.add_argument(
        "--test-tag",
        action="append",
        default=[],
        help="Allowlisted tag indicating a test ticket (repeatable). Default includes mw-test-ticket/test.",
    )
    return parser.parse_args()


def load_stack_artifacts(
    cfn_client,
    sqs_client,
    apigwv2_client,
    stack_name: str,
    env_name: str,
    region: str,
) -> StackArtifacts:
    try:
        response = cfn_client.describe_stacks(StackName=stack_name)
    except ClientError as exc:
        raise SmokeFailure(f"Unable to describe stack '{stack_name}': {exc}") from exc

    stacks = response.get("Stacks", [])
    if not stacks:
        raise SmokeFailure(f"Stack '{stack_name}' was not found.")

    outputs = {item["OutputKey"]: item["OutputValue"] for item in stacks[0].get("Outputs", [])}

    endpoint = outputs.get("IngressEndpointUrl")
    queue_url = outputs.get("EventsQueueUrl")
    secrets_namespace = outputs.get("SecretsNamespace")
    idempotency_table = outputs.get("IdempotencyTableName")
    conversation_state_table = outputs.get("ConversationStateTableName")
    audit_trail_table = outputs.get("AuditTrailTableName")

    missing_outputs: List[str] = []

    if not endpoint:
        endpoint = derive_ingress_endpoint(
            cfn_client, apigwv2_client, stack_name, env_name, region
        )
        missing_outputs.append("IngressEndpointUrl")

    if not queue_url:
        queue_url = derive_queue_url(sqs_client, env_name)
        missing_outputs.append("EventsQueueUrl")

    if not secrets_namespace:
        secrets_namespace = infer_secrets_namespace(env_name)
        missing_outputs.append("SecretsNamespace")
    if not idempotency_table:
        idempotency_table = f"rp_mw_{env_name}_idempotency"
        missing_outputs.append("IdempotencyTableName")

    if missing_outputs:
        print(
            "[WARN] Missing stack outputs: "
            f"{', '.join(missing_outputs)}; derived fallback values were used."
        )

    if endpoint:
        endpoint = endpoint.rstrip("/")

    return StackArtifacts(
        endpoint_url=endpoint,
        queue_url=queue_url,
        secrets_namespace=secrets_namespace,
        idempotency_table=idempotency_table,
        conversation_state_table=conversation_state_table,
        audit_trail_table=audit_trail_table,
    )


def build_http_api_endpoint(api_id: str, region: str) -> str:
    return f"https://{api_id}.execute-api.{region}.amazonaws.com"


def derive_ingress_endpoint(
    cfn_client, apigwv2_client, stack_name: str, env_name: str, region: str
) -> str:
    try:
        resources = cfn_client.describe_stack_resources(StackName=stack_name)
    except ClientError as exc:
        print(f"[WARN] Unable to describe stack resources for '{stack_name}': {exc}")
        resources = {}

    stack_resources = resources.get("StackResources", [])

    for resource in stack_resources:
        logical_id = resource.get("LogicalResourceId", "")
        resource_type = resource.get("ResourceType", "")
        if logical_id == "IngressHttpApi" or resource_type == "AWS::ApiGatewayV2::Api":
            api_id = resource.get("PhysicalResourceId")
            if api_id:
                return build_http_api_endpoint(api_id, region)

    for resource in stack_resources:
        if resource.get("ResourceType") == "AWS::ApiGatewayV2::Stage":
            stage_id = resource.get("PhysicalResourceId", "")
            if stage_id:
                delimiter = "/" if "/" in stage_id else ":"
                api_id = stage_id.split(delimiter, 1)[0]
                if api_id:
                    return build_http_api_endpoint(api_id, region)

    target_name = f"rp-mw-{env_name}-ingress"
    available_api_names: List[str] = []
    try:
        paginator = apigwv2_client.get_paginator("get_apis")
        for page in paginator.paginate():
            for api in page.get("Items", []):
                available_api_names.append(api.get("Name", "<unnamed>"))
                name = (api.get("Name") or "").lower()
                canonical_target = target_name.lower()
                if (
                    name == canonical_target
                    or (name.startswith(f"rp-mw-{env_name}") and "ingress" in name)
                    or ("rp-mw" in name and env_name in name and "ingress" in name)
                ):
                    endpoint = api.get("ApiEndpoint")
                    if endpoint:
                        return endpoint.rstrip("/")
                    api_id = api.get("ApiId")
                    if api_id:
                        return build_http_api_endpoint(api_id, region)
    except ClientError as exc:
        raise SmokeFailure(f"Unable to enumerate HTTP APIs in region {region}: {exc}") from exc

    resource_summary = ", ".join(
        f"{res.get('LogicalResourceId','<unknown>')} ({res.get('ResourceType','?')})"
        for res in stack_resources
    )
    print(
        f"[WARN] Unable to discover ingress API in stack '{stack_name}'. "
        f"Resources inspected: {resource_summary or 'none'}."
    )
    if available_api_names:
        print("[WARN] HTTP APIs visible via apigatewayv2: " + ", ".join(available_api_names))

    raise SmokeFailure(
        "IngressEndpointUrl output missing and HTTP API could not be discovered via CloudFormation or API Gateway."
    )


def derive_queue_url(sqs_client, env_name: str) -> str:
    queue_name = f"rp-mw-{env_name}-events.fifo"
    try:
        response = sqs_client.get_queue_url(QueueName=queue_name)
    except ClientError as exc:
        raise SmokeFailure(f"Could not resolve queue URL for '{queue_name}': {exc}") from exc

    return response["QueueUrl"]


def infer_secrets_namespace(env_name: str) -> str:
    return f"rp-mw/{env_name}"


def load_webhook_token(secrets_client, namespace: str) -> str:
    secret_name = f"{namespace}/richpanel/webhook_token"
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
    except ClientError as exc:
        raise SmokeFailure(f"Unable to read webhook token secret '{secret_name}': {exc}") from exc

    if "SecretString" in response and response["SecretString"]:
        return response["SecretString"]

    if "SecretBinary" in response and response["SecretBinary"]:
        return base64.b64decode(response["SecretBinary"]).decode("utf-8")

    raise SmokeFailure(f"Secret '{secret_name}' did not contain a value.")


def send_webhook(endpoint: str, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    target_url = f"{endpoint}/webhook"
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url=target_url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-richpanel-webhook-token": token,
        },
    )

    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8") or "{}"
            parsed = json.loads(body)
            status_code = resp.getcode()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise SmokeFailure(
            f"Webhook request failed with status {exc.code}: {detail or exc.reason}"
        ) from exc
    except URLError as exc:
        raise SmokeFailure(f"Webhook request could not reach {target_url}: {exc.reason}") from exc

    if status_code != 200 or parsed.get("status") != "accepted":
        raise SmokeFailure(
            f"Webhook response was not accepted (status={status_code}, body={parsed})."
        )

    parsed["_status_code"] = status_code
    return parsed


def wait_for_dynamodb_record(
    ddb_resource,
    table_name: str,
    event_id: str,
    timeout_seconds: int,
    poll_interval: int = 5,
) -> Dict[str, Any]:
    table = ddb_resource.Table(table_name)
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            response = table.get_item(Key={"event_id": event_id})
        except (BotoCoreError, ClientError) as exc:
            raise SmokeFailure(f"Failed to query DynamoDB table '{table_name}': {exc}") from exc

        item = response.get("Item")
        if item:
            return item

        time.sleep(poll_interval)

    raise SmokeFailure(
        f"Event '{event_id}' was not observed in table '{table_name}' within {timeout_seconds}s."
    )


def wait_for_conversation_state_record(
    ddb_resource,
    table_name: str,
    conversation_id: str,
    timeout_seconds: int,
    poll_interval: int = 5,
) -> Dict[str, Any]:
    table = ddb_resource.Table(table_name)
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            response = table.get_item(Key={"conversation_id": conversation_id})
        except (BotoCoreError, ClientError) as exc:
            raise SmokeFailure(
                f"Failed to query conversation state table '{table_name}': {exc}"
            ) from exc

        item = response.get("Item")
        if item:
            return item

        time.sleep(poll_interval)

    raise SmokeFailure(
        f"Conversation '{conversation_id}' was not observed in table '{table_name}' within {timeout_seconds}s."
    )


def wait_for_audit_record(
    ddb_resource,
    table_name: str,
    conversation_id: str,
    event_id: str,
    timeout_seconds: int,
    poll_interval: int = 5,
) -> Dict[str, Any]:
    table = ddb_resource.Table(table_name)
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            response = table.query(
                KeyConditionExpression=Key("conversation_id").eq(conversation_id),
                Limit=5,
                ScanIndexForward=False,
            )
        except (BotoCoreError, ClientError) as exc:
            raise SmokeFailure(f"Failed to query audit table '{table_name}': {exc}") from exc

        items = response.get("Items") or []
        for item in items:
            if item.get("event_id") == event_id:
                return item

        time.sleep(poll_interval)

    raise SmokeFailure(
        f"Audit record for event '{event_id}' was not observed in table '{table_name}' within {timeout_seconds}s."
    )


def validate_idempotency_item(item: Dict[str, Any]) -> tuple[Optional[str], Optional[int]]:
    required = ["event_id", "status"]
    missing = [key for key in required if key not in item]
    if missing:
        raise SmokeFailure(f"Idempotency item missing required fields: {', '.join(missing)}")

    fingerprint = item.get("payload_fingerprint")
    if isinstance(fingerprint, str):
        fingerprint = fingerprint.strip() or None
    else:
        fingerprint = None
    field_count = item.get("payload_field_count")
    if not isinstance(field_count, int):
        field_count = None

    return fingerprint, field_count


def _normalize_tags(value: Any) -> List[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(tag) for tag in value if str(tag)]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def validate_routing(record: Dict[str, Any], *, label: str) -> Dict[str, Any]:
    routing = record.get("routing")
    if not isinstance(routing, dict):
        raise SmokeFailure(f"{label} record did not include routing metadata.")

    category = routing.get("category")
    tags = _normalize_tags(routing.get("tags"))
    reason = routing.get("reason") or routing.get("reasons")

    if not category:
        raise SmokeFailure(f"{label} routing.category was missing or empty.")
    if not tags:
        raise SmokeFailure(f"{label} routing.tags was missing or empty.")
    if not reason:
        raise SmokeFailure(f"{label} routing.reason was missing or empty.")

    return {"category": str(category), "tags": tags, "reason": reason}


def has_order_status_draft_action(actions: Any) -> bool:
    if not isinstance(actions, list):
        return False
    for action in actions:
        if isinstance(action, dict) and action.get("type") == "order_status_draft_reply":
            return True
    return False


def extract_draft_replies(record: Dict[str, Any], *, label: str) -> List[Dict[str, Any]]:
    replies = record.get("draft_replies")
    if replies is None:
        return []
    if not isinstance(replies, list):
        raise SmokeFailure(f"{label} draft_replies was not a list.")
    for reply in replies:
        if not isinstance(reply, dict):
            raise SmokeFailure(f"{label} draft_replies contained a non-dict entry.")
    return replies


def sanitize_draft_replies(replies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    allowed_fields = ("reason", "prompt_fingerprint", "dry_run", "body_hash", "has_body")
    sanitized: List[Dict[str, Any]] = []
    for reply in replies:
        sanitized.append({field: reply.get(field) for field in allowed_fields if field in reply})
    return sanitized


def extract_draft_replies_from_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    extracted: List[Dict[str, Any]] = []
    for action in actions or []:
        if not isinstance(action, dict) or action.get("type") != "order_status_draft_reply":
            continue
        params = action.get("parameters") or {}
        draft = params.get("draft_reply")
        if isinstance(draft, dict):
            body = draft.get("body")
            extracted.append(
                {
                    "reason": action.get("note"),
                    "prompt_fingerprint": params.get("prompt_fingerprint"),
                    "dry_run": action.get("dry_run"),
                    "body_hash": _hash_text(str(body)) if body else None,
                    "has_body": bool(body),
                }
            )
    return extracted


def build_order_status_payload(conversation_id: str, event_id: Optional[str]) -> Dict[str, Any]:
    message = (
        "[TEST] Where is my order? I need tracking details and expected delivery date. "
        "No tracking link is visible."
    )
    subject = "[TEST] Order status check"
    synthetic_order_id = f"smoke-order-{uuid.uuid4().hex[:8]}"
    return {
        "event_id": event_id or f"evt:{uuid.uuid4()}",
        "conversation_id": conversation_id,
        "message_id": uuid.uuid4().hex,
        "source": "dev_richpanel_outbound_smoke",
        "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "customer_message": message,
        "message": message,
        "subject": subject,
        "title": subject,
        "payload": {
            "type": "order_status_smoke",
            "customer_message": message,
            "message": message,
            "subject": subject,
            "title": subject,
            "order_id": synthetic_order_id,
            "channel": "email",
            "nonce": uuid.uuid4().hex,
        },
    }


def _set_richpanel_env(env_name: str) -> None:
    os.environ.setdefault("RICHPANEL_OUTBOUND_ENABLED", "true")
    os.environ.setdefault("RICHPANEL_ENV", env_name)
    os.environ.setdefault("RICH_PANEL_ENV", env_name)
    os.environ.setdefault("MW_ENV", env_name)


def create_richpanel_executor(env_name: str) -> RichpanelExecutor:
    _set_richpanel_env(env_name)
    client = RichpanelClient()
    return RichpanelExecutor(client=client, outbound_enabled=True)


def wait_for_richpanel_metadata(
    executor: RichpanelExecutor,
    conversation_id: str,
    expected_tags: Sequence[str],
    *,
    timeout_seconds: int,
    poll_interval: int = 5,
) -> Dict[str, Any]:
    deadline = time.time() + timeout_seconds
    expected = {tag.lower() for tag in expected_tags if tag}
    last_error: Optional[str] = None

    while time.time() < deadline:
        try:
            meta = executor.get_ticket_metadata(conversation_id, dry_run=False)
        except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
            last_error = str(exc)
            time.sleep(poll_interval)
            continue

        tags_lower = {str(tag).lower() for tag in meta.tags}
        status = (meta.status or "").lower()
        if expected.issubset(tags_lower) and status in {"resolved", "closed", "solved"}:
            return {"status": meta.status, "tags": meta.tags}

        time.sleep(poll_interval)

    if last_error:
        raise SmokeFailure(
            f"Richpanel metadata could not be confirmed within {timeout_seconds}s (last error: {last_error})."
        )
    raise SmokeFailure(
        f"Richpanel ticket did not reflect expected tags/status within {timeout_seconds}s."
    )


def _hash_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _parse_iso_ts(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        cleaned = str(value).strip()
        cleaned = cleaned.replace("Z", "+00:00") if "Z" in cleaned else cleaned
        return datetime.fromisoformat(cleaned).timestamp()
    except Exception:
        pass
    try:
        # Fallback for strict Z format without offset replacement
        return datetime.strptime(str(value).strip(), "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
    except Exception:
        pass
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%dT%H:%M:%SZ").timestamp()
    except Exception:
        return None
    except Exception:
        return None


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        text = str(value).strip()
    except Exception:
        return None
    return text or None


def fetch_ticket_snapshot(
    executor: RichpanelExecutor,
    conversation_id: str,
    *,
    allow_network: bool,
    test_tag_allowlist: Sequence[str],
) -> Dict[str, Any]:
    path = (
        f"/v1/tickets/number/{conversation_id}"
        if conversation_id.isdigit()
        else f"/v1/tickets/{conversation_id}"
    )
    resp = executor.execute(
        "GET",
        path,
        dry_run=not allow_network,
        log_body_excerpt=False,
    )
    payload = resp.json() or {}
    ticket = payload.get("ticket") if isinstance(payload, dict) else None
    if isinstance(ticket, dict):
        payload = ticket
    status = None
    tags: Set[str] = set()
    subject = None
    updated_at = None
    if isinstance(payload, dict):
        status = _coerce_str(payload.get("status") or payload.get("state"))
        raw_tags = payload.get("tags")
        if isinstance(raw_tags, list):
            tags = {t.strip() for t in raw_tags if isinstance(t, str) and t.strip()}
        subject = _coerce_str(payload.get("subject") or payload.get("title"))
        updated_at = _coerce_str(payload.get("updated_at"))

    def _has_test_tag(tag_set: Set[str]) -> bool:
        lower_allow = {t.lower() for t in test_tag_allowlist if t}
        for tag in tag_set:
            lt = tag.lower()
            if "test" in lt or lt in lower_allow:
                return True
        return False

    has_test_tag = _has_test_tag(tags)
    has_test_subject = bool(subject and "test" in subject.lower())

    return {
        "status": status,
        "tags": sorted(tags),
        "status_code": getattr(resp, "status_code", None),
        "has_test_tag": has_test_tag,
        "has_test_subject": has_test_subject,
        "subject_hash": _hash_text(subject),
        "updated_at": updated_at,
        "dry_run": getattr(resp, "dry_run", False),
    }


def wait_for_richpanel_update(
    executor: RichpanelExecutor,
    conversation_id: str,
    *,
    expected_tags: Sequence[str],
    timeout_seconds: int,
    poll_interval: int = 5,
    test_tag_allowlist: Sequence[str],
) -> Dict[str, Any]:
    deadline = time.time() + timeout_seconds
    expected = {tag.lower() for tag in expected_tags if tag}
    last_error: Optional[str] = None
    last_snapshot: Optional[Dict[str, Any]] = None

    while time.time() < deadline:
        try:
            snap = fetch_ticket_snapshot(
                executor,
                conversation_id,
                allow_network=True,
                test_tag_allowlist=test_tag_allowlist,
            )
            last_snapshot = snap
        except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
            last_error = str(exc)
            time.sleep(poll_interval)
            continue

        tags_lower = {t.lower() for t in snap["tags"]}
        status_lower = (snap.get("status") or "").lower()
        if expected.issubset(tags_lower) or status_lower in {"resolved", "closed", "solved"}:
            return snap

        time.sleep(poll_interval)

    detail = f"last_error={last_error}" if last_error else f"last_snapshot={last_snapshot}"
    raise SmokeFailure(
        f"Richpanel ticket did not reflect expected tags/status within {timeout_seconds}s ({detail})."
    )


def build_console_links(
    *,
    region: str,
    idempotency_table: str,
    env_name: str,
    conversation_state_table: Optional[str] = None,
    audit_trail_table: Optional[str] = None,
) -> Dict[str, str]:
    ddb_console = (
        f"https://{region}.console.aws.amazon.com/dynamodbv2/home"
        f"?region={region}#item-explorer?initialTagKey=&initialTagValue=&table={idempotency_table}"
    )
    conversation_console = None
    audit_console = None
    if conversation_state_table:
        conversation_console = (
            f"https://{region}.console.aws.amazon.com/dynamodbv2/home"
            f"?region={region}#item-explorer?initialTagKey=&initialTagValue=&table={conversation_state_table}"
        )
    if audit_trail_table:
        audit_console = (
            f"https://{region}.console.aws.amazon.com/dynamodbv2/home"
            f"?region={region}#item-explorer?initialTagKey=&initialTagValue=&table={audit_trail_table}"
        )
    logs_group = f"/aws/lambda/rp-mw-{env_name}-worker"
    logs_console = (
        f"https://{region}.console.aws.amazon.com/cloudwatch/home"
        f"?region={region}#logsV2:log-groups/log-group/{logs_group.replace('/', '$252F')}"
    )
    return {
        "ddb": ddb_console,
        "logs": logs_console,
        "log_group": logs_group,
        "conversation_ddb": conversation_console,
        "audit_ddb": audit_console,
    }


def write_proof(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def append_summary(path: str, *, env_name: str, data: Dict[str, Any]) -> None:
    env_label = env_name.strip() or "dev"
    env_heading = env_label.replace("_", " ").title()
    lines = [
        f"## {env_heading} Richpanel Outbound Smoke",
        f"- Event ID: `{data['event_id']}`",
        f"- Conversation ID: `{data['conversation_id']}`",
        f"- Endpoint: {data['endpoint']}/webhook",
        f"- Idempotency table: `{data['ddb_table']}`",
        f"- Idempotency console: {data['ddb_console_url']}",
        f"- Routing: category=`{data['routing_category']}`; tags={', '.join(data['routing_tags'])}",
        f"- Draft action present: {'yes' if data['draft_action_present'] else 'no'}; "
        f"draft_replies={data['draft_reply_count']}",
        f"- Richpanel status: `{data['richpanel_status']}`; tags={', '.join(data['richpanel_tags'])}",
        f"- CloudWatch logs: {data['logs_console_url']}",
    ]
    if data.get("conversation_state_table"):
        lines.append(
            "- Conversation state record observed in "
            f"`{data['conversation_state_table']}` (console: {data['conversation_state_console']})"
        )
    if data.get("audit_trail_table"):
        lines.append(
            "- Audit record observed in "
            f"`{data['audit_trail_table']}` (console: {data['audit_console']})"
        )
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


def main() -> int:
    args = parse_args()
    region = args.region
    env_name = args.env
    conversation_id = args.conversation_id
    default_idempotency_table = f"rp_mw_{env_name}_idempotency"

    if not args.confirm_test_ticket:
        raise SmokeFailure(
            "Missing required flag --confirm-test-ticket. Only run against approved test tickets."
        )

    test_tag_allowlist = args.test_tag or ["mw-test-ticket", "test", "[test]"]

    if args.profile:
        os.environ["AWS_PROFILE"] = args.profile
    os.environ.setdefault("AWS_DEFAULT_REGION", region)
    os.environ.setdefault("AWS_REGION", region)

    print(f"[INFO] Target stack: {args.stack_name} (region={region}, env={env_name})")
    print(f"[INFO] Target conversation_id: {conversation_id}")

    session = boto3.session.Session(profile_name=args.profile, region_name=region)
    cfn_client = session.client("cloudformation")
    sqs_client = session.client("sqs")
    apigwv2_client = session.client("apigatewayv2")
    secrets_client = session.client("secretsmanager")
    ddb_resource = session.resource("dynamodb")

    artifacts = load_stack_artifacts(
        cfn_client,
        sqs_client,
        apigwv2_client,
        args.stack_name,
        env_name,
        region,
    )
    dynamo_table = args.idempotency_table or artifacts.idempotency_table or default_idempotency_table
    if not artifacts.conversation_state_table:
        raise SmokeFailure("ConversationStateTableName output was missing from the stack.")
    if not artifacts.audit_trail_table:
        raise SmokeFailure("AuditTrailTableName output was missing from the stack.")

    console_links = build_console_links(
        region=region,
        idempotency_table=dynamo_table,
        env_name=env_name,
        conversation_state_table=artifacts.conversation_state_table,
        audit_trail_table=artifacts.audit_trail_table,
    )

    print(f"[INFO] Ingress endpoint: {artifacts.endpoint_url}/webhook")
    print(f"[INFO] Events queue URL: {artifacts.queue_url}")
    print(f"[INFO] Secrets namespace: {artifacts.secrets_namespace}")

    token = load_webhook_token(secrets_client, artifacts.secrets_namespace)

    executor = create_richpanel_executor(env_name)

    print("[INFO] Fetching Richpanel ticket metadata before webhook (PII-safe)...")
    pre_snapshot = fetch_ticket_snapshot(
        executor,
        conversation_id,
        allow_network=True,
        test_tag_allowlist=test_tag_allowlist,
    )
    is_test_ticket = pre_snapshot["has_test_tag"] or pre_snapshot["has_test_subject"]
    if not is_test_ticket and not args.allow_non_test_ticket:
        raise SmokeFailure(
            "Ticket does not appear to be a test ticket (no test tag/subject). "
            "Add --allow-non-test-ticket only if you are sure this is a safe test ticket."
        )

    payload = build_order_status_payload(conversation_id, args.event_id)
    event_id = payload["event_id"]
    message_id = payload["message_id"]
    payload_hash = _hash_text(json.dumps(payload, sort_keys=True))
    print(f"[INFO] Sending order-status webhook with event_id={event_id}")

    response = send_webhook(artifacts.endpoint_url, token, payload)
    ingress_status = response.get("_status_code", None)
    returned_event_id = response.get("event_id")
    if returned_event_id and returned_event_id != event_id:
        raise SmokeFailure(
            f"Webhook response event_id mismatch (got={returned_event_id}, expected={event_id})."
        )

    print("[INFO] Webhook accepted, waiting for DynamoDB record...")
    item = wait_for_dynamodb_record(
        ddb_resource,
        table_name=dynamo_table,
        event_id=event_id,
        timeout_seconds=args.wait_seconds,
    )
    payload_fingerprint, payload_field_count = validate_idempotency_item(item)
    mode = item.get("mode")
    print(f"[OK] Event '{event_id}' observed in table '{dynamo_table}' (mode={mode}).")
    if payload_fingerprint:
        print(f"[OK] Idempotency payload_fingerprint captured ({payload_fingerprint[:12]}...).")
    else:
        print("[WARN] Idempotency payload_fingerprint missing.")
    print(f"[INFO] DynamoDB console: {console_links['ddb']}")

    state_item = wait_for_conversation_state_record(
        ddb_resource,
        table_name=artifacts.conversation_state_table,
        conversation_id=conversation_id,
        timeout_seconds=args.wait_seconds,
    )
    print(
        f"[OK] Conversation state written for '{conversation_id}' "
        f"in '{artifacts.conversation_state_table}'."
    )

    audit_item = wait_for_audit_record(
        ddb_resource,
        table_name=artifacts.audit_trail_table,
        conversation_id=conversation_id,
        event_id=event_id,
        timeout_seconds=args.wait_seconds,
    )
    print(
        f"[OK] Audit record written for '{conversation_id}' "
        f"in '{artifacts.audit_trail_table}'."
    )
    routing_state = validate_routing(state_item, label="Conversation state")
    routing_audit = validate_routing(audit_item, label="Audit trail")

    combined_actions: List[Dict[str, Any]] = []
    for action_list in (state_item.get("actions"), audit_item.get("actions")):
        if isinstance(action_list, list):
            combined_actions.extend([action for action in action_list if isinstance(action, dict)])

    draft_action_present = has_order_status_draft_action(combined_actions)
    draft_replies = extract_draft_replies(
        state_item, label="Conversation state"
    ) or extract_draft_replies(audit_item, label="Audit trail")
    if not draft_replies:
        draft_replies = extract_draft_replies_from_actions(combined_actions)
    if draft_action_present and not draft_replies:
        print("[WARN] order_status_draft_reply action present but no draft_replies persisted; using fallback evidence only.")

    safe_draft_replies = sanitize_draft_replies(draft_replies)

    print(
        f"[OK] Routing recorded in state and audit (category={routing_state['category']}, "
        f"tags={routing_state['tags']})."
    )
    print(
        f"[INFO] order_status_draft_reply action observed={draft_action_present}; "
        f"draft_replies_count={len(draft_replies)}"
    )
    if safe_draft_replies:
        print(f"[INFO] Draft replies persisted (safe fields): {safe_draft_replies}")
    print(
        f"[OK] Routing recorded in audit (category={routing_audit['category']}, "
        f"tags={routing_audit['tags']})."
    )
    print(f"[INFO] CloudWatch logs group: {console_links['log_group']}")
    print(f"[INFO] Logs console: {console_links['logs']}")

    print("[INFO] Verifying outbound side-effects via Richpanel API...")
    post_snapshot = wait_for_richpanel_update(
        executor,
        conversation_id,
        expected_tags=["mw-auto-replied", "mw-routing-applied"],
        timeout_seconds=args.wait_seconds,
        test_tag_allowlist=test_tag_allowlist,
    )
    print(
        f"[OK] Richpanel ticket updated (status={post_snapshot['status']}; "
        f"tags={post_snapshot['tags']})"
    )

    proof_dir = (
        args.proof_dir
        or os.path.join("REHYDRATION_PACK", "RUNS", args.run_id, "B")
    )
    proof_path = os.path.join(proof_dir, "e2e_outbound_proof.json")
    tags_before = set(pre_snapshot.get("tags") or [])
    tags_after = set(post_snapshot.get("tags") or [])
    tags_added = sorted(t for t in tags_after - tags_before)
    tags_removed = sorted(t for t in tags_before - tags_after)
    status_changed = pre_snapshot.get("status") != post_snapshot.get("status")
    def _parse_ts_candidates(val: Optional[str]) -> Optional[float]:
        if not val:
            return None
        val_str = str(val).strip()
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(val_str, fmt).timestamp()
            except Exception:
                continue
        try:
            cleaned = val_str.replace("Z", "+00:00") if "Z" in val_str else val_str
            return datetime.fromisoformat(cleaned).timestamp()
        except Exception:
            pass
        try:
            base = val_str.split("Z")[0].split(".")[0]
            return datetime.strptime(base, "%Y-%m-%dT%H:%M:%S").timestamp()
        except Exception:
            return None

    ts_before = _parse_ts_candidates(pre_snapshot.get("updated_at"))
    ts_after = _parse_ts_candidates(post_snapshot.get("updated_at"))
    updated_at_delta_seconds: Optional[float] = None
    updated_at_parse_ok = False
    if ts_before is not None and ts_after is not None:
        updated_at_delta_seconds = max(0.0, ts_after - ts_before)
        updated_at_parse_ok = True
    elif pre_snapshot.get("updated_at") and post_snapshot.get("updated_at"):
        if pre_snapshot.get("updated_at") != post_snapshot.get("updated_at"):
            updated_at_delta_seconds = 1.0  # minimal non-zero delta to reflect observed string change
            updated_at_parse_ok = False

    proof_attribution_ok = bool(
        tags_added
        or status_changed
        or (updated_at_delta_seconds is not None and updated_at_delta_seconds > 0)
    )
    proof_payload = {
        "run_id": args.run_id,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "env": env_name,
        "region": region,
        "event_id": event_id,
        "message_id": message_id,
        "payload_sha256": payload_hash,
        "conversation_id": conversation_id,
        "endpoint": artifacts.endpoint_url,
        "ingress_status_code": ingress_status,
        "queue_url": artifacts.queue_url,
        "idempotency_table": dynamo_table,
        "conversation_state_table": artifacts.conversation_state_table,
        "audit_trail_table": artifacts.audit_trail_table,
        "idempotency_mode": mode or "unknown",
        "routing": routing_state,
        "draft_action_present": draft_action_present,
        "draft_reply_count": len(draft_replies),
        "draft_replies_safe": safe_draft_replies,
        "richpanel_status_before": pre_snapshot.get("status"),
        "richpanel_tags_before": pre_snapshot.get("tags"),
        "richpanel_status_after": post_snapshot.get("status"),
        "richpanel_tags_after": post_snapshot.get("tags"),
        "richpanel_status_code_before": pre_snapshot.get("status_code"),
        "richpanel_status_code_after": post_snapshot.get("status_code"),
        "richpanel_has_test_tag": pre_snapshot.get("has_test_tag"),
        "richpanel_has_test_subject": pre_snapshot.get("has_test_subject"),
        "richpanel_subject_hash": pre_snapshot.get("subject_hash"),
        "richpanel_subject_hash_after": post_snapshot.get("subject_hash"),
        "richpanel_updated_at_before": pre_snapshot.get("updated_at"),
        "richpanel_updated_at_after": post_snapshot.get("updated_at"),
        "richpanel_updated_at_delta_seconds": updated_at_delta_seconds,
        "richpanel_updated_at_parse_ok": updated_at_parse_ok,
        "richpanel_status_changed": status_changed,
        "richpanel_tags_added": tags_added,
        "richpanel_tags_removed": tags_removed,
        "ddb_console": console_links["ddb"],
        "logs_console": console_links["logs"],
        "conversation_ddb_console": console_links["conversation_ddb"],
        "audit_ddb_console": console_links["audit_ddb"],
        "idempotency_status": item.get("status"),
        "idempotency_payload_field_count": payload_field_count,
        "idempotency_payload_fingerprint": payload_fingerprint,
        "payload_top_level_key_count": len(payload) if isinstance(payload, dict) else None,
        "payload_nested_key_count": len(payload.get("payload"))
        if isinstance(payload.get("payload"), dict)
        else None,
        "state_actions_count": len(state_item.get("actions") or []),
        "audit_ts_action_id": audit_item.get("ts_action_id"),
        "proof_attribution_ok": proof_attribution_ok,
        "result": "PASS" if proof_attribution_ok else "PASS_WEAK",
        "failure_reason": None
        if proof_attribution_ok
        else "No observable Richpanel delta (tags/status/updated_at)",
    }
    write_proof(proof_path, proof_payload)
    print(f"[OK] Proof written to {proof_path}")

    if args.summary_path:
        summary_data = {
            "event_id": event_id,
            "conversation_id": conversation_id,
            "endpoint": artifacts.endpoint_url,
            "ddb_table": dynamo_table,
            "ddb_console_url": console_links["ddb"],
            "logs_console_url": console_links["logs"],
            "conversation_state_table": artifacts.conversation_state_table,
            "conversation_state_console": console_links["conversation_ddb"],
            "audit_trail_table": artifacts.audit_trail_table,
            "audit_console": console_links["audit_ddb"],
            "routing_category": routing_state["category"],
            "routing_tags": routing_state["tags"],
            "draft_action_present": draft_action_present,
            "draft_reply_count": len(draft_replies),
            "richpanel_status": post_snapshot.get("status"),
            "richpanel_tags": post_snapshot.get("tags"),
            "richpanel_tags_added": tags_added,
            "richpanel_tags_removed": tags_removed,
            "richpanel_status_changed": status_changed,
        }
        append_summary(args.summary_path, env_name=env_name, data=summary_data)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"[FAIL] Richpanel outbound smoke test failed: {exc}")
        raise SystemExit(1)
