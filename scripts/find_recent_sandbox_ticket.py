#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

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
    RichpanelRequestError,
    SecretLoadError,
    TransportError,
)

_SKIP_TAGS = {
    "mw-skip-status-read-failed",
    "mw-skip-order-status-closed",
    "mw-skip-followup-after-auto-reply",
    "route-email-support-team",
    "mw-escalated-human",
}


def _extract_ticket_list(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("tickets", "data", "items", "results"):
            items = payload.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


def _normalize_tags(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        candidates = value
    else:
        candidates = [value]
    tags: List[str] = []
    for candidate in candidates:
        tag = str(candidate).strip() if candidate is not None else ""
        if tag:
            tags.append(tag)
    return tags


def _extract_ticket_fields(ticket: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], List[str]]:
    ticket_number = (
        ticket.get("conversation_no")
        or ticket.get("ticket_number")
        or ticket.get("number")
        or ticket.get("conversation_number")
    )
    ticket_id = ticket.get("id") or ticket.get("ticket_id") or ticket.get("_id")
    tags = _normalize_tags(ticket.get("tags"))
    number_str = str(ticket_number).strip() if ticket_number is not None else None
    id_str = str(ticket_id).strip() if ticket_id is not None else None
    return number_str or None, id_str or None, tags


def _fetch_ticket_tags(client: RichpanelClient, ticket_id: str) -> List[str]:
    encoded_id = urllib.parse.quote(str(ticket_id), safe="")
    response = client.request(
        "GET",
        f"/v1/tickets/{encoded_id}",
        dry_run=False,
        log_body_excerpt=False,
    )
    if response.status_code < 200 or response.status_code >= 300:
        return []
    payload = response.json()
    if isinstance(payload, dict):
        ticket_obj = payload.get("ticket")
        if isinstance(ticket_obj, dict):
            return _normalize_tags(ticket_obj.get("tags"))
        return _normalize_tags(payload.get("tags"))
    return []


def _filter_candidates(
    *,
    client: RichpanelClient,
    tickets: Iterable[Dict[str, Any]],
    require_no_skip_tags: bool,
    max_results: int,
) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    for ticket in tickets:
        number, ticket_id, tags = _extract_ticket_fields(ticket)
        if not number or not ticket_id:
            continue
        if require_no_skip_tags:
            if not tags:
                tags = _fetch_ticket_tags(client, ticket_id)
            if any(tag in _SKIP_TAGS for tag in tags):
                continue
        results.append({"ticket_number": number, "ticket_id": ticket_id})
        if len(results) >= max_results:
            break
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List recent Richpanel sandbox tickets (PII-safe: outputs ticket number + id only)."
        )
    )
    parser.add_argument(
        "--env", default="dev", help="Environment name used for secrets (default: dev)."
    )
    parser.add_argument(
        "--region", default="us-east-2", help="AWS region for Secrets Manager (default: us-east-2)."
    )
    parser.add_argument(
        "--profile",
        help="Optional AWS profile name for the boto3 session (default: use ambient credentials).",
    )
    parser.add_argument(
        "--richpanel-secret-id",
        help="Optional override for the Richpanel API key secret ARN/ID.",
    )
    parser.add_argument(
        "--path",
        default="/v1/tickets",
        help="Richpanel API path for ticket listing (default: /v1/tickets).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Limit passed to the Richpanel API (default: 25).",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page passed to the Richpanel API (default: 1).",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of ticket IDs to print (default: 10).",
    )
    parser.add_argument(
        "--include-skip-tags",
        action="store_true",
        help="Include tickets that already have skip/escalation tags.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if boto3 is None:
        print("[FAIL] boto3 is required to load the Richpanel API key.", file=sys.stderr)
        return 1

    if args.profile or args.region:
        boto3.setup_default_session(
            profile_name=args.profile, region_name=args.region
        )

    os.environ.setdefault("RICHPANEL_ENV", args.env)

    client = RichpanelClient(
        api_key_secret_id=args.richpanel_secret_id,
        dry_run=False,
        read_only=True,
    )

    params: Dict[str, str] = {}
    if args.limit:
        params["limit"] = str(args.limit)
    if args.page:
        params["page"] = str(args.page)

    try:
        response = client.request(
            "GET",
            args.path,
            params=params,
            dry_run=False,
            log_body_excerpt=False,
        )
    except (RichpanelRequestError, SecretLoadError, TransportError) as exc:
        print(f"[FAIL] Richpanel ticket listing failed: {exc}", file=sys.stderr)
        return 1

    if response.status_code < 200 or response.status_code >= 300:
        print(
            f"[FAIL] Richpanel ticket listing failed with status {response.status_code}.",
            file=sys.stderr,
        )
        return 1

    tickets = _extract_ticket_list(response.json())
    require_no_skip_tags = not args.include_skip_tags
    results = _filter_candidates(
        client=client,
        tickets=tickets,
        require_no_skip_tags=require_no_skip_tags,
        max_results=max(args.max_results, 1),
    )

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
