from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from richpanel_middleware.integrations.openai import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    OpenAIClient,
)

ORDER_STATUS_SYSTEM_PROMPT = (
    "You are a Richpanel copilot that reports ecommerce order status using the provided context JSON. "
    "Do not invent data; prefer concise status + ETA. Context: {context}"
)


@dataclass
class PromptConfig:
    model: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    temperature: float = 0.0
    max_tokens: int = 256


@dataclass
class OrderStatusPromptInput:
    name: str
    conversation_id: str
    customer_message: str
    order_summary: Dict[str, Any]
    customer_profile: Optional[Dict[str, Any]] = None


@dataclass
class PromptContract:
    name: str
    messages: List[ChatMessage]
    model: str
    temperature: float
    max_tokens: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_request(self) -> ChatCompletionRequest:
        return ChatCompletionRequest(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            metadata=self.metadata,
        )


@dataclass
class OfflineEvalResult:
    fixture_name: str
    request: ChatCompletionRequest
    response: ChatCompletionResponse
    fingerprint: str


def _sorted_json(value: Dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def prompt_fingerprint(contract: PromptContract) -> str:
    payload = {
        "messages": [{"role": m.role, "content": m.content} for m in contract.messages],
        "model": contract.model,
        "temperature": contract.temperature,
        "max_tokens": contract.max_tokens,
        "metadata": contract.metadata,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(serialized).hexdigest()


def build_order_status_contract(
    prompt_input: OrderStatusPromptInput, *, config: Optional[PromptConfig] = None
) -> PromptContract:
    cfg = config or PromptConfig()
    context_json = _sorted_json(
        {
            "customer_profile": prompt_input.customer_profile or {},
            "order_summary": prompt_input.order_summary or {},
        }
    )
    messages = [
        ChatMessage(
            role="system",
            content=ORDER_STATUS_SYSTEM_PROMPT.format(context=context_json),
        ),
        ChatMessage(role="user", content=prompt_input.customer_message.strip()),
    ]
    metadata = {"conversation_id": prompt_input.conversation_id}
    order_id = prompt_input.order_summary.get("id")
    if order_id:
        metadata["order_id"] = order_id

    return PromptContract(
        name=prompt_input.name,
        messages=messages,
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        metadata=metadata,
    )


def load_order_status_fixtures(path: Path) -> List[OrderStatusPromptInput]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    fixtures: List[OrderStatusPromptInput] = []
    for item in raw:
        fixtures.append(
            OrderStatusPromptInput(
                name=item["name"],
                conversation_id=item["conversation_id"],
                customer_message=item["customer_message"],
                order_summary=item.get("order_summary") or {},
                customer_profile=item.get("customer_profile") or {},
            )
        )
    return fixtures


def run_offline_order_status_eval(
    fixtures: Sequence[OrderStatusPromptInput],
    *,
    client: Optional[OpenAIClient] = None,
    safe_mode: bool = True,
    automation_enabled: bool = False,
) -> List[OfflineEvalResult]:
    """
    Offline harness: builds prompts deterministically and short-circuits model calls.
    """
    client = client or OpenAIClient()
    results: List[OfflineEvalResult] = []

    for fixture in fixtures:
        contract = build_order_status_contract(fixture)
        request = contract.to_request()
        response = client.chat_completion(request, safe_mode=safe_mode, automation_enabled=automation_enabled)
        results.append(
            OfflineEvalResult(
                fixture_name=fixture.name,
                request=request,
                response=response,
                fingerprint=prompt_fingerprint(contract),
            )
        )

    return results


__all__ = [
    "ORDER_STATUS_SYSTEM_PROMPT",
    "OrderStatusPromptInput",
    "OfflineEvalResult",
    "PromptConfig",
    "PromptContract",
    "build_order_status_contract",
    "load_order_status_fixtures",
    "prompt_fingerprint",
    "run_offline_order_status_eval",
]
