"""
LLM-based routing module (advisory mode + roadmap-to-primary scaffold).

This module provides OpenAI-based intent classification and department routing
as an advisory layer over the existing deterministic router.

Key design principles:
- Fail-closed gating: network calls only when all safety gates pass
- Advisory by default: LLM suggestions are logged/persisted but not used for routing
- Roadmap-to-primary: OPENAI_ROUTING_PRIMARY flag enables LLM routing when
  confidence >= threshold and intent+department are valid
- No secrets or reply bodies in logs (only lengths/fingerprints)

See: docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from richpanel_middleware.automation.router import (
    DEPARTMENTS,
    INTENT_TO_DEPARTMENT,
    RoutingDecision,
    classify_routing,
)
from richpanel_middleware.integrations.openai import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    OpenAIClient,
    OpenAIRequestError,
)

LOGGER = logging.getLogger(__name__)

# ============================================================================
# Configuration (environment-based, fail-closed defaults)
# ============================================================================

DEFAULT_ROUTING_MODEL = "gpt-5.2-chat-latest"
DEFAULT_ROUTING_TEMPERATURE = 0.0
DEFAULT_ROUTING_MAX_TOKENS = 256
DEFAULT_CONFIDENCE_THRESHOLD = 0.85

# Roadmap flag: when True, use LLM routing as primary (if confidence passes)
# OFF by default -- enable only for evaluation/dev environments
OPENAI_ROUTING_PRIMARY_DEFAULT = False


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_openai_routing_primary() -> bool:
    """Check if LLM routing should be used as primary (roadmap feature)."""
    return _to_bool(
        os.environ.get("OPENAI_ROUTING_PRIMARY"),
        default=OPENAI_ROUTING_PRIMARY_DEFAULT,
    )


def get_confidence_threshold() -> float:
    """Get the confidence threshold for using LLM routing as primary."""
    raw = os.environ.get("OPENAI_ROUTING_CONFIDENCE_THRESHOLD")
    if raw:
        try:
            return float(raw)
        except (TypeError, ValueError):
            pass
    return DEFAULT_CONFIDENCE_THRESHOLD


# ============================================================================
# LLM Routing Response Schema
# ============================================================================

VALID_INTENTS = set(INTENT_TO_DEPARTMENT.keys())


@dataclass
class LLMRoutingSuggestion:
    """Structured LLM routing suggestion with confidence scoring."""

    intent: str
    department: str
    confidence: float
    reasoning: str = ""
    secondary_intents: List[str] = field(default_factory=list)
    raw_response: Dict[str, Any] = field(default_factory=dict)
    fingerprint: str = ""
    dry_run: bool = False
    gated_reason: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if the suggestion has valid intent and department."""
        return (
            self.intent in VALID_INTENTS
            and self.department in DEPARTMENTS
            and 0.0 <= self.confidence <= 1.0
        )

    def passes_threshold(self, threshold: Optional[float] = None) -> bool:
        """Check if confidence meets the threshold for primary routing."""
        threshold = threshold if threshold is not None else get_confidence_threshold()
        return self.is_valid() and self.confidence >= threshold


@dataclass
class RoutingArtifact:
    """Audit artifact capturing both deterministic and LLM routing decisions."""

    conversation_id: str
    event_id: str
    timestamp: str
    deterministic: Dict[str, Any]
    llm_suggestion: Optional[Dict[str, Any]] = None
    primary_source: str = "deterministic"
    final_routing: Optional[Dict[str, Any]] = None
    gating_report: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# Prompt Contract for Routing
# ============================================================================

ROUTING_SYSTEM_PROMPT = """You are a customer support routing classifier for an ecommerce company.
Your task is to analyze the customer message and determine:
1. The primary intent (what the customer is asking about)
2. The appropriate department to route to
3. Your confidence level (0.0 to 1.0)

Available intents: {intents}

Available departments: {departments}

You MUST respond with valid JSON in this exact format:
{{
  "intent": "<intent from the list above>",
  "department": "<department from the list above>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<brief explanation>",
  "secondary_intents": ["<optional additional intents>"]
}}

Rules:
- Only use intents and departments from the provided lists
- confidence should reflect how certain you are (0.8+ for clear cases, 0.5-0.8 for ambiguous)
- If you cannot determine the intent, use "unknown_other" with low confidence
- Do NOT include any personal data, order numbers, or customer details in your response"""


