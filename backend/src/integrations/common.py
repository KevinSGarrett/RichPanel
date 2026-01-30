from __future__ import annotations

import logging
import os
from typing import Callable, Optional, Tuple

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


def prod_write_ack_matches(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value) == PROD_WRITE_ACK_PHRASE


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


def compute_retry_backoff(
    *,
    attempt: int,
    retry_after: Optional[str],
    backoff_seconds: float,
    backoff_max_seconds: float,
    rng: Callable[[], float],
    retry_after_jitter_ratio: float = 0.0,
) -> float:
    base = min(backoff_seconds * (2 ** (attempt - 1)), backoff_max_seconds)
    jitter = base * 0.25 * rng()
    candidate = base + jitter

    retry_after_value: Optional[float] = None
    if retry_after:
        try:
            parsed = float(retry_after)
            if parsed > 0:
                retry_after_value = parsed
                extra = parsed * retry_after_jitter_ratio * rng()
                candidate = max(candidate, parsed + extra)
        except (TypeError, ValueError):
            retry_after_value = None

    if backoff_max_seconds > 0:
        if retry_after_value is None or retry_after_value <= backoff_max_seconds:
            candidate = min(candidate, backoff_max_seconds)
    return candidate


__all__ = [
    "ENV_RESOLUTION_ORDER",
    "PRODUCTION_ENVIRONMENTS",
    "PROD_WRITE_ACK_ENV",
    "PROD_WRITE_ACK_PHRASE",
    "compute_retry_backoff",
    "log_env_resolution_warning",
    "prod_write_acknowledged",
    "prod_write_ack_matches",
    "resolve_env_name",
]
