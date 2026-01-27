#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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
    RichpanelWriteDisabledError,
    SecretLoadError,
    TransportError,
)
from integrations.common import (  # type: ignore
    PROD_WRITE_ACK_ENV,
    PROD_WRITE_ACK_PHRASE,
    PRODUCTION_ENVIRONMENTS,
)

ENV_FROM_EMAIL = "MW_SMOKE_TICKET_FROM_EMAIL"
ENV_SUBJECT = "MW_SMOKE_TICKET_SUBJECT"
ENV_BODY = "MW_SMOKE_TICKET_BODY"

DEFAULT_FROM_EMAIL = "sandbox.test+autoticket@example.com"
DEFAULT_SUBJECT = "Sandbox E2E smoke (autoticket)"
DEFAULT_BODY = "Automated sandbox E2E smoke test message. Please ignore."
DEFAULT_TO_EMAIL = "support@example.com"
DEFAULT_CUSTOMER_FIRST_NAME = "Sandbox"
DEFAULT_CUSTOMER_LAST_NAME = "Test"
DEFAULT_PROOF_PATH = (
    ROOT
    / "REHYDRATION_PACK"
    / "RUNS"
    / "B59"
    / "B"
    / "PROOF"
    / "created_ticket.json"
)

DEFAULT_TAGS = ["mw-smoke-autoticket"]
ENV_TO_EMAIL = "MW_SMOKE_TICKET_TO_EMAIL"
ENV_FIRST_NAME = "MW_SMOKE_TICKET_FIRST_NAME"
ENV_LAST_NAME = "MW_SMOKE_TICKET_LAST_NAME"


def _fingerprint(value: str, length: int = 12) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length]


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        text = str(value).strip()
    except Exception:
        return None
    return text or None


