from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

DEFAULT_MESSAGE_GROUP_ID = "rp-mw-default"
MAX_DEDUPE_ID_LENGTH = 128


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _shorten(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[:max_length]


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        return str(value)
    except Exception:
        return None


def _sanitize_group_id(value: str, default_group_id: str) -> str:
    cleaned = (value or default_group_id).strip() or default_group_id
    cleaned = cleaned.replace(" ", "-")
    return _shorten(cleaned, MAX_DEDUPE_ID_LENGTH)


@dataclass
class EventEnvelope:
    """Canonical event envelope shared across ingress and worker."""

    event_id: str
    received_at: str
    group_id: str
    dedupe_id: str
    payload: Dict[str, Any]
    source: str
    conversation_id: str
    message_id: Optional[str] = None

    def to_message(self) -> Dict[str, Any]:
        """Return a dict suitable for transport (e.g., SQS body)."""
        body: Dict[str, Any] = {
            "event_id": self.event_id,
            "received_at": self.received_at,
            "group_id": self.group_id,
            "dedupe_id": self.dedupe_id,
            "payload": self.payload,
            "source": self.source,
            "conversation_id": self.conversation_id,
        }
        if self.message_id:
            body["message_id"] = self.message_id
        return body


def build_event_envelope(
    payload: Dict[str, Any],
    *,
    default_group_id: str = DEFAULT_MESSAGE_GROUP_ID,
    source: str = "richpanel_http_target",
) -> EventEnvelope:
    """
    Build a canonical envelope from an ingress payload.

    This is used by ingress before enqueueing, and provides the
    canonical shape the worker expects to consume.
    """

    payload = payload or {}
    cleaned_payload: Dict[str, Any] = payload if isinstance(payload, dict) else {"data": payload}

    event_id = _coerce_str(cleaned_payload.get("event_id")) or f"evt:{uuid.uuid4()}"
    received_at = _coerce_str(cleaned_payload.get("received_at")) or _iso_now()
    conversation_id = (
        _coerce_str(
            cleaned_payload.get("conversation_id")
            or cleaned_payload.get("ticket_id")
            or cleaned_payload.get("group_id")
        )
        or default_group_id
    )
    message_id = _coerce_str(
        cleaned_payload.get("message_id") or cleaned_payload.get("dedupe_id") or event_id
    )
    dedupe_id = _shorten(message_id or event_id, MAX_DEDUPE_ID_LENGTH)
    group_id = _sanitize_group_id(
        _coerce_str(cleaned_payload.get("group_id")) or conversation_id, default_group_id
    )
    source_value = _coerce_str(cleaned_payload.get("source")) or source

    return EventEnvelope(
        event_id=event_id,
        received_at=received_at,
        group_id=group_id,
        dedupe_id=dedupe_id,
        payload=cleaned_payload,
        source=source_value,
        conversation_id=conversation_id,
        message_id=message_id,
    )


def normalize_envelope(
    data: Dict[str, Any],
    *,
    default_group_id: str = DEFAULT_MESSAGE_GROUP_ID,
    source: str = "richpanel_http_target",
) -> EventEnvelope:
    """
    Normalize any inbound event-like dict into the canonical envelope.

    Used by the worker to defensively handle slightly different shapes.
    """
    if not isinstance(data, dict):
        data = {"payload": data}

    payload_obj = data.get("payload") if isinstance(data.get("payload"), dict) else {}

    event_id = (
        _coerce_str(data.get("event_id"))
        or _coerce_str(payload_obj.get("event_id"))
        or f"evt:{uuid.uuid4()}"
    )
    received_at = (
        _coerce_str(data.get("received_at"))
        or _coerce_str(payload_obj.get("received_at"))
        or _iso_now()
    )
    conversation_id = (
        _coerce_str(data.get("conversation_id"))
        or _coerce_str(payload_obj.get("conversation_id"))
        or _coerce_str(payload_obj.get("ticket_id"))
        or _coerce_str(data.get("group_id"))
        or default_group_id
    )
    message_id = _coerce_str(
        data.get("message_id")
        or payload_obj.get("message_id")
        or data.get("dedupe_id")
        or payload_obj.get("dedupe_id")
    )
    dedupe_id = _shorten(
        _coerce_str(data.get("dedupe_id")) or message_id or event_id, MAX_DEDUPE_ID_LENGTH
    )
    group_id = _sanitize_group_id(
        _coerce_str(data.get("group_id")) or conversation_id, default_group_id
    )
    source_value = (
        _coerce_str(data.get("source")) or _coerce_str(payload_obj.get("source")) or source
    )

    return EventEnvelope(
        event_id=event_id,
        received_at=received_at,
        group_id=group_id,
        dedupe_id=dedupe_id,
        payload=payload_obj,
        source=source_value,
        conversation_id=conversation_id,
        message_id=message_id,
    )
