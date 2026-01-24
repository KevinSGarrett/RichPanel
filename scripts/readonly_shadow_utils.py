from __future__ import annotations

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
    sender = str(comment.get("author_type") or comment.get("sender_type") or "").strip()
    if sender:
        normalized = sender.lower()
        if normalized in {"agent", "operator", "staff", "admin", "support"}:
            return True
        if normalized in {"customer", "user", "end_user", "shopper"}:
            return False
    return None


def extract_comment_message(
    payload: Dict[str, Any],
    *,
    extractor: Optional[Callable[..., str]] = None,
) -> str:
    comments = payload.get("comments") or []
    if not isinstance(comments, list):
        return ""
    for comment in reversed(comments):
        if not isinstance(comment, dict):
            continue
        if comment_is_operator(comment) is True:
            continue
        for key in ("plain_body", "body"):
            value = comment.get(key)
            if value is None:
                continue
            try:
                text = str(value).strip()
            except Exception:
                continue
            if text:
                return text
        if extractor:
            try:
                candidate = extractor(comment, default="")
            except TypeError:
                candidate = extractor(comment)
            if candidate:
                return candidate
    return ""
