from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


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
    response = client.request(
        "GET",
        list_path,
        params={"limit": str(sample_size), "page": "1"},
        dry_run=False,
        log_body_excerpt=False,
    )
    if response.dry_run or response.status_code >= 400:
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