def _build_routing_prompt(customer_message: str) -> List[ChatMessage]:
    """Build the routing prompt messages."""
    intents_str = ", ".join(sorted(VALID_INTENTS))
    departments_str = ", ".join(sorted(DEPARTMENTS))

    system_content = ROUTING_SYSTEM_PROMPT.format(
        intents=intents_str,
        departments=departments_str,
    )

    # Truncate customer message to prevent prompt injection and reduce tokens
    truncated_message = customer_message[:2000] if len(customer_message) > 2000 else customer_message

    return [
        ChatMessage(role="system", content=system_content),
        ChatMessage(role="user", content=truncated_message),
    ]


def _compute_prompt_fingerprint(messages: List[ChatMessage], model: str) -> str:
    """Compute a fingerprint for the prompt (for audit, no secrets)."""
    payload = {
        "model": model,
        "message_count": len(messages),
        "system_length": len(messages[0].content) if messages else 0,
        "user_length": len(messages[1].content) if len(messages) > 1 else 0,
    }
    serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()[:16]


# ============================================================================
# Gating Logic
# ============================================================================


def _llm_routing_gating_check(
    *,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool,
    outbound_enabled: bool,
) -> Optional[str]:
    """
    Check all gates for LLM routing. Returns the blocking reason or None if allowed.

    Fail-closed: all gates must pass for network call to proceed.
    """
    if safe_mode:
        return "safe_mode"
    if not automation_enabled:
        return "automation_disabled"
    if not allow_network:
        return "network_disabled"
    if not outbound_enabled:
        return "outbound_disabled"
    return None


# ============================================================================
# LLM Routing Core
# ============================================================================


