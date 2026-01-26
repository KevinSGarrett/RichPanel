from __future__ import annotations

import os
from typing import Optional, Tuple

PRODUCTION_ENVIRONMENTS = {"prod", "production"}
PROD_WRITE_ACK_ENV = "MW_PROD_WRITES_ACK"
PROD_WRITE_ACK_PHRASE = "I_UNDERSTAND_PROD_WRITES"
ENV_RESOLUTION_ORDER = (
    "RICHPANEL_ENV",
    "RICH_PANEL_ENV",
    "MW_ENV",
    "ENV",
    "ENVIRONMENT",
)


def _to_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def prod_write_acknowledged(value: Optional[str]) -> bool:
    if value is None:
        return False
    if _to_bool(value):
        return True
    return str(value).strip().upper() == PROD_WRITE_ACK_PHRASE


def resolve_env_name() -> Tuple[str, Optional[str]]:
    raw = None
    source = None
    for key in ENV_RESOLUTION_ORDER:
        value = os.environ.get(key)
        if value:
            raw = value
            source = key
            break
    if raw is None:
        raw = "local"
    value = str(raw).strip().lower() or "local"
    return value, source


__all__ = [
    "ENV_RESOLUTION_ORDER",
    "PRODUCTION_ENVIRONMENTS",
    "PROD_WRITE_ACK_ENV",
    "PROD_WRITE_ACK_PHRASE",
    "prod_write_acknowledged",
    "resolve_env_name",
]
