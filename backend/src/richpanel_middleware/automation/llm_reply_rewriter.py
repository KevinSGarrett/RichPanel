from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from richpanel_middleware.integrations.openai import (
    ChatCompletionRequest,
    ChatMessage,
    OpenAIClient,
    OpenAIRequestError,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_REPLY_MODEL = "gpt-5.2-chat-latest"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 256
OPENAI_REPLY_REWRITE_ENABLED_DEFAULT = False

_SYSTEM_PROMPT = """You are a guardrailed editor for ecommerce customer support.
- Rewrite the reply for clarity and empathy.
- Do NOT add new promises, discounts, or tracking details.
- Keep all factual statements unchanged.
- Keep length under 1000 characters.
- If the draft already looks safe, return it unchanged.

Respond ONLY with compact JSON:
{"body": "<rewritten reply text>", "confidence": <0-1 float>, "risk_flag": <true|false>}
"""


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _fingerprint(obj: Any, *, length: int = 12) -> str:
    try:
        serialized = json.dumps(obj, sort_keys=True, default=str)
    except Exception:
        serialized = str(obj)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:length]


def _rewrite_block_reason(
    *,
    rewrite_enabled: bool,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
) -> Optional[str]:
    if not rewrite_enabled:
        return "rewrite_disabled"
    if not outbound_enabled:
        return "outbound_disabled"
    if safe_mode:
        return "safe_mode"
    if not automation_enabled:
        return "automation_disabled"
    if not allow_network:
        return "network_disabled"
    return None


def _build_user_prompt(draft_reply: Dict[str, Any], order_summary: Dict[str, Any]) -> str:
    body = draft_reply.get("body") or ""
    safe_summary = {
        "status": order_summary.get("status"),
        "eta": order_summary.get("eta") or order_summary.get("delivery_estimate"),
        "id_hash": _fingerprint(order_summary.get("id")),
    }
    return json.dumps({"draft_reply": body, "order_summary": safe_summary}, default=str)


def _parse_response(message: str) -> Optional[Dict[str, Any]]:
    try:
        parsed = json.loads(message)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    body = parsed.get("body")
    if not body or not isinstance(body, str):
        return None
    confidence = parsed.get("confidence")
    if confidence is not None:
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = None
    risk_flag = bool(parsed.get("risk_flag"))
    result: Dict[str, Any] = {"body": body}
    if confidence is not None:
        result["confidence"] = confidence
    result["risk_flag"] = risk_flag
    return result


@dataclass
class RewriteResult:
    reply: Dict[str, Any]
    used_llm: bool
    reason: str
    dry_run: bool
    prompt_fingerprint: str
    response_fingerprint: Optional[str] = None

    def log_record(self) -> Dict[str, Any]:
        return {
            "used_llm": self.used_llm,
            "reason": self.reason,
            "dry_run": self.dry_run,
            "prompt_fingerprint": self.prompt_fingerprint,
            "response_fingerprint": self.response_fingerprint,
            "has_reply": bool(self.reply),
        }


def rewrite_order_status_reply(
    draft_reply: Dict[str, Any],
    order_summary: Dict[str, Any],
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
    rewrite_enabled: Optional[bool] = None,
    client: Optional[OpenAIClient] = None,
) -> RewriteResult:
    """
    Attempt to rewrite the deterministic order-status reply with an LLM.

    Fail-closed:
    - Disabled by default via OPENAI_REPLY_REWRITE_ENABLED (False)
    - Requires outbound_enabled, allow_network, automation_enabled, and safe_mode == False
    - On any error or risk flag, returns the original draft reply.
    """
    rewrite_enabled = (
        rewrite_enabled
        if rewrite_enabled is not None
        else _to_bool(
            os.environ.get("OPENAI_REPLY_REWRITE_ENABLED"),
            default=OPENAI_REPLY_REWRITE_ENABLED_DEFAULT,
        )
    )
    prompt_fingerprint = _fingerprint(
        {
            "draft_reply": draft_reply.get("body"),
            "order_summary": {
                "status": order_summary.get("status"),
                "eta": order_summary.get("eta") or order_summary.get("delivery_estimate"),
                "id": order_summary.get("id"),
            },
        }
    )

    reason = _rewrite_block_reason(
        rewrite_enabled=rewrite_enabled,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        outbound_enabled=outbound_enabled,
    )
    if reason:
        return RewriteResult(
            reply=draft_reply,
            used_llm=False,
            reason=reason,
            dry_run=True,
            prompt_fingerprint=prompt_fingerprint,
        )

    client = client or OpenAIClient(allow_network=allow_network)
    request = ChatCompletionRequest(
        model=DEFAULT_REPLY_MODEL,
        messages=[
            ChatMessage(role="system", content=_SYSTEM_PROMPT),
            ChatMessage(role="user", content=_build_user_prompt(draft_reply, order_summary)),
        ],
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS,
        metadata={"feature": "reply_rewriter"},
    )

    try:
        response = client.chat_completion(
            request, safe_mode=safe_mode, automation_enabled=automation_enabled
        )
    except OpenAIRequestError:
        return RewriteResult(
            reply=draft_reply,
            used_llm=False,
            reason="exception",
            dry_run=True,
            prompt_fingerprint=prompt_fingerprint,
        )

    response_fingerprint = _fingerprint(response.raw) if response.raw else None

    if not response.message:
        return RewriteResult(
            reply=draft_reply,
            used_llm=False,
            reason="empty_response",
            dry_run=response.dry_run,
            prompt_fingerprint=prompt_fingerprint,
            response_fingerprint=response_fingerprint,
        )

    parsed = _parse_response(response.message)
    if not parsed:
        return RewriteResult(
            reply=draft_reply,
            used_llm=False,
            reason="invalid_response",
            dry_run=response.dry_run,
            prompt_fingerprint=prompt_fingerprint,
            response_fingerprint=response_fingerprint,
        )

    if parsed.get("risk_flag"):
        return RewriteResult(
            reply=draft_reply,
            used_llm=False,
            reason="risk_flagged",
            dry_run=response.dry_run,
            prompt_fingerprint=prompt_fingerprint,
            response_fingerprint=response_fingerprint,
        )

    rewritten_reply = dict(draft_reply)
    rewritten_reply["body"] = parsed["body"]
    if "confidence" in parsed:
        rewritten_reply["confidence"] = parsed["confidence"]

    return RewriteResult(
        reply=rewritten_reply,
        used_llm=not response.dry_run,
        reason="rewritten",
        dry_run=response.dry_run,
        prompt_fingerprint=prompt_fingerprint,
        response_fingerprint=response_fingerprint,
    )


__all__ = ["RewriteResult", "rewrite_order_status_reply"]
