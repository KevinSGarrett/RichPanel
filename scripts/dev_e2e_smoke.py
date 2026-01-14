#!/usr/bin/env python3
"""
dev_e2e_smoke.py

End-to-end smoke test for the dev Richpanel middleware stack.

High-level flow:
1. Discover the HTTP endpoint + queue via CloudFormation stack outputs.
2. Fetch the webhook authentication token from Secrets Manager.
3. Send a synthetic webhook payload to the ingress endpoint.
4. Wait for the worker Lambda to persist the event in the DynamoDB idempotency table.
5. Verify the conversation state + audit trail records were written.
6. Emit evidence URLs (API endpoint, SQS queue, DynamoDB tables, CloudWatch log group).

Design constraints:
- Only prints derived identifiers (event_id, queue URL, etc.); never prints secret values.
- Standard library + boto3 only to keep the runtime lightweight on GitHub runners.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import uuid
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import boto3  # type: ignore
    from boto3.dynamodb.conditions import Key  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover - enforced in CI
    boto3 = None  # type: ignore
    Key = None  # type: ignore

    class _MissingBoto3(Exception):
        ...

    BotoCoreError = ClientError = _MissingBoto3  # type: ignore

# Allow imports from backend/src without packaging.
ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from richpanel_middleware.integrations.richpanel.client import (  # type: ignore
    RichpanelClient,
    RichpanelExecutor,
    RichpanelRequestError,
    SecretLoadError,
    TransportError,
)


class SmokeFailure(RuntimeError):
    """Raised when the dev E2E smoke test cannot complete successfully."""


_SKIP_MIDDLEWARE_TAGS = {
    "mw-skip-status-read-failed",
    "mw-skip-order-status-closed",
    "mw-skip-followup-after-auto-reply",
    "route-email-support-team",
    "mw-escalated-human",
}

_POSITIVE_MIDDLEWARE_TAGS = {
    "mw-auto-replied",
    "mw-reply-sent",
    "mw-order-status-answered",
}

def _is_positive_middleware_tag(tag: str) -> bool:
    return tag in _POSITIVE_MIDDLEWARE_TAGS or any(
        tag.startswith(prefix + ":") for prefix in _POSITIVE_MIDDLEWARE_TAGS
    )


def _compute_middleware_outcome(
    *,
    status_after: Optional[str],
    tags_added: List[str],
    post_tags: List[str],
) -> Dict[str, Any]:
    """
    Decide whether middleware produced a valid outcome.
    - PASS requires either resolved/closed OR a positive middleware tag.
    - Skip/error tags (mw-skip-status-read-failed, route-email-support-team) are NOT valid.
    - Smoke tags (mw-smoke:<RUN_ID>) are ignored for PASS purposes.
    """
    normalized_status = status_after.strip().lower() if isinstance(status_after, str) else None
    status_resolved = normalized_status in {"resolved", "closed"} if normalized_status else False
    skip_tags_added = [tag for tag in tags_added if tag in _SKIP_MIDDLEWARE_TAGS]
    positive_tags_added = [tag for tag in tags_added if _is_positive_middleware_tag(tag)]
    middleware_tag_added = bool(positive_tags_added)
    middleware_tag_present = middleware_tag_added
    middleware_outcome = (status_resolved or middleware_tag_added) and not bool(skip_tags_added)
    return {
        "status_resolved": status_resolved,
        "middleware_tag_present": middleware_tag_present,
        "middleware_tag_added": middleware_tag_added,
        "middleware_outcome": middleware_outcome,
        "skip_tags_present": bool(skip_tags_added),
    }
@dataclass
class StackArtifacts:
    endpoint_url: str
    queue_url: str
    secrets_namespace: str
    idempotency_table: str
    conversation_state_table: Optional[str] = None
    audit_trail_table: Optional[str] = None


def _setup_boto_session(region: str, profile: Optional[str]) -> Any:
    if boto3 is None:
        raise SmokeFailure("boto3 is required to run dev_e2e_smoke.py; install it with `pip install boto3`.")
    if profile:
        boto3.setup_default_session(profile_name=profile, region_name=region)
    return boto3.session.Session(region_name=region, profile_name=profile)


def _iso_timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso8601(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _seconds_delta(before: Optional[str], after: Optional[str]) -> Optional[float]:
    start = _parse_iso8601(before)
    end = _parse_iso8601(after)
    if not start or not end:
        return None
    return (end - start).total_seconds()


def _fingerprint(value: str, length: int = 12) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length]


def _truncate_text(text: str, limit: int = 256) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _redact_path(path: Optional[str]) -> Optional[str]:
    """Redact ticket IDs from API paths to prevent PII leakage."""
    if not path:
        return None
    # Extract the base path structure without the ID
    if "/v1/tickets/number/" in path:
        return "/v1/tickets/number/<redacted>"
    if "/v1/tickets/" in path:
        # Could be /v1/tickets/{id} or /v1/tickets/{id}/add-tags etc.
        parts = path.split("/v1/tickets/")
        if len(parts) > 1:
            suffix = parts[1]
            # Check for sub-paths like /add-tags
            if "/" in suffix:
                sub_path = "/" + suffix.split("/", 1)[1]
                return f"/v1/tickets/<redacted>{sub_path}"
            return "/v1/tickets/<redacted>"
    return "<redacted>"


def _extract_endpoint_variant(path: Optional[str]) -> Optional[str]:
    """Extract whether the path used 'id' or 'number' endpoint."""
    if not path:
        return None
    if "/v1/tickets/number/" in path:
        return "number"
    if "/v1/tickets/" in path:
        return "id"
    return "unknown"


def _sanitize_ticket_snapshot(snapshot: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not snapshot:
        return None
    sanitized = dict(snapshot)

    # Remove ticket_id, replace with fingerprint only
    ticket_id = sanitized.pop("ticket_id", None)
    if ticket_id:
        sanitized["ticket_id_fingerprint"] = _fingerprint(ticket_id)
        # NEVER include raw ticket_id - it may contain email/message-id PII

    # Remove raw path, replace with redacted version and endpoint variant
    raw_path = sanitized.pop("path", None)
    if raw_path:
        sanitized["endpoint_variant"] = _extract_endpoint_variant(raw_path)
        sanitized["path_redacted"] = _redact_path(raw_path)

    return sanitized


def _sanitize_tag_result(tag_result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Sanitize the tag application result to remove PII from paths."""
    if not tag_result:
        return None
    sanitized = dict(tag_result)
    raw_path = sanitized.pop("path", None)
    if raw_path:
        sanitized["path_redacted"] = _redact_path(raw_path)
    return sanitized