def _redact_identifier(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return f"redacted:{_fingerprint(value)}"


def _resolve_text(value: Optional[str], env_key: str, default: str) -> str:
    candidate = value or os.environ.get(env_key) or default
    try:
        candidate = str(candidate).strip()
    except Exception:
        return default
    return candidate or default


def _prod_write_ack_matches(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip() == PROD_WRITE_ACK_PHRASE


def _require_prod_write_ack(*, env_name: str, ack_token: Optional[str]) -> None:
    if env_name.strip().lower() not in PRODUCTION_ENVIRONMENTS:
        return
    env_value = os.environ.get(PROD_WRITE_ACK_ENV)
    if _prod_write_ack_matches(env_value) or _prod_write_ack_matches(ack_token):
        return
    raise SystemExit(
        "[FAIL] Refusing to create tickets in production without "
        f"{PROD_WRITE_ACK_ENV}={PROD_WRITE_ACK_PHRASE} or "
        f"--i-understand-prod-writes {PROD_WRITE_ACK_PHRASE}."
    )


def _build_ticket_payload(
    *,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    first_name: str,
    last_name: str,
) -> Dict[str, Any]:
    ticket: Dict[str, Any] = {
        "status": "OPEN",
        "priority": "LOW",
        "subject": subject,
        "comment": {
            "sender_type": "customer",
            "body": body,
            "public": True,
        },
        "via": {
            "channel": "email",
            "source": {
                "from": {"address": from_email},
                "to": {"address": to_email},
            },
        },
        "customer_profile": {
            "firstName": first_name,
            "lastName": last_name,
        },
    }
    if DEFAULT_TAGS:
        ticket["tags"] = list(DEFAULT_TAGS)
    return {"ticket": ticket}


def _extract_ticket_fields(payload: Any) -> Tuple[Optional[str], Optional[str]]:
    ticket_obj: Dict[str, Any] = {}
    if isinstance(payload, dict):
        if isinstance(payload.get("ticket"), dict):
            ticket_obj = payload["ticket"]
        else:
            ticket_obj = payload
    ticket_number = (
        ticket_obj.get("conversation_no")
        or ticket_obj.get("ticket_number")
        or ticket_obj.get("number")
        or ticket_obj.get("conversation_number")
    )
    ticket_id = ticket_obj.get("id") or ticket_obj.get("ticket_id") or ticket_obj.get("_id")
    return _coerce_str(ticket_number), _coerce_str(ticket_id)


def _write_artifact(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a fresh sandbox email ticket (PII-safe output)."
    )
    parser.add_argument(
        "--env", default="dev", help="Environment name used for secrets (default: dev)."
    )
    parser.add_argument(
        "--i-understand-prod-writes",
        dest="prod_writes_ack",
        help=(
            "Acknowledge production ticket writes; must equal "
            f"{PROD_WRITE_ACK_PHRASE}."
        ),
    )
    parser.add_argument(
        "--region",
        required=True,
        help="AWS region for Secrets Manager (e.g. us-east-2).",
    )
    parser.add_argument(
        "--stack-name",
        default="RichpanelMiddleware-dev",
        help="CloudFormation stack name (unused; kept for dev_e2e_smoke parity).",
    )
    parser.add_argument(
        "--profile",
        help="Optional AWS profile name for the boto3 session (default: use ambient credentials).",
    )
    parser.add_argument(
        "--from-email",
        dest="from_email",
        help=(
            "Customer from-address for the ticket. "
            f"Defaults to ${ENV_FROM_EMAIL} or {DEFAULT_FROM_EMAIL}."
        ),
    )
    parser.add_argument(
        "--subject",
        help=(
            "Email subject for the ticket. "
            f"Defaults to ${ENV_SUBJECT} or '{DEFAULT_SUBJECT}'."
        ),
    )
    parser.add_argument(
        "--body",
        help=(
            "Email body for the ticket. "
            f"Defaults to ${ENV_BODY} or '{DEFAULT_BODY}'."
        ),
    )
    parser.add_argument(
        "--proof-path",
        default=str(DEFAULT_PROOF_PATH),
        help="Path to write the PII-safe created_ticket artifact.",
    )
    parser.add_argument(
        "--richpanel-secret-id",
        help="Optional override for the Richpanel API key secret ARN/ID.",
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
    _require_prod_write_ack(env_name=args.env, ack_token=args.prod_writes_ack)

    from_email = _resolve_text(args.from_email, ENV_FROM_EMAIL, DEFAULT_FROM_EMAIL)
    to_email = _resolve_text(os.environ.get(ENV_TO_EMAIL), ENV_TO_EMAIL, DEFAULT_TO_EMAIL)
    subject = _resolve_text(args.subject, ENV_SUBJECT, DEFAULT_SUBJECT)
    body = _resolve_text(args.body, ENV_BODY, DEFAULT_BODY)
    first_name = _resolve_text(
        os.environ.get(ENV_FIRST_NAME), ENV_FIRST_NAME, DEFAULT_CUSTOMER_FIRST_NAME
    )
    last_name = _resolve_text(
        os.environ.get(ENV_LAST_NAME), ENV_LAST_NAME, DEFAULT_CUSTOMER_LAST_NAME
    )

    client = RichpanelClient(
        api_key_secret_id=args.richpanel_secret_id,
        dry_run=False,
    )
    payload = _build_ticket_payload(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
        first_name=first_name,
        last_name=last_name,
    )

    try:
        response = client.request(
            "POST",
            "/v1/tickets",
            json_body=payload,
            dry_run=False,
            log_body_excerpt=False,
        )
    except (RichpanelRequestError, RichpanelWriteDisabledError, SecretLoadError, TransportError) as exc:
        print(f"[FAIL] Ticket creation failed: {exc}", file=sys.stderr)
        return 1

    if response.dry_run:
        print("[FAIL] Richpanel client is in dry-run mode; ticket not created.", file=sys.stderr)
        return 1

    if response.status_code < 200 or response.status_code >= 300:
        print(
            f"[FAIL] Ticket creation failed with status {response.status_code}.",
            file=sys.stderr,
        )
        return 1

    ticket_number, ticket_id = _extract_ticket_fields(response.json())
    if not ticket_number and not ticket_id:
        print("[FAIL] Ticket creation response missing ticket identifiers.", file=sys.stderr)
        return 1

    proof_path = Path(args.proof_path) if args.proof_path else None
    ticket_number_fp = _fingerprint(ticket_number) if ticket_number else None
    ticket_id_fp = _fingerprint(ticket_id) if ticket_id else None

    artifact = {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "env": args.env,
            "region": args.region,
            "stack_name": args.stack_name,
        },
        "request": {
            "channel": "email",
            "from_email_redacted": _redact_identifier(from_email),
            "subject_fingerprint": _fingerprint(subject),
            "body_fingerprint": _fingerprint(body),
            "tags": list(DEFAULT_TAGS),
        },
        "response": {
            "status_code": response.status_code,
            "ticket_number_redacted": _redact_identifier(ticket_number),
            "ticket_number_fingerprint": ticket_number_fp,
            "conversation_id_redacted": _redact_identifier(ticket_id),
            "conversation_id_fingerprint": ticket_id_fp,
        },
        "result": {"status": "created"},
    }

    if proof_path:
        _write_artifact(proof_path, artifact)
        print(f"[OK] Wrote created-ticket artifact to {proof_path}")

    display_ticket = _redact_identifier(ticket_number) or "<redacted>"
    display_conversation = _redact_identifier(ticket_id) or "<redacted>"
    print(
        "[OK] Created sandbox email ticket "
        f"(ticket_number={display_ticket}, conversation_id={display_conversation})."
    )
    if ticket_number_fp or ticket_id_fp:
        print(
            "[OK] Fingerprints "
            f"(ticket_number={ticket_number_fp or 'n/a'}, "
            f"conversation_id={ticket_id_fp or 'n/a'})."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
