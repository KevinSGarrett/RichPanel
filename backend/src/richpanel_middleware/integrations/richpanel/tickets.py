from __future__ import annotations

import logging
from dataclasses import dataclass
import urllib.parse
from typing import Any, Optional, Set

from richpanel_middleware.integrations.richpanel.client import (
    RichpanelExecutor,
    RichpanelRequestError,
    SecretLoadError,
    TransportError,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class TicketMetadata:
    """PII-safe ticket snapshot used for automation guards."""

    status: Optional[str]
    tags: Set[str]
    status_code: Optional[int] = None
    dry_run: bool = False
    state: Optional[str] = None


def _normalize_status(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        normalized = str(value).strip()
    except Exception:
        return None
    return normalized or None


def dedupe_tags(raw_tags: Any) -> Set[str]:
    if raw_tags is None:
        return set()
    candidates = raw_tags if isinstance(raw_tags, list) else [raw_tags]
    tags: Set[str] = set()
    for candidate in candidates:
        try:
            value = str(candidate).strip()
        except Exception:
            continue
        if value:
            tags.add(value)
    return tags


def get_ticket_metadata(
    conversation_id: str,
    executor: RichpanelExecutor,
    *,
    allow_network: bool,
) -> TicketMetadata:
    """
    Fetch ticket status + tags without logging bodies/PII.

    Raises RichpanelRequestError/SecretLoadError/TransportError on failure.
    """
    if hasattr(executor, "get_ticket_metadata"):
        upstream = executor.get_ticket_metadata(  # type: ignore[attr-defined]
            conversation_id, dry_run=not allow_network
        )
        if isinstance(upstream, TicketMetadata):
            return upstream
        return TicketMetadata(
            status=_normalize_status(getattr(upstream, "status", None)),
            tags=dedupe_tags(getattr(upstream, "tags", None)),
            status_code=getattr(upstream, "status_code", None),
            dry_run=bool(getattr(upstream, "dry_run", not allow_network)),
        )

    encoded_id = urllib.parse.quote(str(conversation_id), safe="")
    response = executor.execute(
        "GET",
        f"/v1/tickets/{encoded_id}",
        dry_run=not allow_network,
    )
    payload = response.json() or {}
    if not isinstance(payload, dict):
        payload = {}

    status = _normalize_status(payload.get("status") or payload.get("state"))
    state = _normalize_status(payload.get("state") or payload.get("status"))
    tags = dedupe_tags(payload.get("tags"))

    return TicketMetadata(
        status=status,
        tags=tags,
        status_code=response.status_code,
        dry_run=response.dry_run,
        state=state,
    )


__all__ = ["TicketMetadata", "dedupe_tags", "get_ticket_metadata"]