def _parse_llm_response(response: ChatCompletionResponse) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Parse and validate the LLM response JSON.

    Returns (parsed_dict, error_reason) - error_reason is None on success.
    """
    if response.dry_run or not response.message:
        return {}, response.reason or "dry_run"

    content = response.message.strip()

    # Try to extract JSON from the response (handle markdown code blocks)
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if json_match:
        content = json_match.group(1).strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {}, "invalid_json"

    if not isinstance(parsed, dict):
        return {}, "not_a_dict"

    # Validate required fields
    intent = parsed.get("intent")
    department = parsed.get("department")
    confidence = parsed.get("confidence")

    if not intent or not isinstance(intent, str):
        return {}, "missing_intent"
    if not department or not isinstance(department, str):
        return {}, "missing_department"
    if confidence is None:
        return {}, "missing_confidence"

    try:
        confidence = float(confidence)
        if not (0.0 <= confidence <= 1.0):
            return {}, "confidence_out_of_range"
    except (TypeError, ValueError):
        return {}, "invalid_confidence"

    # Validate against allowlists
    if intent not in VALID_INTENTS:
        parsed["_original_intent"] = intent
        parsed["intent"] = "unknown_other"
        parsed["_validation_note"] = f"intent '{intent}' not in allowlist"

    if department not in DEPARTMENTS:
        parsed["_original_department"] = department
        # Map intent to department if possible
        parsed["department"] = INTENT_TO_DEPARTMENT.get(parsed["intent"], "Email Support Team")
        parsed["_validation_note"] = parsed.get("_validation_note", "") + f"; department '{department}' not in allowlist"

    return parsed, None


def suggest_llm_routing(
    customer_message: str,
    *,
    conversation_id: str,
    event_id: str,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool = False,
    outbound_enabled: bool = False,
    client: Optional[OpenAIClient] = None,
) -> LLMRoutingSuggestion:
    """
    Get an LLM-based routing suggestion.

    This function is fail-closed:
    - If any gate fails, returns a dry-run suggestion with gated_reason
    - If the LLM call fails, returns a suggestion with low confidence
    - Never logs secrets or full message bodies

    Args:
        customer_message: The customer message to classify
        conversation_id: For audit/correlation
        event_id: For audit/correlation
        safe_mode: If True, block network calls
        automation_enabled: If False, block network calls
        allow_network: If False, block network calls
        outbound_enabled: If False, block network calls
        client: Optional OpenAI client (for testing)

    Returns:
        LLMRoutingSuggestion with the classification or dry-run result
    """
    model = os.environ.get("OPENAI_MODEL", DEFAULT_ROUTING_MODEL)
    messages = _build_routing_prompt(customer_message)
    fingerprint = _compute_prompt_fingerprint(messages, model)

    # Check gates
    gated_reason = _llm_routing_gating_check(
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        outbound_enabled=outbound_enabled,
    )

    if gated_reason:
        LOGGER.info(
            "llm_routing.gated",
            extra={
                "event_id": event_id,
                "conversation_id": conversation_id,
                "reason": gated_reason,
                "fingerprint": fingerprint,
                "message_length": len(customer_message),
            },
        )
        return LLMRoutingSuggestion(
            intent="unknown",
            department="Email Support Team",
            confidence=0.0,
            reasoning="",
            fingerprint=fingerprint,
            dry_run=True,
            gated_reason=gated_reason,
        )

    # Build and send request
    openai_client = client or OpenAIClient(allow_network=True)

    request = ChatCompletionRequest(
        model=model,
        messages=messages,
        temperature=DEFAULT_ROUTING_TEMPERATURE,
        max_tokens=DEFAULT_ROUTING_MAX_TOKENS,
        metadata={"conversation_id": conversation_id, "event_id": event_id},
    )

    try:
        response = openai_client.chat_completion(
            request,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
        )
    except OpenAIRequestError as exc:
        LOGGER.warning(
            "llm_routing.request_failed",
            extra={
                "event_id": event_id,
                "conversation_id": conversation_id,
                "fingerprint": fingerprint,
                "error": str(exc)[:200],
            },
        )
        return LLMRoutingSuggestion(
            intent="unknown",
            department="Email Support Team",
            confidence=0.0,
            reasoning="llm_request_failed",
            fingerprint=fingerprint,
            dry_run=False,
            gated_reason="request_failed",
        )

    # Parse response (no secrets or full bodies in logs)
    parsed, parse_error = _parse_llm_response(response)

    if parse_error:
        LOGGER.warning(
            "llm_routing.parse_failed",
            extra={
                "event_id": event_id,
                "conversation_id": conversation_id,
                "fingerprint": fingerprint,
                "parse_error": parse_error,
                "response_length": len(response.message or ""),
            },
        )
        return LLMRoutingSuggestion(
            intent="unknown",
            department="Email Support Team",
            confidence=0.0,
            reasoning=f"parse_failed: {parse_error}",
            fingerprint=fingerprint,
            dry_run=response.dry_run,
            gated_reason=parse_error,
        )

    # Build successful suggestion
    suggestion = LLMRoutingSuggestion(
        intent=parsed.get("intent", "unknown"),
        department=parsed.get("department", "Email Support Team"),
        confidence=float(parsed.get("confidence", 0.0)),
        reasoning=parsed.get("reasoning", "")[:500],  # Truncate for safety
        secondary_intents=parsed.get("secondary_intents", [])[:3],  # Limit
        raw_response={
            "status_code": response.status_code,
            "model": response.model,
            "dry_run": response.dry_run,
        },
        fingerprint=fingerprint,
        dry_run=response.dry_run,
    )

    LOGGER.info(
        "llm_routing.suggestion",
        extra={
            "event_id": event_id,
            "conversation_id": conversation_id,
            "intent": suggestion.intent,
            "department": suggestion.department,
            "confidence": suggestion.confidence,
            "fingerprint": fingerprint,
            "is_valid": suggestion.is_valid(),
            "dry_run": suggestion.dry_run,
        },
    )

    return suggestion


# ============================================================================
# Dual Routing (Deterministic + LLM Advisory)
# ============================================================================


def compute_dual_routing(
    payload: Dict[str, Any],
    *,
    conversation_id: str,
    event_id: str,
    safe_mode: bool,
    automation_enabled: bool,
    allow_network: bool = False,
    outbound_enabled: bool = False,
    client: Optional[OpenAIClient] = None,
) -> Tuple[RoutingDecision, RoutingArtifact]:
    """
    Compute both deterministic and LLM routing, returning the final decision and audit artifact.

    Pipeline:
    1. Always compute deterministic routing (baseline)
    2. Compute LLM routing suggestion (dry-run if gated)
    3. Decide which to use based on OPENAI_ROUTING_PRIMARY flag and confidence
    4. Build audit artifact for persistence

    Returns:
        (final_routing_decision, audit_artifact)
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Step 1: Deterministic routing (always computed)
    deterministic = classify_routing(payload)

    # Extract customer message for LLM
    from richpanel_middleware.automation.router import extract_customer_message
    customer_message = extract_customer_message(payload, default="")

    # Step 2: LLM routing suggestion
    llm_suggestion = suggest_llm_routing(
        customer_message,
        conversation_id=conversation_id,
        event_id=event_id,
        safe_mode=safe_mode,
        automation_enabled=automation_enabled,
        allow_network=allow_network,
        outbound_enabled=outbound_enabled,
        client=client,
    )

    # Step 3: Decide primary source
    primary_source = "deterministic"
    final_routing = deterministic

    if get_openai_routing_primary():
        threshold = get_confidence_threshold()
        if llm_suggestion.passes_threshold(threshold):
            primary_source = "llm"
            # Build RoutingDecision from LLM suggestion
            final_routing = RoutingDecision(
                category=deterministic.category,  # Preserve category from deterministic
                tags=[
                    "mw-routing-applied",
                    f"mw-intent-{llm_suggestion.intent}",
                    "mw-llm-routed",
                ],
                reason=f"llm_routing (confidence={llm_suggestion.confidence:.2f})",
                department=llm_suggestion.department,
                intent=llm_suggestion.intent,
            )
            LOGGER.info(
                "llm_routing.primary_selected",
                extra={
                    "event_id": event_id,
                    "conversation_id": conversation_id,
                    "confidence": llm_suggestion.confidence,
                    "threshold": threshold,
                    "intent": llm_suggestion.intent,
                    "department": llm_suggestion.department,
                },
            )
        else:
            LOGGER.info(
                "llm_routing.fallback_to_deterministic",
                extra={
                    "event_id": event_id,
                    "conversation_id": conversation_id,
                    "confidence": llm_suggestion.confidence,
                    "threshold": threshold,
                    "is_valid": llm_suggestion.is_valid(),
                    "gated_reason": llm_suggestion.gated_reason,
                },
            )

    # Step 4: Build audit artifact
    gating_report = {
        "safe_mode": safe_mode,
        "automation_enabled": automation_enabled,
        "allow_network": allow_network,
        "outbound_enabled": outbound_enabled,
        "openai_routing_primary": get_openai_routing_primary(),
        "confidence_threshold": get_confidence_threshold(),
        "llm_gated_reason": llm_suggestion.gated_reason,
    }

    artifact = RoutingArtifact(
        conversation_id=conversation_id,
        event_id=event_id,
        timestamp=timestamp,
        deterministic=asdict(deterministic),
        llm_suggestion={
            "intent": llm_suggestion.intent,
            "department": llm_suggestion.department,
            "confidence": llm_suggestion.confidence,
            "is_valid": llm_suggestion.is_valid(),
            "dry_run": llm_suggestion.dry_run,
            "fingerprint": llm_suggestion.fingerprint,
            "gated_reason": llm_suggestion.gated_reason,
        },
        primary_source=primary_source,
        final_routing=asdict(final_routing),
        gating_report=gating_report,
    )

    return final_routing, artifact


__all__ = [
    "OPENAI_ROUTING_PRIMARY_DEFAULT",
    "LLMRoutingSuggestion",
    "RoutingArtifact",
    "compute_dual_routing",
    "get_confidence_threshold",
    "get_openai_routing_primary",
    "suggest_llm_routing",
]