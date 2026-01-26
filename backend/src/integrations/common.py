from __future__ import annotations

from typing import Optional

PRODUCTION_ENVIRONMENTS = {"prod", "production"}
PROD_WRITE_ACK_ENV = "MW_PROD_WRITES_ACK"
PROD_WRITE_ACK_PHRASE = "I_UNDERSTAND_PROD_WRITES"


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


__all__ = [
    "PRODUCTION_ENVIRONMENTS",
    "PROD_WRITE_ACK_ENV",
    "PROD_WRITE_ACK_PHRASE",
    "prod_write_acknowledged",
]
