#!/usr/bin/env python3
"""
dev_richpanel_close_probe.py

PII-safe probe to discover which Richpanel ticket update payload actually closes/resolves
tickets in the dev environment. Runs against a single ticket/reference and records a
redacted proof JSON for auditability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import boto3  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

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


PII_PATTERNS = ["@", "%40", "<", ">", "mail.", "%3C", "%3E"]
DEFAULT_COMMENT = {"body": "middleware close probe", "type": "internal", "source": "middleware"}
CLOSED_STATES = {"closed", "resolved", "solved"}


def _fingerprint(value: str, length: int = 12) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length]


def _normalize_status(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        normalized = str(value).strip()
    except Exception:
        return None
    return normalized or None


def _is_closed_status(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in CLOSED_STATES


def _redact_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if "/v1/tickets/number/" in path:
        return "/v1/tickets/number/<redacted>"
    if "/v1/tickets/" in path:
        parts = path.split("/v1/tickets/")
        if len(parts) > 1:
            suffix = parts[1]
            if "/" in suffix:
                sub_path = "/" + suffix.split("/", 1)[1]
                return f"/v1/tickets/<redacted>{sub_path}"
        return "/v1/tickets/<redacted>"
    return "<redacted>"


def _extract_endpoint_variant(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if "/v1/tickets/number/" in path:
        return "number"
    if "/v1/tickets/" in path:
        return "id"
    return "unknown"


def _sanitize_snapshot(snapshot: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not snapshot:
        return None
    sanitized = dict(snapshot)
    ticket_id = sanitized.pop("ticket_id", None)
    if ticket_id:
        sanitized["ticket_id_fingerprint"] = _fingerprint(str(ticket_id))
    raw_path = sanitized.pop("path", None)
    if raw_path:
        sanitized["path_redacted"] = _redact_path(raw_path)
        sanitized["endpoint_variant"] = _extract_endpoint_variant(raw_path)
    return sanitized


def _seconds_delta(before: Optional[str], after: Optional[str]) -> Optional[float]:
    if not before or not after:
        return None
    try:
        start = datetime.fromisoformat(before.replace("Z", "+00:00"))
        end = datetime.fromisoformat(after.replace("Z", "+00:00"))
        return (end - start).total_seconds()
    except Exception:
        return None


def _check_pii_safe(payload_json: str) -> Optional[str]:
    safe_json = payload_json.replace("<redacted>", "REDACTED_PLACEHOLDER")
    for pattern in PII_PATTERNS:
        if pattern in safe_json:
            return f"PII pattern '{pattern}' detected in proof payload"
    return None


def _build_executor(env_name: str, *, allow_network: bool) -> RichpanelExecutor:
    os.environ.setdefault("RICHPANEL_ENV", env_name)
    client = RichpanelClient(dry_run=not allow_network)
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

        status = _normalize_status(payload.get("status"))
        state = _normalize_status(payload.get("state"))
        tags = payload.get("tags") or []
        updated_at = payload.get("updated_at") or payload.get("updatedAt")
        message_count = payload.get("messages_count") or payload.get("message_count") or payload.get("messagesCount")
        last_message_source = payload.get("last_message_source") or payload.get("lastMessageSource")

        return {
            "ticket_id": str(payload.get("id") or ticket_ref),
            "status": status,
            "state": state,
            "tags": tags,
            "updated_at": updated_at,
            "message_count": message_count,
            "last_message_source": last_message_source,
            "status_code": response.status_code,
            "dry_run": response.dry_run,
            "path": path,
        }

    raise RuntimeError("Ticket lookup failed; attempted paths: " + "; ".join(errors or attempts))


def _candidate_payloads(comment: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    return [
        ("status_resolved_top", {"status": "resolved", "comment": comment}),
        ("state_closed_top", {"state": "closed", "comment": comment}),
        ("ticket_status_resolved", {"ticket": {"status": "resolved", "comment": comment}}),
        ("ticket_status_closed", {"ticket": {"status": "closed", "comment": comment}}),
        ("ticket_state_closed_status_CLOSED", {"ticket": {"state": "closed", "status": "CLOSED", "comment": comment}}),
        ("ticket_state_resolved_status_RESOLVED", {"ticket": {"state": "resolved", "status": "RESOLVED", "comment": comment}}),
        ("ticket_state_closed", {"ticket": {"state": "closed", "comment": comment}}),
        ("ticket_state_resolved", {"ticket": {"state": "resolved", "comment": comment}}),
        ("ticket_state_nested_status_resolved", {"ticket_state": {"status": "resolved"}, "comment": comment}),
        ("ticket_state_nested_state_closed", {"ticket_state": {"state": "closed"}, "comment": comment}),
    ]


def _summarize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"keys": sorted(payload.keys())}
    if "ticket" in payload and isinstance(payload["ticket"], dict):
        summary["ticket_keys"] = sorted(payload["ticket"].keys())
    if "ticket_state" in payload and isinstance(payload["ticket_state"], dict):
        summary["ticket_state_keys"] = sorted(payload["ticket_state"].keys())
    if "status" in payload:
        summary["status"] = payload["status"]
    if "state" in payload:
        summary["state"] = payload["state"]
    if "ticket" in payload and isinstance(payload["ticket"], dict):
        if "status" in payload["ticket"]:
            summary["ticket.status"] = payload["ticket"]["status"]
        if "state" in payload["ticket"]:
            summary["ticket.state"] = payload["ticket"]["state"]
    if "ticket_state" in payload and isinstance(payload["ticket_state"], dict):
        if "status" in payload["ticket_state"]:
            summary["ticket_state.status"] = payload["ticket_state"]["status"]
        if "state" in payload["ticket_state"]:
            summary["ticket_state.state"] = payload["ticket_state"]["state"]
    return summary


def _run_probe(
    *,
    executor: RichpanelExecutor,
    ticket_ref: str,
    run_id: str,
    proof_path: Path,
    allow_network: bool,
) -> Dict[str, Any]:
    before_snapshot = _fetch_ticket_snapshot(executor, ticket_ref, allow_network=allow_network)
    baseline_closed = _is_closed_status(before_snapshot.get("status")) or _is_closed_status(before_snapshot.get("state"))
    attempts: List[Dict[str, Any]] = []
    winning_candidate: Optional[str] = None
    latest_snapshot = before_snapshot

    for candidate_name, payload in _candidate_payloads(DEFAULT_COMMENT):
        response = executor.execute(
            "PUT",
            f"/v1/tickets/{urllib.parse.quote(before_snapshot['ticket_id'], safe='')}",
            json_body=payload,
            dry_run=not allow_network,
            log_body_excerpt=False,
        )

        after_snapshot = _fetch_ticket_snapshot(executor, before_snapshot["ticket_id"], allow_network=allow_network)
        status_after = after_snapshot.get("status")
        state_after = after_snapshot.get("state")
        closed_after = _is_closed_status(status_after) or _is_closed_status(state_after)
        status_changed = (
            status_after != before_snapshot.get("status") or state_after != before_snapshot.get("state")
        )

        attempts.append(
            {
                "candidate": candidate_name,
                "payload_summary": _summarize_payload(payload),
                "status_code": response.status_code,
                "dry_run": response.dry_run,
                "path_redacted": _redact_path(response.url),
                "endpoint_variant": _extract_endpoint_variant(response.url),
                "status_before": before_snapshot.get("status"),
                "state_before": before_snapshot.get("state"),
                "status_after": status_after,
                "state_after": state_after,
                "status_changed": status_changed,
                "closed_state_reached": closed_after,
                "updated_at_delta_seconds": _seconds_delta(
                    before_snapshot.get("updated_at"), after_snapshot.get("updated_at")
                ),
                "snapshot_after": _sanitize_snapshot(after_snapshot),
            }
        )

        latest_snapshot = after_snapshot
        if closed_after or status_changed:
            winning_candidate = candidate_name
            break
        # Carry forward the latest snapshot as the new "before" in case later payloads build on it.
        before_snapshot = after_snapshot

    proof = {
        "run_id": run_id,
        "ticket_ref_fingerprint": _fingerprint(ticket_ref),
        "ticket_id_fingerprint": _fingerprint(str(latest_snapshot.get("ticket_id", ticket_ref))),
        "endpoint_variant": _extract_endpoint_variant(latest_snapshot.get("path")),
        "baseline_closed": baseline_closed,
        "winning_candidate": winning_candidate,
        "status_changed": winning_candidate is not None,
        "closed_state_reached": winning_candidate is not None,
        "before": _sanitize_snapshot(before_snapshot),
        "after": _sanitize_snapshot(latest_snapshot),
        "attempts": attempts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    proof_json = json.dumps(proof, indent=2, sort_keys=True)
    error = _check_pii_safe(proof_json)
    if error:
        raise RuntimeError(error)

    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(proof_json, encoding="utf-8")
    return proof


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe Richpanel ticket close payloads (PII-safe).")
    parser.add_argument("--profile", required=True, help="AWS profile to use for Secrets Manager auth.")
    parser.add_argument("--region", required=True, help="AWS region for Secrets Manager.")
    parser.add_argument("--env", required=True, choices=["dev", "staging", "prod", "local"], help="Environment name.")
    parser.add_argument("--conversation-id", dest="conversation_id", help="Richpanel conversation/ticket ID.")
    parser.add_argument("--ticket-number", dest="ticket_number", help="Richpanel ticket number.")
    parser.add_argument("--run-id", required=True, help="RUN_<...> identifier for evidence paths.")
    parser.add_argument(
        "--proof-path",
        help="Where to write the probe proof JSON (PII-safe). Defaults to REHYDRATION_PACK/RUNS/<RUN_ID>/C/richpanel_close_probe.json",
    )
    parser.add_argument(
        "--confirm-test-ticket",
        action="store_true",
        help="Required safety guard to confirm the provided ticket is safe for probing.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.confirm_test_ticket:
        print("ERROR: --confirm-test-ticket is required to run the probe.", file=sys.stderr)
        return 1

    if not (args.conversation_id or args.ticket_number):
        print("ERROR: Provide --conversation-id or --ticket-number.", file=sys.stderr)
        return 1
    if args.conversation_id and args.ticket_number:
        print("ERROR: Provide only one of --conversation-id or --ticket-number.", file=sys.stderr)
        return 1

    ticket_ref = args.conversation_id or args.ticket_number
    proof_path = (
        Path(args.proof_path)
        if args.proof_path
        else ROOT
        / "REHYDRATION_PACK"
        / "RUNS"
        / args.run_id
        / "C"
        / "richpanel_close_probe.json"
    )

    os.environ.setdefault("AWS_PROFILE", args.profile)
    os.environ.setdefault("AWS_DEFAULT_REGION", args.region)
    os.environ.setdefault("AWS_REGION", args.region)

    executor = _build_executor(args.env, allow_network=True)
    try:
        proof = _run_probe(
            executor=executor,
            ticket_ref=ticket_ref,
            run_id=args.run_id,
            proof_path=proof_path,
            allow_network=True,
        )
    except Exception as exc:  # pragma: no cover - runtime safety
        print(f"ERROR: probe failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"proof_path": str(proof_path), "winning_candidate": proof.get("winning_candidate")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
