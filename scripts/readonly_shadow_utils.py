from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from richpanel_middleware.integrations.richpanel.client import (  # type: ignore
    RichpanelRequestError,
    SecretLoadError,
    TransportError as RichpanelTransportError,
)
from richpanel_middleware.integrations.shopify import (  # type: ignore
    ShopifyRequestError,
    TransportError as ShopifyTransportError,
)


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
        raise SystemExit("--sample-size/--max-tickets must be >= 1")
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
    if isinstance(
        exc, (RichpanelRequestError, SecretLoadError, RichpanelTransportError)
    ):
        return {"type": "richpanel_error"}
    if isinstance(exc, (ShopifyRequestError, ShopifyTransportError)):
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


def _comment_has_text(comment: Dict[str, Any]) -> bool:
    for key in ("plain_body", "body"):
        value = comment.get(key)
        if value is None:
            continue
        try:
            text = str(value).strip()
        except Exception:
            continue
        if text:
            return True
    return False


def summarize_comment_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
    ticket_obj = payload.get("ticket") if isinstance(payload.get("ticket"), dict) else payload
    comments = ticket_obj.get("comments") or []
    if not isinstance(comments, list):
        return {
            "comment_count": 0,
            "comment_text_present": False,
            "comment_operator_flag_present": False,
            "customer_comment_present": False,
        }
    comment_dicts = [comment for comment in comments if isinstance(comment, dict)]
    comment_count = len(comment_dicts)
    comment_text_present = any(_comment_has_text(comment) for comment in comment_dicts)
    comment_operator_flag_present = any(
        comment_is_operator(comment) is not None for comment in comment_dicts
    )
    customer_comment_present = any(
        comment_is_operator(comment) is False for comment in comment_dicts
    )
    return {
        "comment_count": comment_count,
        "comment_text_present": comment_text_present,
        "comment_operator_flag_present": comment_operator_flag_present,
        "customer_comment_present": customer_comment_present,
    }


def build_route_info(routing: Any, routing_artifact: Any) -> Dict[str, Optional[Any]]:
    llm = getattr(routing_artifact, "llm_suggestion", None) if routing_artifact else None
    if not isinstance(llm, dict):
        llm = {}
    confidence = llm.get("confidence")
    return {
        "intent": getattr(routing, "intent", None),
        "department": getattr(routing, "department", None),
        "reason": getattr(routing, "reason", None),
        "primary_source": getattr(routing_artifact, "primary_source", None),
        "confidence": confidence,
        "llm_model": llm.get("model"),
        "llm_response_id": llm.get("response_id"),
        "llm_gated_reason": llm.get("gated_reason"),
    }


_ORDER_NUMBER_PATTERNS = (
    re.compile(r"(?mi)\borderNumber\s*:\s*(\d{3,20})\b"),
    re.compile(r"(?mi)\border\s*number\s*:\s*(\d{3,20})\b"),
    re.compile(r"(?mi)\border\s*no\.?\s*[:#]?\s*(\d{3,20})\b"),
    re.compile(r"(?mi)\border\s*#?\s*(\d{3,20})\b"),
    re.compile(r"(?<!\d)#(\d{3,10})(?!\d)"),
)


def _coerce_order_number(value: Any) -> str:
    if value is None:
        return ""
    try:
        text = str(value).strip()
    except Exception:
        return ""
    if not text:
        return ""
    normalized = text.replace(",", "")
    if normalized.startswith("#"):
        normalized = normalized[1:].strip()
    return normalized if normalized.isdigit() and len(normalized) >= 3 else ""


def _extract_order_number_from_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.replace(",", "")
    for pattern in _ORDER_NUMBER_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return match.group(1)
    return ""


def _iter_comment_texts(payload: Dict[str, Any]) -> List[str]:
    ticket_obj = payload.get("ticket") if isinstance(payload.get("ticket"), dict) else payload
    comments = ticket_obj.get("comments") or []
    if not isinstance(comments, list):
        return []
    texts: List[str] = []
    for comment in comments:
        if not isinstance(comment, dict):
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
                texts.append(text)
    return texts


def extract_order_number(payload: Dict[str, Any]) -> str:
    for key in ("order_number", "orderNumber", "order_no", "orderNo"):
        value = _coerce_order_number(payload.get(key))
        if value:
            return value

    order = payload.get("order")
    if isinstance(order, dict):
        for key in ("number", "order_number", "orderNumber", "order_no", "orderNo"):
            value = _coerce_order_number(order.get(key))
            if value:
                return value
        name_value = order.get("name")
        if name_value:
            candidate = _extract_order_number_from_text(str(name_value))
            if candidate:
                return candidate

    custom_fields = payload.get("custom_fields")
    if isinstance(custom_fields, dict):
        for key, value in custom_fields.items():
            if "order" not in str(key).lower():
                continue
            candidate = _coerce_order_number(value)
            if candidate:
                return candidate
            candidate = _extract_order_number_from_text(str(value))
            if candidate:
                return candidate

    subject = payload.get("subject")
    if subject:
        candidate = _extract_order_number_from_text(str(subject))
        if candidate:
            return candidate

    comment_texts = _iter_comment_texts(payload)
    if comment_texts:
        for pattern in _ORDER_NUMBER_PATTERNS:
            for text in comment_texts:
                match = pattern.search(text.replace(",", ""))
                if match:
                    return match.group(1)

    messages = payload.get("messages") or payload.get("conversation_messages") or []
    if isinstance(messages, list):
        message_texts: List[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            for key in ("plain_body", "body", "text", "message"):
                value = message.get(key)
                if value is None:
                    continue
                message_texts.append(str(value))
        if message_texts:
            for pattern in _ORDER_NUMBER_PATTERNS:
                for text in message_texts:
                    match = pattern.search(text.replace(",", ""))
                    if match:
                        return match.group(1)

    return ""


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
