from __future__ import annotations

import logging
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


def log_env_resolution_warning(
    logger: logging.Logger,
    *,
    service: str,
    env_source: Optional[str],
    environment: str,
) -> None:
    if env_source == "ENV":
        if environment in PRODUCTION_ENVIRONMENTS:
            logger.warning(
                f"{service}.env_resolution_from_env",
                extra={"environment": environment, "env_source": env_source},
            )
        return
    if (
        env_source is None
        and environment == "local"
        and (
            os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
            or os.environ.get("AWS_EXECUTION_ENV")
        )
    ):
        logger.warning(
            f"{service}.env_resolution_default_local",
            extra={"environment": environment, "env_source": env_source},
        )


__all__ = [
    "ENV_RESOLUTION_ORDER",
    "PRODUCTION_ENVIRONMENTS",
    "PROD_WRITE_ACK_ENV",
    "PROD_WRITE_ACK_PHRASE",
    "log_env_resolution_warning",
    "prod_write_acknowledged",
    "resolve_env_name",
]
