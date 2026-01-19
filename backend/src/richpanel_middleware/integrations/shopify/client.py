"""
Compatibility wrapper that re-exports the Shopify integration from the
shared `integrations` namespace.
"""

from __future__ import annotations

from integrations.shopify.client import (  # noqa: F401
    HttpTransport,
    ShopifyClient,
    ShopifyRequestError,
    ShopifyResponse,
    Transport,
    TransportError,
    TransportRequest,
    TransportResponse,
)

__all__ = [
    "ShopifyClient",
    "ShopifyRequestError",
    "ShopifyResponse",
    "Transport",
    "TransportRequest",
    "TransportResponse",
    "TransportError",
    "HttpTransport",
]
