from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple


def extract_ticket_list(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("tickets", "data", "items", "results"):
            items = payload.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


def extract_ticket_fields(ticket: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    ticket_number = (
        ticket.get("conversation_no")
        or ticket.get("ticket_number")
        or ticket.get("number")
        or ticket.get("conversation_number")
    )
    ticket_id = ticket.get("id") or ticket.get("ticket_id") or ticket.get("_id")
    number_str = str(ticket_number).strip() if ticket_number is not None else None
    id_str = str(ticket_id).strip() if ticket_id is not None else None
    return number_str or None, id_str or None


def fetch_recent_ticket_refs(
    client: Any, *, sample_size: int, list_path: str
) -> List[str]:
    if sample_size < 1:
        raise SystemExit("--sample-size must be >= 1")
    list_paths = [list_path]
    if list_path == "/v1/tickets":
        list_paths.append("/api/v1/conversations")
        list_paths.append("/v1/conversations")

    for path in list_paths:
        response = client.request(
            "GET",
            path,
            params={"limit": str(sample_size), "page": "1"},
            dry_run=False,
            log_body_excerpt=False,
        )
        if response.dry_run:
            raise SystemExit(
                f"Ticket listing failed: status {response.status_code} dry_run={response.dry_run}"
            )
        if response.status_code >= 400:
            if path != list_paths[-1] and response.status_code in {401, 403, 404}:
                continue
            raise SystemExit(
                f"Ticket listing failed: status {response.status_code} dry_run={response.dry_run}"
            )
        tickets = extract_ticket_list(response.json())
        results: List[str] = []
        seen: set[str] = set()
        for ticket in tickets:
            number, ticket_id = extract_ticket_fields(ticket)
            candidate = ticket_id or number
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            results.append(candidate)
            if len(results) >= sample_size:
                break
        return results


def safe_error(exc: Exception) -> Dict[str, str]:
    name = exc.__class__.__name__
    if name in {"RichpanelRequestError", "SecretLoadError", "TransportError"}:
        return {"type": "richpanel_error"}
    if name in {"ShopifyRequestError"}:
        return {"type": "shopify_error"}
    return {"type": "error"}


def comment_is_operator(comment: Dict[str, Any]) -> Optional[bool]:
    for key in ("is_operator", "isOperator"):
        if key in comment:
            return bool(comment.get(key))
    via = comment.get("via")
    if isinstance(via, dict):
        for key in ("isOperator", "is_operator"):
            if key in via:
                return bool(via.get(key))
    return None


def _parse_timestamp(value: Any) -> Optional[float]:
    if not value:
        return None
    try:
        text = str(value).strip()
    except Exception:
        return None
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def extract_comment_message(
    payload: Dict[str, Any],
    *,
    extractor: Optional[Callable[..., str]] = None,
) -> str:
    ticket_obj = payload.get("ticket") if isinstance(payload.get("ticket"), dict) else payload
    comments = ticket_obj.get("comments") or []
    if not isinstance(comments, list):
        return ""

    has_operator_flag = any(
        comment_is_operator(comment) is not None
        for comment in comments
        if isinstance(comment, dict)
    )

    candidates: list[tuple[tuple[Any, ...], str]] = []
    for index, comment in enumerate(comments):
        if not isinstance(comment, dict):
            continue
        text_value = ""
        for key in ("plain_body", "body"):
            value = comment.get(key)
            if value is None:
                continue
            try:
                text_value = str(value).strip()
            except Exception:
                text_value = ""
            if text_value:
                break
        if not text_value and extractor:
            try:
                text_value = extractor(comment, default="")  # type: ignore[arg-type]
            except TypeError:
                text_value = extractor(comment)  # type: ignore[call-arg]
        if not text_value:
            continue

        via = comment.get("via") if isinstance(comment.get("via"), dict) else {}
        channel = str(via.get("channel") or "").strip().lower()
        email_rank = 0 if channel == "email" else 1

        operator_flag = comment_is_operator(comment)
        if has_operator_flag:
            if operator_flag is False:
                operator_rank = 0
            elif operator_flag is True:
                operator_rank = 2
            else:
                operator_rank = 1
        else:
            operator_rank = 0

        created_at = comment.get("created_at") or comment.get("createdAt")
        timestamp = _parse_timestamp(created_at)
        created_rank = -timestamp if timestamp is not None else float("inf")

        plain_len = 0
        try:
            if comment.get("plain_body"):
                plain_len = len(str(comment.get("plain_body")).strip())
        except Exception:
            plain_len = 0
        body_len = len(text_value) if text_value else 0
        text_len = plain_len if plain_len > 0 else body_len

        score = (operator_rank, email_rank, created_rank, text_len, index)
        candidates.append((score, text_value))

    if not candidates:
        return ""
    best = min(candidates, key=lambda item: item[0])
    return best[1]