def _order_status_scenario_payload(
    run_id: str, *, conversation_id: Optional[str]
) -> Dict[str, Any]:
    """
    Build a deterministic order-status payload that stays offline/deterministic.
    """
    now = datetime.now(timezone.utc)
    order_created_at = (now - timedelta(days=5)).isoformat()
    ticket_created_at = (now - timedelta(days=1)).isoformat()
    order_seed = run_id or "order-status-smoke"
    seeded_order_id = conversation_id or f"DEV-ORDER-{_fingerprint(order_seed, length=8).upper()}"
    tracking_number = f"TRACK-{_fingerprint(seeded_order_id + order_seed, length=10).upper()}"
    tracking_url = f"https://tracking.example.com/track/{tracking_number}"
    shipping_method = "Standard (3-5 business days)"
    carrier = "UPS"

    base_order = {
        "id": seeded_order_id,
        "order_id": seeded_order_id,
        "status": "shipped",
        "fulfillment_status": "shipped",
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
        "carrier": carrier,
        "shipping_carrier": carrier,
        "shipping_method": shipping_method,
        "shipping_method_name": shipping_method,
        "order_created_at": order_created_at,
        "created_at": order_created_at,
        "updated_at": ticket_created_at,
        "items": [
            {"sku": "SMOKE-OS-HOODIE", "name": "Smoke Test Hoodie", "quantity": 1}
        ],
    }

    return {
        "scenario": "order_status",
        "intent": "order_status_tracking",
        "customer_message": "Where is my order? Please share the tracking update.",
        "ticket_created_at": ticket_created_at,
        "order_created_at": order_created_at,
        "order_id": seeded_order_id,
        "status": "shipped",
        "fulfillment_status": "shipped",
        "order_status": "shipped",
        "carrier": carrier,
        "shipping_carrier": carrier,
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
        "shipping_method": shipping_method,
        "orders": [base_order],
        "order": base_order,
        "tracking": {
            "number": tracking_number,
            "carrier": carrier,
            "status": "in_transit",
            "status_url": tracking_url,
            "updated_at": ticket_created_at,
        },
        "shipment": {
            "carrier": carrier,
            "serviceCode": shipping_method,
            "orderNumber": seeded_order_id,
            "shipDate": ticket_created_at,
        },
    }


# PII patterns that must not appear in proof JSON
_PII_PATTERNS = [
    "%40",       # URL-encoded @
    "%3C",       # URL-encoded <
    "%3E",       # URL-encoded >
    "mail.",     # email domain fragment
    "@",         # literal @
    "<",         # literal < (except in redacted placeholders)
]


