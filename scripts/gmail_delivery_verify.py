#!/usr/bin/env python3
"""
gmail_delivery_verify.py

PII-safe Gmail delivery proof helper for sandbox order-status replies.
Requires OAuth env vars and stores only hashed/redacted evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


_EMAIL_REGEX = re.compile(r"(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}")
_TOKEN_URI = "https://oauth2.googleapis.com/token"
_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@dataclass(frozen=True)
class GmailEnv:
    client_id: str
    client_secret: str
    refresh_token: str
    user: str


def _fingerprint(value: Optional[str], *, length: int = 12) -> Optional[str]:
    if not value:
        return None
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length]


def _redact_query(query: str) -> str:
    return _EMAIL_REGEX.sub("<redacted>", query)


def _parse_internal_date(value: Any) -> Optional[str]:
    try:
        ms = int(value)
    except (TypeError, ValueError):
        return None
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.isoformat()


def _header_map(headers: Iterable[Dict[str, Any]]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for header in headers:
        if not isinstance(header, dict):
            continue
        name = header.get("name")
        value = header.get("value")
        if isinstance(name, str) and isinstance(value, str):
            result[name] = value
    return result


def _extract_recipients(headers: Dict[str, str]) -> List[str]:
    recipients: List[str] = []
    for key in ("To", "Delivered-To", "X-Original-To"):
        value = headers.get(key)
        if isinstance(value, str) and value:
            recipients.append(value)
    return recipients


def _matches_expected(value: str, expected: str) -> bool:
    return expected.lower() in value.lower()


def _sanitize_message_entry(
    message: Dict[str, Any],
    *,
    expected_to: Optional[str],
) -> Dict[str, Any]:
    headers = _header_map(message.get("headers") or [])
    recipients = _extract_recipients(headers)
    matches_expected_to = (
        any(_matches_expected(recipient, expected_to) for recipient in recipients)
        if expected_to
        else None
    )
    return {
        "id_fingerprint": _fingerprint(message.get("id")),
        "thread_id_fingerprint": _fingerprint(message.get("threadId")),
        "internal_date": _parse_internal_date(message.get("internalDate")),
        "label_ids": [str(label) for label in message.get("labelIds") or []],
        "subject_hash": _fingerprint(headers.get("Subject")),
        "from_hash": _fingerprint(headers.get("From")),
        "to_hash": _fingerprint(headers.get("To")),
        "delivered_to_hash": _fingerprint(headers.get("Delivered-To")),
        "original_to_hash": _fingerprint(headers.get("X-Original-To")),
        "date": headers.get("Date"),
        "matches_expected_to": matches_expected_to,
    }


def _build_proof_payload(
    *,
    query: str,
    user: str,
    messages: List[Dict[str, Any]],
    max_results: int,
    expected_to: Optional[str],
    profile_email: Optional[str],
) -> Dict[str, Any]:
    sanitized_messages = [
        _sanitize_message_entry(msg, expected_to=expected_to) for msg in messages
    ]
    expected_to_fingerprint = _fingerprint(expected_to) if expected_to else None
    profile_email_hash = _fingerprint(profile_email) if profile_email else None
    expected_match_count = (
        sum(1 for entry in sanitized_messages if entry.get("matches_expected_to"))
        if expected_to
        else None
    )
    most_recent = next(
        (
            entry.get("internal_date")
            for entry in sorted(
                sanitized_messages,
                key=lambda item: item.get("internal_date") or "",
                reverse=True,
            )
            if entry.get("internal_date")
        ),
        None,
    )
    status = "found" if sanitized_messages else "not_found"
    if expected_to:
        status = "found" if expected_match_count else "not_found"
    payload = {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gmail_user": user if user == "me" else f"redacted:{_fingerprint(user)}",
            "query_redacted": _redact_query(query),
            "query_fingerprint": _fingerprint(query),
            "max_results": max_results,
            "expected_to_fingerprint": expected_to_fingerprint,
            "profile_email_hash": profile_email_hash,
        },
        "result": {
            "status": status,
            "message_count": len(sanitized_messages),
            "most_recent_internal_date": most_recent,
            "expected_to_match_count": expected_match_count,
        },
        "messages": sanitized_messages,
    }
    _assert_pii_safe(payload)
    return payload


def _assert_pii_safe(payload: Dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    if _EMAIL_REGEX.search(serialized):
        raise RuntimeError("PII detected in gmail proof payload; aborting write.")


def _load_env() -> GmailEnv:
    client_id = os.environ.get("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
    refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")
    user = os.environ.get("GMAIL_USER") or "me"
    missing = [
        name
        for name, value in (
            ("GMAIL_CLIENT_ID", client_id),
            ("GMAIL_CLIENT_SECRET", client_secret),
            ("GMAIL_REFRESH_TOKEN", refresh_token),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Gmail OAuth env vars: " + ", ".join(missing)
        )
    return GmailEnv(
        client_id=str(client_id),
        client_secret=str(client_secret),
        refresh_token=str(refresh_token),
        user=str(user),
    )


def _build_credentials(env: GmailEnv):  # pragma: no cover - networked
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise RuntimeError(
            "Missing Google API deps. Install with "
            "`pip install google-auth google-auth-oauthlib google-api-python-client`."
        ) from exc

    creds = Credentials(
        token=None,
        refresh_token=env.refresh_token,
        token_uri=_TOKEN_URI,
        client_id=env.client_id,
        client_secret=env.client_secret,
        scopes=_SCOPES,
    )
    creds.refresh(Request())
    return creds


def _fetch_messages(  # pragma: no cover - networked
    *,
    env: GmailEnv,
    query: str,
    max_results: int,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Missing Google API deps. Install with "
            "`pip install google-auth google-auth-oauthlib google-api-python-client`."
        ) from exc

    creds = _build_credentials(env)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile_email = None
    profile = service.users().getProfile(userId=env.user).execute()
    if isinstance(profile, dict):
        profile_email = profile.get("emailAddress")

    list_resp = (
        service.users()
        .messages()
        .list(userId=env.user, q=query, maxResults=max_results)
        .execute()
    )
    messages = list_resp.get("messages") or []
    results: List[Dict[str, Any]] = []
    for entry in messages:
        msg_id = entry.get("id")
        if not msg_id:
            continue
        msg = (
            service.users()
            .messages()
            .get(
                userId=env.user,
                id=msg_id,
                format="metadata",
                metadataHeaders=[
                    "Subject",
                    "To",
                    "From",
                    "Date",
                    "Delivered-To",
                    "X-Original-To",
                ],
            )
            .execute()
        )
        results.append(
            {
                "id": msg.get("id"),
                "threadId": msg.get("threadId"),
                "internalDate": msg.get("internalDate"),
                "labelIds": msg.get("labelIds"),
                "headers": (msg.get("payload") or {}).get("headers") or [],
            }
        )
    return results, profile_email


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a PII-safe Gmail delivery proof artifact."
    )
    parser.add_argument(
        "--query",
        nargs="+",
        required=True,
        help="Gmail search query (quotes optional).",
    )
    parser.add_argument(
        "--expected-to",
        dest="expected_to",
        help="Optional recipient email to match (stored as fingerprint only).",
    )
    parser.add_argument("--out", required=True, help="Path to write proof JSON.")
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Max messages to include (default: 10).",
    )
    return parser.parse_args(argv)


def _normalize_query(raw: List[str]) -> str:
    return " ".join(part for part in raw if part)


def main() -> int:  # pragma: no cover - networked
    args = parse_args()
    query = _normalize_query(args.query)
    expected_to = args.expected_to
    env = _load_env()
    messages, profile_email = _fetch_messages(
        env=env, query=query, max_results=args.max_results
    )
    payload = _build_proof_payload(
        query=query,
        user=env.user,
        messages=messages,
        max_results=args.max_results,
        expected_to=expected_to,
        profile_email=profile_email if isinstance(profile_email, str) else None,
    )
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"[OK] Wrote Gmail delivery proof to {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
