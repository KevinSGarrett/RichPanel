"""
Compatibility wrapper that re-exports the OpenAI integration from the
shared `integrations` namespace.
"""

from __future__ import annotations

from integrations.openai.client import (  # noqa: F401
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    HttpTransport,
    OpenAIClient,
    OpenAIConfigError,
    OpenAIRequestError,
    Transport,
    TransportError,
    TransportRequest,
    TransportResponse,
)

__all__ = [
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatMessage",
    "HttpTransport",
    "OpenAIClient",
    "OpenAIConfigError",
    "OpenAIRequestError",
    "Transport",
    "TransportError",
    "TransportRequest",
    "TransportResponse",
]