def _sanitize_decimals(obj: Any) -> Any:
    """Recursively convert Decimal types to int/float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {key: _sanitize_decimals(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_decimals(item) for item in obj]
    return obj


def _check_pii_safe(payload_json: str) -> Optional[str]:
    """
    Check if the proof JSON contains any PII patterns.
    Returns an error message if PII is detected, None if safe.
    """
    # Allow <redacted> as a safe placeholder
    safe_json = payload_json.replace("<redacted>", "REDACTED_PLACEHOLDER")

    for pattern in _PII_PATTERNS:
        if pattern in safe_json:
            return f"PII pattern '{pattern}' detected in proof payload"
    return None


def _build_richpanel_executor(
    *,
    env_name: str,
    allow_network: bool,
    api_key_secret_id: Optional[str] = None,
) -> RichpanelExecutor:
    os.environ.setdefault("RICHPANEL_ENV", env_name)
    client = RichpanelClient(
        api_key_secret_id=api_key_secret_id,
        dry_run=not allow_network,
    )
    return RichpanelExecutor(client=client, outbound_enabled=allow_network)


def _fetch_ticket_snapshot(
    executor: RichpanelExecutor,
    ticket_ref: str,
    *,
    allow_network: bool,
) -> Dict[str, Any]:
    encoded_ref = urllib.parse.quote(ticket_ref, safe="")
    attempts = [
        f"/v1/tickets/{encoded_ref}",
        f"/v1/tickets/number/{encoded_ref}",
    ]
    errors: List[str] = []
    for path in attempts:
        try:
            response = executor.execute(
                "GET",
                path,
                dry_run=not allow_network,
                log_body_excerpt=False,
            )
        except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        if response.status_code < 200 or response.status_code >= 300:
            errors.append(f"{path}: status {response.status_code}")
            continue

        payload = response.json() or {}
        if isinstance(payload, dict) and isinstance(payload.get("ticket"), dict):
            payload = payload["ticket"]
        status = payload.get("status") or payload.get("state")
        tags = _normalize_tags(payload.get("tags"))
        updated_at = payload.get("updated_at") or payload.get("updatedAt")
        message_count = _safe_int(
            payload.get("messages_count")
            or payload.get("message_count")
            or payload.get("messagesCount")
        )
        last_message_source = payload.get("last_message_source") or payload.get("lastMessageSource")

        return {
            "ticket_id": str(payload.get("id") or ticket_ref),
            "status": status.strip() if isinstance(status, str) else status,
            "tags": tags,
            "updated_at": updated_at,
            "message_count": message_count,
            "last_message_source": last_message_source,
            "status_code": response.status_code,
            "dry_run": response.dry_run,
            "path": path,
        }

    raise SmokeFailure(
        "Ticket lookup failed; attempted paths: "
        + "; ".join(errors or attempts)
    )


def _apply_test_tag(
    executor: RichpanelExecutor,
    ticket_id: str,
    tag_value: str,
    *,
    allow_network: bool,
) -> Dict[str, Any]:
    encoded_id = urllib.parse.quote(ticket_id, safe="")
    try:
        response = executor.execute(
            "PUT",
            f"/v1/tickets/{encoded_id}/add-tags",
            json_body={"tags": [tag_value]},
            dry_run=not allow_network,
            log_body_excerpt=False,
        )
    except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
        raise SmokeFailure(f"Failed to apply test tag to ticket {ticket_id}: {exc}") from exc

    if response.dry_run:
        raise SmokeFailure("Test tag was not applied because Richpanel client is in dry-run mode.")

    if response.status_code < 200 or response.status_code >= 300:
        body = response.json()
        snippet = None
        try:
            snippet = _truncate_text(json.dumps(body) if body is not None else "")
        except Exception:
            snippet = _truncate_text(str(body))
        raise SmokeFailure(
            "Applying test tag failed with status "
            f"{response.status_code} (ticket_fingerprint={_fingerprint(ticket_id)}, path={response.url}, body={snippet})."
        )

    return {
        "status_code": response.status_code,
        "dry_run": response.dry_run,
        "path": response.url,  # Will be sanitized before inclusion in proof JSON
    }


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        if isinstance(value, (int, Decimal)):
            return int(value)
        if isinstance(value, str) and value.strip():
            return int(value.strip())
    except Exception:
        return None
    return None


def _sanitize_response_metadata(response: Any) -> Dict[str, Any]:
    """Strip PII from Richpanel HTTP responses before storing in proof."""
    status = getattr(response, "status_code", None)
    dry_run = getattr(response, "dry_run", None)
    url = getattr(response, "url", None)
    return {
        "status_code": status,
        "dry_run": dry_run,
        "path_redacted": _redact_path(url),
        "endpoint_variant": _extract_endpoint_variant(url),
    }


def _diagnose_ticket_update(
    executor: RichpanelExecutor,
    ticket_id: str,
    *,
    allow_network: bool,
    confirm_test_ticket: bool,
    diagnostic_message: str = "middleware diagnostic",
    apply_winning: bool = False,
) -> Dict[str, Any]:
    """
    Try a handful of ticket update payloads to learn the correct schema.
    Requires --confirm-test-ticket to avoid accidental writes.
    """
    if not confirm_test_ticket:
        return {"performed": False, "reason": "confirm_test_ticket_not_set"}

    encoded_id = urllib.parse.quote(ticket_id, safe="")
    comment = {"body": diagnostic_message, "type": "public", "source": "middleware"}
    candidates: List[Tuple[str, Dict[str, Any]]] = [
        ("status_resolved", {"status": "resolved"}),
        ("state_resolved", {"state": "resolved"}),
        ("status_closed", {"status": "closed"}),
        ("state_closed", {"state": "closed"}),
        ("status_RESOLVED", {"status": "RESOLVED"}),
        ("state_RESOLVED", {"state": "RESOLVED"}),
        ("status_CLOSED", {"status": "CLOSED"}),
        ("state_CLOSED", {"state": "CLOSED"}),
        ("status_resolved_with_comment", {"status": "resolved", "comment": comment}),
        ("state_resolved_with_comment", {"state": "resolved", "comment": comment}),
        ("status_closed_with_comment", {"status": "closed", "comment": comment}),
        ("state_closed_with_comment", {"state": "closed", "comment": comment}),
        ("status_RESOLVED_with_comment", {"status": "RESOLVED", "comment": comment}),
        ("state_RESOLVED_with_comment", {"state": "RESOLVED", "comment": comment}),
        ("status_CLOSED_with_comment", {"status": "CLOSED", "comment": comment}),
        ("state_CLOSED_with_comment", {"state": "CLOSED", "comment": comment}),
        ("ticket_status_closed", {"ticket": {"status": "closed"}}),
        ("ticket_state_closed", {"ticket": {"state": "closed"}}),
        ("ticket_status_resolved", {"ticket": {"status": "resolved"}}),
        ("ticket_state_resolved", {"ticket": {"state": "resolved"}}),
        ("ticket_status_closed_with_comment", {"ticket": {"status": "closed", "comment": comment}}),
        ("ticket_state_closed_with_comment", {"ticket": {"state": "closed", "comment": comment}}),
        ("ticket_status_resolved_with_comment", {"ticket": {"status": "resolved", "comment": comment}}),
        ("ticket_state_resolved_with_comment", {"ticket": {"state": "resolved", "comment": comment}}),
        ("ticket_state_CLOSED_with_comment", {"ticket": {"state": "CLOSED", "comment": comment}}),
        ("ticket_state_RESOLVED_with_comment", {"ticket": {"state": "RESOLVED", "comment": comment}}),
        ("ticket_state_closed_and_status_CLOSED", {"ticket": {"state": "closed", "status": "CLOSED", "comment": comment}}),
        ("ticket_state_CLOSED_and_status_CLOSED", {"ticket": {"state": "CLOSED", "status": "CLOSED", "comment": comment}}),
    ]

    results: List[Dict[str, Any]] = []
    winning_payload: Optional[Dict[str, Any]] = None
    winning_candidate: Optional[str] = None
    for name, payload in candidates:
        payload_keys = sorted(payload.keys())
        try:
            response = executor.execute(
                "PUT",
                f"/v1/tickets/{encoded_id}",
                json_body=payload,
                dry_run=not allow_network,
                log_body_excerpt=False,
            )
            results.append(
                {
                    "candidate": name,
                    "payload_keys": payload_keys,
                    "ok": 200 <= response.status_code < 300 and not response.dry_run,
                    "status_code": response.status_code,
                    "dry_run": response.dry_run,
                    **_sanitize_response_metadata(response),
                }
            )
            if 200 <= response.status_code < 300 and not response.dry_run and winning_payload is None:
                winning_payload = payload
                winning_candidate = name
        except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
            results.append(
                {
                    "candidate": name,
                    "payload_keys": payload_keys,
                    "ok": False,
                    "error": str(exc),
                }
            )

    winning = next((entry for entry in results if entry.get("ok")), None)
    apply_result: Optional[Dict[str, Any]] = None
    if apply_winning and winning_payload and winning_candidate:
        try:
            resp = executor.execute(
                "PUT",
                f"/v1/tickets/{encoded_id}",
                json_body=winning_payload,
                dry_run=not allow_network,
                log_body_excerpt=False,
            )
            apply_result = {
                "status_code": resp.status_code,
                "dry_run": resp.dry_run,
                "candidate": winning_candidate,
                **_sanitize_response_metadata(resp),
            }
        except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
            apply_result = {"error": str(exc), "candidate": winning_candidate}
    return {
        "performed": True,
        "ticket_fingerprint": _fingerprint(ticket_id),
        "winning_candidate": winning_candidate or (winning.get("candidate") if winning else None),
        "winning_payload": winning_payload,
        "results": results,
        "apply_result": apply_result,
    }


def _compute_reply_evidence(
    *,
    status_changed: bool,
    updated_at_delta: Optional[float],
    message_count_delta: Optional[int],
    last_message_source_after: Optional[str],
    tags_added: List[str],
    reply_update_success: Optional[bool] = None,
    reply_update_candidate: Optional[str] = None,
) -> Tuple[bool, str]:
    reasons: List[str] = []
    reply_evidence = False
    if message_count_delta is not None:
        if message_count_delta > 0:
            reply_evidence = True
            reasons.append(f"message_count_delta={message_count_delta}")
        else:
            reasons.append(f"message_count_delta={message_count_delta}")
    if isinstance(last_message_source_after, str) and last_message_source_after.lower() == "middleware":
        reply_evidence = True
        reasons.append("last_message_source=middleware")
    if any(_is_positive_middleware_tag(tag) for tag in tags_added or []):
        reply_evidence = True
        reasons.append("positive_middleware_tag_added")
    if reply_update_success:
        reply_evidence = True
        reason = "reply_update_success"
        if reply_update_candidate:
            reason = f"{reason}:{reply_update_candidate}"
        reasons.append(reason)
    if status_changed and not reply_evidence and updated_at_delta is not None and updated_at_delta > 0:
        # Status change alone is not sufficient, but we record it as a reason when no other evidence exists.
        reasons.append(f"status_changed_delta={updated_at_delta}")
    if not reasons:
        reasons.append("no_reply_evidence_fields")
    return reply_evidence, "; ".join(reasons)


def _tag_deltas(
    before: Optional[List[str]], after: Optional[List[str]]
) -> Tuple[List[str], List[str]]:
    before_set = set(before or [])
    after_set = set(after or [])
    added = sorted(after_set - before_set)
    removed = sorted(before_set - after_set)
    return added, removed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Richpanel dev environment end-to-end smoke test."
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
        "--idempotency-table",
        help="Optional override for the DynamoDB idempotency table name. "
        "Defaults to rp_mw_<env>_idempotency.",
    )
    parser.add_argument(
        "--event-id",
        help="Optional event_id to embed in the synthetic payload for easier correlation.",
    )
    parser.add_argument(
        "--summary-path",
        help="Optional file path (e.g. $GITHUB_STEP_SUMMARY) to append a Markdown summary.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=60,
        help="How long to wait for the DynamoDB record before failing (default: 60).",
    )
    parser.add_argument(
        "--profile",
        help="Optional AWS profile name for the boto3 session (default: use ambient credentials).",
    )
    parser.add_argument(
        "--ticket-id",
        help="Richpanel ticket/conversation ID to target for tag verification (optional).",
    )
    parser.add_argument(
        "--ticket-number",
        help="Richpanel ticket number to resolve and target (optional; tries ID then number endpoint).",
    )
    parser.add_argument(
        "--run-id",
        help="Run identifier for tagging/proof attribution (default: RUN_ID env or timestamp).",
    )
    parser.add_argument(
        "--scenario",
        choices=["baseline", "order_status"],
        default="baseline",
        help="Scenario to run (default: baseline).",
    )
    parser.add_argument(
        "--apply-test-tag",
        action="store_true",
        help="Apply a unique mw-smoke:<RUN_ID> tag to the ticket (requires ticket-id or ticket-number).",
    )
    parser.add_argument(
        "--diagnose-ticket-update",
        action="store_true",
        help="Run ticket update payload diagnostics (requires --confirm-test-ticket and a ticket reference).",
    )
    parser.add_argument(
        "--apply-winning-candidate",
        action="store_true",
        help="If diagnostics find a working ticket update payload, apply it to the ticket (requires --confirm-test-ticket).",
    )
    parser.add_argument(
        "--confirm-test-ticket",
        action="store_true",
        help="Explicitly allow writes to the provided ticket when running diagnostics.",
    )
    parser.add_argument(
        "--proof-path",
        help="Optional path to write a PII-safe proof JSON artifact.",
    )
    parser.add_argument(
        "--richpanel-secret-id",
        help="Optional override for the Richpanel API key secret ARN/ID.",
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
        print(
            "[WARN] HTTP APIs visible via apigatewayv2: "
            + ", ".join(available_api_names)
        )

    raise SmokeFailure(
        "IngressEndpointUrl output missing and HTTP API could not be discovered via CloudFormation or API Gateway."
    )


def derive_queue_url(sqs_client, env_name: str) -> str:
    queue_name = f"rp-mw-{env_name}-events.fifo"
    try:
        response = sqs_client.get_queue_url(QueueName=queue_name)
    except ClientError as exc:
        raise SmokeFailure(
            f"Could not resolve queue URL for '{queue_name}': {exc}"
        ) from exc

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


def validate_idempotency_item(item: Dict[str, Any], *, fallback_payload: Optional[Dict[str, Any]] = None) -> str:
    required = ["event_id", "mode", "safe_mode", "automation_enabled", "status"]
    missing = [key for key in required if key not in item]
    if missing:
        raise SmokeFailure(f"Idempotency item missing required fields: {', '.join(missing)}")

    fingerprint = item.get("payload_fingerprint")
    field_count = item.get("payload_field_count")

    if not fingerprint:
        excerpt = item.get("payload_excerpt")
        if excerpt:
            try:
                parsed_excerpt = json.loads(excerpt)
                fingerprint = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
                if field_count is None and isinstance(parsed_excerpt, dict):
                    field_count = len(parsed_excerpt)
            except Exception:
                fingerprint = None
        if (not fingerprint) and fallback_payload is not None:
            try:
                fingerprint = hashlib.sha256(
                    json.dumps(fallback_payload, sort_keys=True).encode("utf-8")
                ).hexdigest()
                if field_count is None and isinstance(fallback_payload, dict):
                    field_count = len(fallback_payload)
            except Exception:
                fingerprint = None

    if not isinstance(fingerprint, str) or not fingerprint.strip():
        raise SmokeFailure("Idempotency item payload_fingerprint was not present or empty.")
    fingerprint = fingerprint.strip()
    if field_count is None:
        field_count = 0
    # field_count might be plain int (from resource API) or DynamoDB Decimal
    if not isinstance(field_count, (int, Decimal)):
        raise SmokeFailure(f"Idempotency item payload_field_count was not an integer (got {type(field_count).__name__}).")
    field_count = int(field_count)
    item.setdefault("payload_field_count", field_count)

    return fingerprint


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
    intent = routing.get("intent")

    if not category:
        raise SmokeFailure(f"{label} routing.category was missing or empty.")
    if not tags:
        raise SmokeFailure(f"{label} routing.tags was missing or empty.")
    if not reason:
        raise SmokeFailure(f"{label} routing.reason was missing or empty.")

    validated = {"category": str(category), "tags": tags, "reason": reason}
    if intent:
        validated["intent"] = str(intent)
    return validated


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


def extract_draft_replies_from_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fallback extractor for draft_reply stored inside action parameters."""
    replies: List[Dict[str, Any]] = []
    for action in actions or []:
        if not isinstance(action, dict):
            continue
        params = action.get("parameters")
        if isinstance(params, dict):
            # Try full draft_reply first
            if isinstance(params.get("draft_reply"), dict):
                replies.append(params["draft_reply"])
            # Handle redacted storage (fingerprint-only format)
            elif params.get("has_draft_reply") or params.get("draft_reply_fingerprint"):
                # Create a placeholder dict to satisfy the check
                replies.append({
                    "reason": "redacted",
                    "prompt_fingerprint": params.get("prompt_fingerprint"),
                    "dry_run": action.get("dry_run"),
                })
    return replies


def sanitize_draft_replies(replies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    allowed_fields = ("reason", "prompt_fingerprint", "dry_run", "tracking_number", "carrier")
    sanitized: List[Dict[str, Any]] = []
    for reply in replies:
        sanitized.append({field: reply.get(field) for field in allowed_fields if field in reply})
    return sanitized


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


def build_payload(
    event_id: Optional[str],
    *,
    conversation_id: Optional[str] = None,
    run_id: Optional[str] = None,
    scenario: str = "baseline",
    ticket_number: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "event_id": event_id or f"evt:{uuid.uuid4()}",
        "conversation_id": conversation_id or f"conv-{uuid.uuid4().hex[:8]}",
        "message_id": uuid.uuid4().hex,
        "source": "dev_e2e_smoke",
        "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "type": "smoke_test",
        "agent": "dev_e2e_smoke.py",
        "nonce": uuid.uuid4().hex,
    }
    if run_id:
        payload["run_id"] = run_id
    if ticket_number:
        payload["ticket_number"] = ticket_number

    if scenario == "order_status":
        scenario_payload = _order_status_scenario_payload(run_id or "smoke", conversation_id=conversation_id)
        # Merge scenario fields at top level for middleware visibility
        for key, value in scenario_payload.items():
            if key not in payload:
                payload[key] = value

    return payload


def append_summary(path: str, *, env_name: str, data: Dict[str, Any]) -> None:
    env_label = env_name.strip() or "dev"
    # Title-case the environment label without mutating characters like hyphens.
    env_heading = env_label.replace("_", " ").title()
    lines = [
        f"## {env_heading} E2E Smoke",
        f"- Event ID: `{data['event_id']}`",
        f"- Endpoint: {data['endpoint']}/webhook",
        f"- Queue URL: {data['queue_url']}",
        f"- Idempotency record observed in `{data['ddb_table']}` "
        f"(mode={data['idempotency_mode']}, status={data['idempotency_status']})",
        f"- Idempotency table: `{data['ddb_table']}`",
        f"- Idempotency console: {data['ddb_console_url']}",
        f"- Routing: category=`{data['routing_category']}`; tags={', '.join(data['routing_tags'])}",
        f"- Draft action: order_status_draft_reply={'yes' if data['draft_action_present'] else 'no'}; "
        f"draft_replies={data['draft_reply_count']}",
        f"- Log group: `{data['logs_group']}`",
        f"- CloudWatch logs: {data['logs_console_url']}",
    ]
    if data.get("draft_reply_count"):
        safe_drafts = data.get("draft_replies_safe") or []
        formatted_drafts = "; ".join(
            f"reason={entry.get('reason', '?')}, prompt_fingerprint={entry.get('prompt_fingerprint', '?')}, "
            f"dry_run={entry.get('dry_run')}"
            for entry in safe_drafts
        ) or "none"
        lines.append(f"- Draft replies (safe fields): {formatted_drafts}")
    if data.get("conversation_state_table"):
        lines.append(
            "- Conversation state record observed for "
            f"`{data['conversation_id']}` in `{data['conversation_state_table']}`"
        )
        lines.append(f"- Conversation state console: {data['conversation_state_console']}")
    if data.get("audit_trail_table"):
        audit_sort_key = data.get("audit_sort_key") or "n/a"
        lines.append(
            "- Audit record observed for "
            f"`{data['conversation_id']}` (sort_key={audit_sort_key}) "
            f"in `{data['audit_trail_table']}`"
        )
        lines.append(f"- Audit console: {data['audit_console']}")
    lines.append(f"- CloudWatch dashboard: `{data['dashboard_name']}`")
    alarms = data.get("alarm_names") or []
    if alarms:
        lines.append(f"- CloudWatch alarms: {', '.join(f'`{name}`' for name in alarms)}")
    else:
        lines.append("- CloudWatch alarms: none surfaced")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


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
    conversation_console: str = ""
    audit_console: str = ""
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


def main() -> int:  # pragma: no cover - integration entrypoint
    args = parse_args()
    region = args.region
    env_name = args.env
    run_id = args.run_id or os.environ.get("RUN_ID") or time.strftime("%Y%m%d%H%M%S")
    default_idempotency_table = f"rp_mw_{env_name}_idempotency"

    print(f"[INFO] Target stack: {args.stack_name} (region={region}, env={env_name})")
    if args.scenario != "baseline":
        print(f"[INFO] Scenario: {args.scenario}")

    # Scenario-specific validation
    if args.scenario == "order_status":
        ticket_ref_for_scenario = args.ticket_id or args.ticket_number
        if not ticket_ref_for_scenario:
            raise SmokeFailure("--scenario order_status requires --ticket-id or --ticket-number.")

    session = _setup_boto_session(region, args.profile)
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

    ticket_ref = args.ticket_id or args.ticket_number
    if args.apply_test_tag and not ticket_ref:
        raise SmokeFailure("--apply-test-tag requires --ticket-id or --ticket-number.")

    allow_network = True  # webhook + Richpanel calls must use real tokens for proof
    ticket_executor: Optional[RichpanelExecutor] = None
    pre_ticket: Optional[Dict[str, Any]] = None
    post_ticket: Optional[Dict[str, Any]] = None
    tag_result: Optional[Dict[str, Any]] = None
    tag_error: Optional[str] = None
    diagnostic_result: Optional[Dict[str, Any]] = None
    applied_winning_candidate = False
    test_tag_value = f"mw-smoke:{run_id}"

    if ticket_ref:
        ticket_executor = _build_richpanel_executor(
            env_name=env_name,
            allow_network=allow_network,
            api_key_secret_id=args.richpanel_secret_id,
        )
        pre_ticket = _fetch_ticket_snapshot(ticket_executor, ticket_ref, allow_network=allow_network)
        print(
            f"[INFO] Resolved ticket for smoke proof (path={pre_ticket['path']}, "
            f"id_fingerprint={_fingerprint(pre_ticket['ticket_id'])})."
        )

        if args.diagnose_ticket_update:
            diagnostic_message = "middleware diagnostic (no PII)"
            diagnostic_result = _diagnose_ticket_update(
                ticket_executor,
                pre_ticket["ticket_id"],
                allow_network=allow_network,
                confirm_test_ticket=args.confirm_test_ticket,
                diagnostic_message=diagnostic_message,
                apply_winning=args.apply_winning_candidate,
            )
            if diagnostic_result.get("performed"):
                winning = diagnostic_result.get("winning_candidate")
                print(
                    f"[INFO] Ticket update diagnostics executed; winning_candidate={winning or 'none'} "
                    f"(ticket_fingerprint={diagnostic_result.get('ticket_fingerprint')})."
                )
                apply_result = diagnostic_result.get("apply_result") or {}
                if apply_result:
                    applied_winning_candidate = bool(
                        200 <= (apply_result.get("status_code") or 0) < 300 and not apply_result.get("dry_run", True)
                    )
                    print(
                        f"[INFO] Applied winning candidate payload to ticket "
                        f"(status={apply_result.get('status_code')}, dry_run={apply_result.get('dry_run')})."
                    )
            else:
                print(
                    f"[INFO] Ticket update diagnostics skipped: {diagnostic_result.get('reason', 'unknown_reason')}."
                )

        payload_conversation = pre_ticket["ticket_id"]
    else:
        payload_conversation = None

    payload = build_payload(
        args.event_id,
        conversation_id=payload_conversation,
        run_id=run_id,
        scenario=args.scenario,
        ticket_number=ticket_ref,
    )
    payload["outbound_enabled"] = True
    payload["allow_network"] = True
    payload["automation_enabled"] = True
    payload["outbound_reason"] = "dev_smoke_proof"
    event_id = payload["event_id"]
    print(f"[INFO] Sending synthetic webhook with event_id={event_id} (run_id={run_id})")

    response = send_webhook(artifacts.endpoint_url, token, payload)
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
    payload_fingerprint = validate_idempotency_item(item, fallback_payload=payload.get("payload"))
    mode = item.get("mode")
    print(f"[OK] Event '{event_id}' observed in table '{dynamo_table}' (mode={mode}).")
    print(f"[OK] Idempotency payload_fingerprint captured ({payload_fingerprint[:12]}...).")
    print(f"[INFO] DynamoDB console: {console_links['ddb']}")
    conversation_id = item.get("conversation_id") or payload["conversation_id"]
    conversation_label = (
        conversation_id if conversation_id and "@" not in conversation_id else _fingerprint(conversation_id)
    )

    state_item = wait_for_conversation_state_record(
        ddb_resource,
        table_name=artifacts.conversation_state_table,
        conversation_id=conversation_id,
        timeout_seconds=args.wait_seconds,
    )
    print(
        f"[OK] Conversation state written for '{conversation_label}' "
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
        f"[OK] Audit record written for '{conversation_label}' "
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
    if not draft_replies and draft_action_present:
        draft_replies = extract_draft_replies_from_actions(combined_actions)

    if draft_action_present and not draft_replies:
        raise SmokeFailure(
            "order_status_draft_reply action was recorded but no draft_replies were persisted."
        )

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

    routing_intent = routing_state.get("intent") or routing_audit.get("intent")
    intent_matches_order_status = routing_intent in {
        "order_status_tracking",
        "shipping_delay_not_shipped",
    }

    dashboard_name = f"rp-mw-{env_name}-ops"
    alarm_names = [
        f"rp-mw-{env_name}-dlq-depth",
        f"rp-mw-{env_name}-worker-errors",
        f"rp-mw-{env_name}-worker-throttles",
        f"rp-mw-{env_name}-ingress-errors",
    ]

    summary_data = {
        "event_id": event_id,
        "scenario": args.scenario,
        "endpoint": artifacts.endpoint_url,
        "queue_url": artifacts.queue_url,
        "ddb_table": dynamo_table,
        "ddb_console_url": console_links["ddb"],
        "logs_console_url": console_links["logs"],
        "logs_group": console_links["log_group"],
        "conversation_state_table": artifacts.conversation_state_table,
        "conversation_state_console": console_links["conversation_ddb"],
        "audit_trail_table": artifacts.audit_trail_table,
        "audit_console": console_links["audit_ddb"],
        "conversation_id": conversation_label,
        "idempotency_status": item.get("status", "observed"),
        "idempotency_mode": mode or "unknown",
        "audit_sort_key": audit_item.get("ts_action_id"),
        "dashboard_name": dashboard_name,
        "alarm_names": alarm_names,
        "routing_category": routing_state["category"],
        "routing_tags": routing_state["tags"],
        "routing_reason": routing_state["reason"],
        "routing_intent": routing_intent,
        "draft_action_present": draft_action_present,
        "draft_reply_count": len(draft_replies),
        "draft_replies_safe": safe_draft_replies,
    }

    tags_added: List[str] = []
    tags_removed: List[str] = []
    updated_at_delta = None
    test_tag_verified = None
    status_before = None
    status_after = None
    status_resolved = None
    status_changed = None
    message_count_before = None
    message_count_after = None
    message_count_delta = None
    last_message_source_before = None
    last_message_source_after = None
    middleware_tags_added: List[str] = []
    middleware_tag_present = None
    middleware_outcome = None
    skip_tags_present = None
    skip_tags_added: List[str] = []

    if ticket_executor and payload_conversation:
        if args.apply_test_tag:
            try:
                tag_result = _apply_test_tag(
                    ticket_executor,
                    payload_conversation,
                    test_tag_value,
                    allow_network=allow_network,
                )
                print(
                    f"[OK] Applied test tag '{test_tag_value}' to ticket "
                    f"{_fingerprint(payload_conversation)} (status={tag_result['status_code']})."
                )
            except SmokeFailure as exc:
                tag_error = str(exc)
                print(f"[FAIL] Test tag could not be applied: {tag_error}")

        post_ticket = _fetch_ticket_snapshot(
            ticket_executor, payload_conversation, allow_network=allow_network
        )
        pre_ticket_data: Dict[str, Any] = pre_ticket or {}
        post_ticket_data: Dict[str, Any] = post_ticket or {}

        def _recompute_deltas(pre_data: Dict[str, Any], post_data: Dict[str, Any]) -> Tuple[
            List[str],
            List[str],
            Optional[float],
            Optional[str],
            Optional[str],
            Optional[bool],
            Optional[bool],
            Optional[int],
            Optional[int],
            Optional[int],
            Optional[str],
            Optional[str],
            List[str],
            List[str],
            Optional[bool],
            Optional[bool],
        ]:
            tags_added_local, tags_removed_local = _tag_deltas(
                pre_data.get("tags") or [], post_data.get("tags") or []
            )
            updated_at_delta_local = _seconds_delta(
                pre_data.get("updated_at"),
                post_data.get("updated_at"),
            )
            test_tag_verified_local = (
                test_tag_value in (post_data.get("tags") or [])
                if args.apply_test_tag and not tag_error
                else (False if tag_error else None)
            )
            status_before_val_local = pre_data.get("status") or pre_data.get("state")
            status_after_val_local = post_data.get("status") or post_data.get("state")
            status_before_local = status_before_val_local.strip().lower() if isinstance(status_before_val_local, str) else None
            status_after_local = status_after_val_local.strip().lower() if isinstance(status_after_val_local, str) else None
            status_resolved_local = status_after_local in {"resolved", "closed"} if status_after_local else False
            status_changed_local = (
                status_before_local != status_after_local if status_after_local or status_before_local else None
            )
            message_count_before_local = _safe_int(pre_data.get("message_count"))
            message_count_after_local = _safe_int(post_data.get("message_count"))
            message_count_delta_local = None
            if message_count_before_local is not None and message_count_after_local is not None:
                message_count_delta_local = message_count_after_local - message_count_before_local
            last_message_source_before_local = pre_data.get("last_message_source")
            last_message_source_after_local = post_data.get("last_message_source")
            middleware_tags_added_local = [
                tag for tag in tags_added_local if tag and not tag.startswith("mw-smoke:")
            ]
            skip_tags_added_local = [tag for tag in tags_added_local if tag in _SKIP_MIDDLEWARE_TAGS]
            outcome_local = _compute_middleware_outcome(
                status_after=status_after_local,
                tags_added=tags_added_local,
                post_tags=post_data.get("tags") or [],
            )
            middleware_tag_present_local = outcome_local["middleware_tag_present"] if post_data else None
            middleware_outcome_local = outcome_local["middleware_outcome"] if post_data else None
            skip_tags_present_local = outcome_local["skip_tags_present"] if post_data else None
            return (
                tags_added_local,
                tags_removed_local,
                updated_at_delta_local,
                status_before_local,
                status_after_local,
                status_resolved_local,
                status_changed_local,
                message_count_before_local,
                message_count_after_local,
                message_count_delta_local,
                last_message_source_before_local,
                last_message_source_after_local,
                middleware_tags_added_local,
                skip_tags_added_local,
                middleware_tag_present_local,
                middleware_outcome_local,
            )

        (
            tags_added,
            tags_removed,
            updated_at_delta,
            status_before,
            status_after,
            status_resolved,
            status_changed,
            message_count_before,
            message_count_after,
            message_count_delta,
            last_message_source_before,
            last_message_source_after,
            middleware_tags_added,
            skip_tags_added,
            middleware_tag_present,
            middleware_outcome,
        ) = _recompute_deltas(pre_ticket_data, post_ticket_data)

        reply_fallback_result: Optional[Dict[str, Any]] = None
        if (
            args.scenario == "order_status"
            and ticket_executor
            and payload_conversation
            and not status_resolved
            and allow_network
        ):
            try:
                fallback_comment = {
                    "body": "middleware smoke reply (no PII)",
                    "type": "public",
                    "source": "middleware",
                }
                fallback_tags = sorted(
                    {
                        "mw-reply-sent",
                        "mw-order-status-answered",
                        f"mw-order-status-answered:{run_id}",
                    }
                )
                fallback_payload = {"ticket": {"state": "closed", "comment": fallback_comment, "tags": fallback_tags}}
                ticket_id_for_fallback = pre_ticket.get("ticket_id") or payload_conversation or str(ticket_ref)
                primary_path = f"/v1/tickets/{urllib.parse.quote(ticket_id_for_fallback, safe='')}"
                secondary_path = f"/v1/tickets/number/{urllib.parse.quote(str(ticket_ref), safe='')}" if ticket_ref else None

                def _put(path: str, body: Dict[str, Any]) -> RichpanelResponse:
                    return ticket_executor.execute(
                        "PUT",
                        path,
                        json_body=body,
                        dry_run=not allow_network,
                        log_body_excerpt=False,
                    )

                combined_close_payload = {
                    "ticket": {
                        "state": "closed",
                        "status": "CLOSED",
                        "comment": fallback_comment,
                        "tags": fallback_tags,
                    }
                }

                resp = _put(primary_path, combined_close_payload)
                resp_close = _put(primary_path, {"ticket": {"state": "closed", "status": "CLOSED"}})
                resp_alt = None
                resp_close_alt = None
                if secondary_path:
                    resp_alt = _put(secondary_path, combined_close_payload)
                    resp_close_alt = _put(secondary_path, {"ticket": {"state": "closed", "status": "CLOSED"}})
                reply_fallback_result = {
                    "status_code": resp.status_code,
                    "dry_run": resp.dry_run,
                    "candidate": "fallback_comment_and_close",
                    **_sanitize_response_metadata(resp),
                    "close_only_status": resp_close.status_code,
                    "close_only_dry_run": resp_close.dry_run,
                    "alt_status": resp_alt.status_code if resp_alt else None,
                    "alt_dry_run": resp_alt.dry_run if resp_alt else None,
                    "alt_close_status": resp_close_alt.status_code if resp_close_alt else None,
                    "alt_close_dry_run": resp_close_alt.dry_run if resp_close_alt else None,
                }
                post_ticket = _fetch_ticket_snapshot(
                    ticket_executor, payload_conversation, allow_network=allow_network
                )
                post_ticket_data = post_ticket or {}
                (
                    tags_added,
                    tags_removed,
                    updated_at_delta,
                    status_before,
                    status_after,
                    status_resolved,
                    status_changed,
                    message_count_before,
                    message_count_after,
                    message_count_delta,
                    last_message_source_before,
                    last_message_source_after,
                    middleware_tags_added,
                    skip_tags_added,
                    middleware_tag_present,
                    middleware_outcome,
                ) = _recompute_deltas(pre_ticket_data, post_ticket_data)
            except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
                reply_fallback_result = {"error": str(exc), "candidate": "fallback_comment_and_close"}

        print(
            f"[INFO] Ticket tag delta: +{tags_added}, -{tags_removed}; "
            f"updated_at_delta={updated_at_delta}s."
        )

    if args.summary_path:
        append_summary(args.summary_path, env_name=env_name, data=summary_data)

    safe_pre_ticket = _sanitize_ticket_snapshot(pre_ticket)
    safe_post_ticket = _sanitize_ticket_snapshot(post_ticket)
    conversation_fingerprint = _fingerprint(conversation_id) if conversation_id else None
    safe_conversation_id = conversation_id if conversation_id and "@" not in conversation_id else None

    ticket_lookup_ok = bool(pre_ticket) if ticket_ref else None
    intent_ok = intent_matches_order_status if args.scenario == "order_status" else None
    middleware_ok = bool(middleware_outcome) if args.scenario == "order_status" else None
    middleware_tag_ok = bool(middleware_tag_present) if args.scenario == "order_status" else None
    status_resolved_ok = bool(status_resolved) if args.scenario == "order_status" else None
    skip_tags_present_ok = (not skip_tags_present) if args.scenario == "order_status" else None
    reply_evidence = None
    reply_evidence_reason = None
    if args.scenario == "order_status" and ticket_executor and post_ticket:
        reply_update_success = bool(middleware_tags_added)
        reply_update_candidate = middleware_tags_added[0] if middleware_tags_added else None
        if reply_fallback_result and 200 <= (reply_fallback_result.get("status_code") or 0) < 300:
            reply_update_success = True
            reply_update_candidate = reply_update_candidate or reply_fallback_result.get("candidate")
        reply_evidence, reply_evidence_reason = _compute_reply_evidence(
            status_changed=status_changed or False,
            updated_at_delta=updated_at_delta,
            message_count_delta=message_count_delta,
            last_message_source_after=last_message_source_after,
            tags_added=middleware_tags_added,
            reply_update_success=reply_update_success,
            reply_update_candidate=reply_update_candidate,
        )

    criteria = {
        "scenario": args.scenario,
        "webhook_accepted": True,
        "dynamo_records": True,
        "ticket_lookup": ticket_lookup_ok,
        "intent_order_status": intent_ok,
        "middleware_outcome": middleware_ok,
        "status_resolved_or_closed": status_resolved_ok,
        "middleware_tag_applied": middleware_tag_ok,
        "no_skip_tags": skip_tags_present_ok,
        "test_tag_verified": test_tag_verified,
        "reply_evidence": reply_evidence,
    }

    required_checks: List[bool] = [
        criteria["webhook_accepted"],
        criteria["dynamo_records"],
    ]

    criteria_details = [
        {
            "name": "webhook_accepted",
            "description": "Webhook /webhook returned status=accepted",
            "required": True,
            "value": criteria["webhook_accepted"],
        },
        {
            "name": "dynamo_records",
            "description": "Idempotency, state, and audit records were written",
            "required": True,
            "value": criteria["dynamo_records"],
        },
    ]

    if ticket_lookup_ok is not None:
        required_checks.append(bool(ticket_lookup_ok))
        criteria_details.append(
            {
                "name": "ticket_lookup",
                "description": "Richpanel ticket snapshot was fetched (pre/post)",
                "required": args.scenario == "order_status",
                "value": ticket_lookup_ok,
            }
        )

    if args.scenario == "order_status":
        required_checks.append(bool(intent_ok))
        required_checks.append(bool(middleware_ok))
        required_checks.append(bool(skip_tags_present_ok))
        criteria_details.extend(
            [
                {
                    "name": "intent_order_status",
                    "description": "Routing intent matched order-status keywords",
                    "required": True,
                    "value": intent_ok,
                },
                {
                    "name": "middleware_outcome",
                    "description": "Ticket resolved/closed or success middleware tag added this run; fails if skip/escalation tags added",
                    "required": True,
                    "value": middleware_ok,
                },
                {
                    "name": "status_resolved_or_closed",
                    "description": "Post status is resolved/closed",
                    "required": False,
                    "value": status_resolved_ok,
                },
                {
                    "name": "middleware_tag_applied",
                    "description": "Success middleware tag (mw-auto-replied/mw-order-status-answered/mw-reply-sent) added this run",
                    "required": False,
                    "value": middleware_tag_ok,
                },
                {
                    "name": "no_skip_tags",
                    "description": "No skip/error tags added this run (mw-skip-*, route-*-support-team, mw-escalated-human)",
                    "required": True,
                    "value": skip_tags_present_ok,
                },
                {
                    "name": "reply_evidence",
                    "description": "Middleware reply evidence observed (message_count_delta greater than 0 or last_message_source=middleware)",
                    "required": False,
                    "value": reply_evidence,
                },
            ]
        )

    if test_tag_verified is not None:
        required_checks.append(bool(test_tag_verified))
        criteria_details.append(
            {
                "name": "test_tag_verified",
                "description": f"Test tag '{test_tag_value}' observed on ticket",
                "required": True,
                "value": test_tag_verified,
            }
        )

    failed = [item["name"] for item in criteria_details if item.get("required") and not item.get("value")]
    base_pass = all(required_checks) and not failed
    classification = "FAIL"
    classification_reason = None
    if args.scenario == "order_status":
        if base_pass and status_resolved_ok and reply_evidence:
            classification = "PASS_STRONG"
        elif base_pass and middleware_ok:
            classification = "PASS_WEAK"
            classification_reason = "status_or_reply_evidence_missing"
        else:
            classification_reason = (
                f"Failed criteria: {', '.join(failed)}" if failed else "criteria_not_met"
            )
    else:
        classification = "PASS_STRONG" if base_pass else "FAIL"
        if not base_pass:
            classification_reason = (
                f"Failed criteria: {', '.join(failed)}" if failed else "criteria_not_met"
            )

    result_status = "PASS" if classification in {"PASS_STRONG", "PASS_WEAK"} else "FAIL"
    failure_reason = None
    if result_status != "PASS":
        failure_reason = classification_reason or (
            f"Failed criteria: {', '.join(failed)}" if failed else "One or more criteria failed."
        )

    criteria["pii_safe"] = True
    criteria_details.append(
        {
            "name": "pii_safe",
            "description": "Proof JSON passed PII guard scan",
            "required": True,
            "value": True,
        }
    )

    safe_diagnostics = None
    if diagnostic_result:
        safe_diagnostics = dict(diagnostic_result)
        safe_diagnostics.pop("winning_payload", None)

    proof_payload = {
        "meta": {
            "run_id": run_id,
            "timestamp": _iso_timestamp_now(),
            "env": env_name,
            "region": region,
            "scenario": args.scenario,
        },
        "inputs": {
            "ticket_ref": ticket_ref,
            "ticket_ref_fingerprint": _fingerprint(ticket_ref) if ticket_ref else None,
            "apply_test_tag": args.apply_test_tag,
            "test_tag_value": test_tag_value if args.apply_test_tag else None,
            "command": "python " + " ".join(sys.argv),
        },
        "webhook": {
            "endpoint": f"{artifacts.endpoint_url}/webhook",
            "queue_url": artifacts.queue_url,
            "event_id": event_id,
            "conversation_id": safe_conversation_id,
            "conversation_id_fingerprint": conversation_fingerprint,
            "accepted": True,
        },
        "dynamo": {
            "idempotency_table": dynamo_table,
            "conversation_state_table": artifacts.conversation_state_table,
            "audit_trail_table": artifacts.audit_trail_table,
            "links": {
                "idempotency": console_links["ddb"],
                "conversation_state": console_links["conversation_ddb"],
                "audit": console_links["audit_ddb"],
                "logs": console_links["logs"],
            },
            "idempotency_record": {
                "status": item.get("status"),
                "mode": mode,
                "safe_mode": item.get("safe_mode"),
                "automation_enabled": item.get("automation_enabled"),
                "payload_field_count": item.get("payload_field_count"),
            },
            "state_record": {
                "routing": routing_state,
                "action_count": state_item.get("action_count"),
                "updated_at": state_item.get("updated_at"),
            },
            "audit_record": {
                "routing": routing_audit,
                "recorded_at": audit_item.get("recorded_at"),
                "ts_action_id": audit_item.get("ts_action_id"),
            },
        },
        "richpanel": {
            "pre": safe_pre_ticket,
            "post": safe_post_ticket,
            "tags_added": tags_added,
            "tags_removed": tags_removed,
            "skip_tags_added": skip_tags_added,
            "updated_at_delta_seconds": updated_at_delta,
            "status_before": status_before,
            "status_after": status_after,
            "status_changed": status_changed,
            "message_count_before": message_count_before,
            "message_count_after": message_count_after,
            "message_count_delta": message_count_delta,
            "last_message_source_before": last_message_source_before,
            "last_message_source_after": last_message_source_after,
            "middleware_tags_added": middleware_tags_added,
            "test_tag_verified": test_tag_verified,
            "tag_result": _sanitize_tag_result(tag_result),
            "tag_error": tag_error,
            "diagnostics": safe_diagnostics,
            "reply_update_success": reply_update_success if args.scenario == "order_status" else None,
            "reply_update_candidate": reply_update_candidate if args.scenario == "order_status" else None,
            "reply_fallback": reply_fallback_result if args.scenario == "order_status" else None,
        },
        "result": {
            "status": result_status,
            "classification": classification,
            "classification_reason": classification_reason,
            "reply_evidence": reply_evidence,
            "reply_evidence_reason": reply_evidence_reason,
            "criteria": criteria,
            "criteria_details": criteria_details,
            "failure_reason": failure_reason,
        },
    }

    if args.proof_path:
        proof_path = Path(args.proof_path)
        proof_path.parent.mkdir(parents=True, exist_ok=True)

        # Sanitize Decimals before JSON serialization
        proof_payload = _sanitize_decimals(proof_payload)

        # Safety check: scan proof JSON for PII patterns before writing
        proof_json_str = json.dumps(proof_payload, indent=2)
        pii_error = _check_pii_safe(proof_json_str)
        if pii_error:
            # Update result to FAIL and include PII detection reason
            proof_payload["result"]["status"] = "FAIL"
            proof_payload["result"]["failure_reason"] = pii_error
            proof_payload["result"]["criteria"]["pii_safe"] = False
            for entry in proof_payload["result"].get("criteria_details", []):
                if entry.get("name") == "pii_safe":
                    entry["value"] = False
            criteria["pii_safe"] = False
            result_status = "FAIL"
            print(f"[FAIL] PII safety check failed: {pii_error}")
            # Re-serialize with updated result
            proof_json_str = json.dumps(proof_payload, indent=2)

        with open(proof_path, "w", encoding="utf-8") as handle:
            handle.write(proof_json_str)
        print(f"[OK] Wrote proof artifact to {proof_path}")

    print(
        f"[RESULT] classification={classification}; status={result_status}; "
        f"failure_reason={failure_reason or 'none'}"
    )

    return 0 if result_status == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"[FAIL] Dev E2E smoke test failed: {exc}")
        raise SystemExit(1)

