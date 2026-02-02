from __future__ import annotations

import base64
import json
import logging
import os
import random
import time
import email.utils
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

from integrations.common import (
    PROD_WRITE_ACK_ENV,
    PRODUCTION_ENVIRONMENTS,
    compute_retry_backoff,
    get_header_value,
    log_env_resolution_warning,
    prod_write_acknowledged,
    resolve_env_name,
)

try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Placeholder to allow offline tests without boto3."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _truncate(text: str, limit: int = 512) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


READ_ONLY_ENVIRONMENTS = {"prod", "production", "staging"}
TRACE_SAFE_SEGMENTS = {
    "api",
    "v1",
    "v2",
    "v3",
    "tickets",
    "ticket",
    "conversations",
    "conversation",
    "orders",
    "order",
    "number",
    "shipments",
    "shipment",
    "users",
    "user",
}

RICHPANEL_RETRY_AFTER_HEADERS = ("retry-after",)
RICHPANEL_RESET_HEADERS = (
    "x-ratelimit-reset",
    "x-rate-limit-reset",
    "ratelimit-reset",
    "rate-limit-reset",
    "x-richpanel-rate-limit-reset",
    "x-richpanel-reset",
    "x-rp-rate-limit-reset",
)


@dataclass
class TransportRequest:
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[bytes]
    timeout: float


@dataclass
class TransportResponse:
    status_code: int
    headers: Dict[str, str]
    body: bytes


@dataclass
class RichpanelResponse:
    status_code: int
    headers: Dict[str, str]
    body: bytes
    url: str
    dry_run: bool = False

    def json(self) -> Any:
        try:
            payload = (
                self.body.decode("utf-8")
                if isinstance(self.body, (bytes, bytearray))
                else self.body
            )
            return json.loads(payload)
        except Exception:
            return None


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        text = str(value).strip()
    except Exception:
        return None
    return text or None


def _normalize_tag_list(value: Any) -> List[str]:
    if value is None:
        candidates: List[Any] = []
    elif isinstance(value, list):
        candidates = value
    else:
        candidates = [value]

    tags: List[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        tag = _coerce_str(candidate)
        if not tag or tag in seen:
            continue
        tags.append(tag)
        seen.add(tag)
    return tags


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        seconds = float(value)
        if seconds > 0:
            return seconds
    except (TypeError, ValueError):
        pass
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed is None:
            return None
        seconds = parsed.timestamp() - time.time()
        return seconds if seconds > 0 else None
    except Exception:
        return None


def _parse_reset_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    now = time.time()
    if parsed > 10_000_000:
        delta = parsed - now
        return delta if delta > 0 else None
    return parsed


@dataclass
class TicketMetadata:
    """
    Minimal, PII-safe ticket metadata used for safety gates.

    NOTE: Do not store or log full ticket payloads (customer profile, messages, etc.).
    """

    ticket_id: str
    status: Optional[str] = None
    tags: List[str] = None  # type: ignore[assignment]
    conversation_no: Optional[int] = None

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = []


class TransportError(Exception):
    """Raised when the HTTP transport cannot complete the request."""


class SecretLoadError(Exception):
    """Raised when the Richpanel API key cannot be loaded."""


class RichpanelRequestError(Exception):
    """Raised when a Richpanel request fails after retries."""

    def __init__(
        self, message: str, *, response: Optional[RichpanelResponse] = None
    ) -> None:
        super().__init__(message)
        self.response = response


class RichpanelWriteDisabledError(RichpanelRequestError):
    """Raised when a Richpanel write is attempted while writes are disabled."""


class Transport(Protocol):
    def send(self, request: TransportRequest) -> TransportResponse: ...


class HttpTransport:
    """Minimal urllib-based transport to avoid external dependencies."""

    def send(self, request: TransportRequest) -> TransportResponse:
        req = urllib.request.Request(
            request.url,
            data=request.body,
            method=request.method.upper(),
            headers=request.headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=request.timeout) as resp:
                body = resp.read()
                headers = dict(resp.headers.items())
                status = resp.getcode() or 0
                return TransportResponse(status_code=status, headers=headers, body=body)
        except urllib.error.HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            headers = dict(exc.headers.items()) if exc.headers else {}
            return TransportResponse(status_code=exc.code, headers=headers, body=body)
        except urllib.error.URLError as exc:
            raise TransportError(str(exc)) from exc


class TokenBucketRateLimiter:
    """
    Thread-safe token bucket rate limiter for Richpanel API calls.

    Enforces a maximum request rate to stay under Richpanel's 50/30s quota.
    This is a GLOBAL limiter - all requests through any RichpanelClient
    instance share the same bucket when using the module-level instance.

    Default: 1.0 requests/second = 30 requests/30s = 40% headroom under limit
    """

    def __init__(
        self,
        rate: float = 1.0,
        capacity: float = 5.0,
        *,
        clock: Optional[Callable[[], float]] = None,
        sleeper: Optional[Callable[[float], None]] = None,
    ) -> None:
        """
        Args:
            rate: Tokens (requests) added per second. 1.0 = safe, 1.5 = aggressive.
            capacity: Maximum tokens to accumulate (burst allowance).
            clock: Time function (default: time.monotonic)
            sleeper: Sleep function (default: time.sleep)
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._clock = clock or time.monotonic
        self._last_refill = self._clock()
        self._lock = threading.Lock()
        self._sleeper = sleeper or time.sleep
        self._logger = logging.getLogger(__name__)
        if self._rate <= 0:
            self._logger.warning(
                "richpanel.rate_limiter_invalid_rate",
                extra={"rate": self._rate},
            )

        # Statistics for diagnostics
        self._total_requests = 0
        self._total_wait_seconds = 0.0
        self._waits_over_1s = 0

    def acquire(self, timeout: float = 60.0) -> bool:
        """
        Acquire a token (permission to make one request).

        Blocks until a token is available or timeout is reached.
        Returns True if token acquired, False if timeout.
        """
        start = self._clock()
        if self._rate <= 0:
            self._logger.warning(
                "richpanel.rate_limiter_invalid_rate",
                extra={"rate": self._rate},
            )
            return False
        while True:
            with self._lock:
                now = self._clock()
                elapsed = now - self._last_refill

                # Refill tokens based on elapsed time
                self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
                self._last_refill = now

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    wait_time = now - start
                    self._total_requests += 1
                    self._total_wait_seconds += wait_time
                    if wait_time > 1.0:
                        self._waits_over_1s += 1
                    return True

                # Calculate wait time for next token
                tokens_needed = 1.0 - self._tokens
                wait_for_token = tokens_needed / self._rate

            # Check timeout before sleeping
            elapsed_total = self._clock() - start
            if elapsed_total + wait_for_token > timeout:
                self._logger.warning(
                    "richpanel.rate_limiter.timeout",
                    extra={
                        "timeout": timeout,
                        "elapsed": elapsed_total,
                        "tokens": self._tokens,
                    },
                )
                return False

            # Sleep outside the lock to allow other threads to proceed
            sleep_time = min(wait_for_token, 0.1)
            self._sleeper(sleep_time)

    def get_stats(self) -> Dict[str, Any]:
        """Return rate limiter statistics for diagnostics."""
        with self._lock:
            return {
                "rate_rps": self._rate,
                "capacity": self._capacity,
                "current_tokens": round(self._tokens, 2),
                "total_requests": self._total_requests,
                "total_wait_seconds": round(self._total_wait_seconds, 2),
                "waits_over_1s": self._waits_over_1s,
                "avg_wait_ms": (
                    round((self._total_wait_seconds / self._total_requests) * 1000, 2)
                    if self._total_requests > 0
                    else 0.0
                ),
            }


# Module-level rate limiter instance (shared across all RichpanelClient instances)
_GLOBAL_RATE_LIMITER: Optional[TokenBucketRateLimiter] = None
_RATE_LIMITER_LOCK = threading.Lock()


def _get_global_rate_limiter() -> Optional[TokenBucketRateLimiter]:
    """
    Get or create the global rate limiter based on environment config.

    Configure via: RICHPANEL_RATE_LIMIT_RPS (default: 0 = disabled)

    Recommended values:
    - 1.0: Safe, 60% headroom (30/30s out of 50/30s limit)
    - 0.8: Conservative, 52% headroom (24/30s)
    - 1.5: Aggressive, only 10% headroom (45/30s) - NOT recommended

    IMPORTANT: This rate applies PER PROCESS. For Lambda with concurrency > 1,
    you must divide by concurrency:
    - Concurrency 1: RPS = 1.0
    - Concurrency 2: RPS = 0.5
    - Concurrency 3: RPS = 0.33
    """
    global _GLOBAL_RATE_LIMITER

    with _RATE_LIMITER_LOCK:
        if _GLOBAL_RATE_LIMITER is not None:
            return _GLOBAL_RATE_LIMITER

        rps_str = os.environ.get("RICHPANEL_RATE_LIMIT_RPS", "0")
        try:
            rps = float(rps_str)
        except (TypeError, ValueError):
            rps = 0.0

        if rps <= 0:
            return None

        _GLOBAL_RATE_LIMITER = TokenBucketRateLimiter(rate=rps, capacity=5.0)
        logging.getLogger(__name__).info(
            "richpanel.rate_limiter.initialized",
            extra={"rate_rps": rps, "capacity": 5.0},
        )
        return _GLOBAL_RATE_LIMITER


def get_rate_limiter_stats() -> Optional[Dict[str, Any]]:
    """Get current rate limiter statistics (for diagnostics/logging)."""
    limiter = _get_global_rate_limiter()
    return limiter.get_stats() if limiter else None


class RichpanelClient:
    """
    Minimal Richpanel API client with safe defaults.

    - API key is sourced from AWS Secrets Manager (rp-mw/<env>/richpanel/api_key).
    - Retries + backoff for 429/5xx and transport errors.
    - Optional client-side rate limiter via RICHPANEL_RATE_LIMIT_RPS.
    - Dry-run by default to avoid side effects until explicitly enabled.
    - Structured logging with redaction of secrets and large bodies.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_secret_id: Optional[str] = None,
        dry_run: Optional[bool] = None,
        read_only: Optional[bool] = None,
        timeout_seconds: Optional[float] = None,
        max_attempts: int = 3,
        backoff_seconds: float = 0.5,
        backoff_max_seconds: float = 4.0,
        transport: Optional[Transport] = None,
        logger: Optional[logging.Logger] = None,
        sleeper: Optional[Callable[[float], None]] = None,
        rng: Optional[Callable[[], float]] = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.environ.get("RICHPANEL_API_BASE_URL")
            or "https://api.richpanel.com"
        ).rstrip("/")
        self.environment, env_source = resolve_env_name()
        self.api_key_secret_id = (
            api_key_secret_id
            or os.environ.get("RICHPANEL_API_KEY_SECRET_ARN")
            or os.environ.get("RICHPANEL_API_KEY_SECRET_ID")
            or f"rp-mw/{self.environment}/richpanel/api_key"
        )
        self.dry_run = self._resolve_dry_run(dry_run)
        self.read_only = self._resolve_read_only(read_only)
        self.timeout_seconds = float(
            timeout_seconds or os.environ.get("RICHPANEL_HTTP_TIMEOUT_SECONDS") or 5.0
        )
        self.max_attempts = max(
            1, int(os.environ.get("RICHPANEL_HTTP_MAX_ATTEMPTS", max_attempts))
        )
        self.backoff_seconds = float(
            os.environ.get("RICHPANEL_HTTP_BACKOFF_SECONDS", backoff_seconds)
        )
        self.backoff_max_seconds = float(
            os.environ.get("RICHPANEL_HTTP_BACKOFF_MAX_SECONDS", backoff_max_seconds)
        )
        self.transport = transport or HttpTransport()
        self._logger = logger or logging.getLogger(__name__)
        log_env_resolution_warning(
            self._logger,
            service="richpanel",
            env_source=env_source,
            environment=self.environment,
        )
        self._api_key = (
            api_key
            or os.environ.get("RICHPANEL_API_KEY_OVERRIDE")
            or os.environ.get("RP_KEY")
        )
        self._trace_enabled = _to_bool(
            os.environ.get("RICHPANEL_TRACE_ENABLED"), default=False
        )
        self._request_trace: List[Dict[str, Any]] = []
        self._secrets_client_obj = None
        self._sleeper = sleeper or time.sleep
        self._rng = rng or random.random
        self._cooldown_until = 0.0
        self._cooldown_lock = threading.Lock()
        self._cooldown_multiplier = self._parse_cooldown_multiplier(
            os.environ.get("RICHPANEL_429_COOLDOWN_MULTIPLIER")
        )
        self._token_pool_enabled = _to_bool(
            os.environ.get("RICHPANEL_TOKEN_POOL_ENABLED"), default=False
        )
        self._token_pool_secret_ids = [
            secret_id.strip()
            for secret_id in (
                os.environ.get("RICHPANEL_TOKEN_POOL_SECRET_IDS", "") or ""
            ).split(",")
            if secret_id.strip()
        ]
        self._token_pool: List[str] = []
        self._token_pool_index = 0
        self._token_pool_lock = threading.Lock()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, str]] = None,
        json_body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[float] = None,
        dry_run: Optional[bool] = None,
        log_body_excerpt: bool = True,
    ) -> RichpanelResponse:
        method_upper = method.upper()
        writes_disabled = self._writes_disabled()
        prod_write_ack_required = self._prod_write_ack_required()
        if (
            (self.read_only or writes_disabled or prod_write_ack_required)
            and method_upper not in {"GET", "HEAD"}
        ):
            self._logger.warning(
                "richpanel.write_blocked",
                extra={
                    "method": method_upper,
                    "read_only": self.read_only,
                    "write_disabled": writes_disabled,
                    "prod_write_ack_required": prod_write_ack_required,
                    "environment": self.environment,
                },
            )
            raise RichpanelWriteDisabledError(
                "Richpanel writes are disabled; request blocked"
            )
        use_dry_run = self.dry_run if dry_run is None else bool(dry_run)
        url = self._build_url(path, params)
        body_bytes = self._encode_body(json_body)

        if use_dry_run:
            self._logger.info(
                "richpanel.dry_run",
                extra={"method": method.upper(), "url": url, "dry_run": True},
            )
            return RichpanelResponse(
                status_code=204,
                headers={"x-dry-run": "1"},
                body=b"",
                url=url,
                dry_run=True,
            )

        api_key = self._load_api_key()
        request_headers = self._merge_headers(
            headers, api_key, has_body=body_bytes is not None
        )
        rate_limiter = _get_global_rate_limiter()
        if rate_limiter is not None:
            if not rate_limiter.acquire(timeout=60.0):
                raise RichpanelRequestError(
                    "Rate limiter timeout: unable to acquire token within 60s"
                )
        attempt = 1
        last_response: Optional[RichpanelResponse] = None

        while attempt <= self.max_attempts:
            self._sleep_for_cooldown()
            start = time.monotonic()
            try:
                transport_response = self.transport.send(
                    TransportRequest(
                        method=method.upper(),
                        url=url,
                        headers=request_headers,
                        body=body_bytes,
                        timeout=float(timeout_seconds or self.timeout_seconds),
                    )
                )
            except TransportError as exc:
                self._logger.warning(
                    "richpanel.transport_error",
                    extra={"method": method.upper(), "url": url, "attempt": attempt},
                )
                delay = self._compute_backoff(attempt, retry_after=None)
                if self._trace_enabled:
                    self._record_trace(
                        method=method.upper(),
                        url=url,
                        status=0,
                        attempt=attempt,
                        retry_after=None,
                        retry_delay=delay,
                    )
                if attempt >= self.max_attempts:
                    raise RichpanelRequestError(
                        f"Richpanel transport failed after {attempt} attempts"
                    ) from exc

                self._sleep(delay)
                attempt += 1
                continue

            latency_ms = int((time.monotonic() - start) * 1000)
            response = self._to_response(transport_response, url)
            last_response = response

            should_retry, delay = self._should_retry(response, attempt)
            if should_retry and response.status_code == 429:
                self._register_cooldown(delay)
            retry_after_header = get_header_value(
                response.headers, RICHPANEL_RETRY_AFTER_HEADERS
            ) or get_header_value(response.headers, RICHPANEL_RESET_HEADERS)
            if self._trace_enabled:
                self._record_trace(
                    method=method.upper(),
                    url=url,
                    status=response.status_code,
                    attempt=attempt,
                    retry_after=retry_after_header,
                    retry_delay=delay if should_retry else None,
                )
            self._log_response(
                method.upper(),
                response,
                latency_ms,
                attempt,
                delay if should_retry else None,
                log_body_excerpt=log_body_excerpt,
            )

            if should_retry and attempt < self.max_attempts:
                self._sleep(delay)
                attempt += 1
                continue

            if response.status_code >= 500 or response.status_code == 429:
                raise RichpanelRequestError(
                    f"Richpanel request failed with status {response.status_code}",
                    response=response,
                )

            return response

        raise RichpanelRequestError(
            f"Richpanel request exhausted retries (last status: {last_response.status_code if last_response else 'unknown'})",
            response=last_response,
        )

    def get_ticket_metadata(
        self, ticket_id: str, *, dry_run: Optional[bool] = None
    ) -> TicketMetadata:
        """
        Fetch PII-safe ticket metadata for safety checks.

        Uses: GET /v1/tickets/{id}
        Returns only: status + tags (no messages/customer profile).
        """
        encoded_id = urllib.parse.quote(str(ticket_id), safe="")
        resp = self.request("GET", f"/v1/tickets/{encoded_id}", dry_run=dry_run)
        if resp.dry_run:
            return TicketMetadata(ticket_id=str(ticket_id), status=None, tags=[])

        if resp.status_code < 200 or resp.status_code >= 300:
            # Fail-closed: callers should treat this as an error and avoid outbound replies.
            raise RichpanelRequestError(
                f"Richpanel ticket metadata fetch failed with status {resp.status_code}",
                response=resp,
            )

        data = resp.json()
        if not isinstance(data, dict):
            raise RichpanelRequestError(
                "Richpanel ticket metadata fetch returned non-JSON body",
                response=resp,
            )

        ticket_candidate = data.get("ticket")
        ticket_obj = ticket_candidate if isinstance(ticket_candidate, dict) else data
        status = _coerce_str(ticket_obj.get("status") or ticket_obj.get("state"))
        tags = _normalize_tag_list(ticket_obj.get("tags"))
        conversation_no = ticket_obj.get("conversation_no")
        if conversation_no is not None:
            try:
                conversation_no = int(conversation_no)
            except (TypeError, ValueError):
                conversation_no = None
        return TicketMetadata(
            ticket_id=str(ticket_id),
            status=status,
            tags=tags,
            conversation_no=conversation_no,
        )

    def _to_response(
        self, transport_response: TransportResponse, url: str
    ) -> RichpanelResponse:
        return RichpanelResponse(
            status_code=transport_response.status_code,
            headers=transport_response.headers,
            body=transport_response.body,
            url=url,
            dry_run=False,
        )

    def _should_retry(
        self, response: RichpanelResponse, attempt: int
    ) -> Tuple[bool, float]:
        if response.status_code == 429 or 500 <= response.status_code < 600:
            retry_after = _parse_retry_after(
                get_header_value(response.headers, RICHPANEL_RETRY_AFTER_HEADERS)
            )
            if retry_after is None:
                retry_after = _parse_reset_after(
                    get_header_value(response.headers, RICHPANEL_RESET_HEADERS)
                )
            delay = self._compute_backoff(attempt, retry_after)
            return True, delay
        return False, 0.0

    def _compute_backoff(
        self, attempt: int, retry_after: Optional[float]
    ) -> float:
        backoff_max = self.backoff_max_seconds
        if retry_after is not None:
            backoff_max = max(backoff_max, retry_after)
        return compute_retry_backoff(
            attempt=attempt,
            retry_after=str(retry_after) if retry_after is not None else None,
            backoff_seconds=self.backoff_seconds,
            backoff_max_seconds=backoff_max,
            rng=self._rng,
            retry_after_jitter_ratio=0.1,
        )

    def _sleep(self, delay: float) -> None:
        try:
            self._sleeper(delay)
        except Exception:
            # Sleeper is best-effort; failures should not crash the worker.
            self._logger.warning("richpanel.sleep_failed", extra={"delay": delay})

    def _sleep_for_cooldown(self) -> None:
        try:
            with self._cooldown_lock:
                now = time.monotonic()
                if now >= self._cooldown_until:
                    return
                delay = self._cooldown_until - now
            if delay > 0:
                self._sleep(delay)
        except Exception:
            self._logger.warning("richpanel.cooldown_failed")

    def _register_cooldown(self, delay: float) -> None:
        if delay <= 0:
            return
        try:
            cooldown = delay * self._cooldown_multiplier
            with self._cooldown_lock:
                target = time.monotonic() + cooldown
                if target > self._cooldown_until:
                    self._cooldown_until = target
        except Exception:
            self._logger.warning("richpanel.cooldown_register_failed")

    def _record_trace(
        self,
        *,
        method: str,
        url: str,
        status: int,
        attempt: int,
        retry_after: Optional[str],
        retry_delay: Optional[float],
    ) -> None:
        try:
            timestamp = time.time()
        except Exception:
            timestamp = 0.0
        self._request_trace.append(
            {
                "timestamp": timestamp,
                "method": method,
                "path": _redact_url_path(url),
                "status": status,
                "attempt": attempt,
                "retry_after": retry_after,
                "retry_delay_seconds": retry_delay,
            }
        )

    def get_request_trace(self) -> List[Dict[str, Any]]:
        return list(self._request_trace)

    def clear_request_trace(self) -> None:
        self._request_trace = []

    def _load_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        if self._token_pool_enabled and self._token_pool_secret_ids:
            pool = self._load_token_pool()
            if not pool:
                raise SecretLoadError("Richpanel token pool is empty")
            return self._select_pool_key(pool)
        if boto3 is None:
            raise SecretLoadError(
                "boto3 is required to load the Richpanel API key; provide api_key or RICHPANEL_API_KEY_OVERRIDE for local runs."
            )
        secret_value = self._load_secret_value(self.api_key_secret_id)
        if not secret_value:
            raise SecretLoadError("Richpanel API key secret is empty")
        self._api_key = secret_value
        return str(self._api_key)

    def _load_token_pool(self) -> List[str]:
        if self._token_pool:
            return list(self._token_pool)
        if self._secrets_client_obj is None and boto3 is None:
            raise SecretLoadError(
                "boto3 is required to load the Richpanel token pool."
            )
        secrets: List[str] = []
        for secret_id in self._token_pool_secret_ids:
            value = self._load_secret_value(secret_id)
            if value:
                secrets.append(value)
            else:
                self._logger.warning(
                    "richpanel.token_pool_missing_secret",
                    extra={"secret_id": secret_id},
                )
        with self._token_pool_lock:
            if not self._token_pool:
                self._token_pool = secrets
        return list(self._token_pool)

    def _select_pool_key(self, pool: List[str]) -> str:
        with self._token_pool_lock:
            if not pool:
                raise SecretLoadError("Richpanel token pool is empty")
            selected = pool[self._token_pool_index]
            self._token_pool_index = (self._token_pool_index + 1) % len(pool)
            return selected

    def _load_secret_value(self, secret_id: str) -> Optional[str]:
        try:
            response = self._secrets_client().get_secret_value(SecretId=secret_id)
        except (BotoCoreError, ClientError) as exc:
            raise SecretLoadError(
                "Unable to load Richpanel API key from Secrets Manager"
            ) from exc
        secret_value = response.get("SecretString")
        if secret_value is None and response.get("SecretBinary") is not None:
            secret_value = base64.b64decode(response["SecretBinary"]).decode("utf-8")
        if not secret_value:
            return None
        return str(secret_value)

    def _parse_cooldown_multiplier(self, value: Optional[str]) -> float:
        if value is None:
            return 1.0
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            self._logger.warning(
                "richpanel.cooldown_multiplier_invalid",
                extra={"value": value},
            )
            return 1.0
        if parsed <= 0:
            self._logger.warning(
                "richpanel.cooldown_multiplier_invalid",
                extra={"value": value},
            )
            return 1.0
        return parsed

    def _secrets_client(self):
        if self._secrets_client_obj is None:
            if boto3 is None:
                raise SecretLoadError(
                    "boto3 is required to create a secretsmanager client."
                )
            self._secrets_client_obj = boto3.client("secretsmanager")
        return self._secrets_client_obj

    def _merge_headers(
        self, headers: Optional[Dict[str, str]], api_key: str, has_body: bool
    ) -> Dict[str, str]:
        merged: Dict[str, str] = {
            "accept": "application/json",
            "x-richpanel-key": api_key,
        }
        if has_body:
            merged["content-type"] = "application/json"
        if headers:
            merged.update(headers)
            # Prevent accidental override of the API key.
            merged["x-richpanel-key"] = api_key
        return merged

    def _encode_body(self, json_body: Optional[Any]) -> Optional[bytes]:
        if json_body is None:
            return None
        if isinstance(json_body, bytes):
            return json_body
        if isinstance(json_body, str):
            return json_body.encode("utf-8")
        return json.dumps(json_body).encode("utf-8")

    def _build_url(self, path: str, params: Optional[Dict[str, str]]) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = urllib.parse.urljoin(f"{self.base_url}/", normalized_path.lstrip("/"))
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"
        return url

    def _log_response(
        self,
        method: str,
        response: RichpanelResponse,
        latency_ms: int,
        attempt: int,
        retry_in: Optional[float],
        *,
        log_body_excerpt: bool,
    ) -> None:
        extra = {
            "method": method,
            "url": response.url,
            "status": response.status_code,
            "latency_ms": latency_ms,
            "attempt": attempt,
            "dry_run": response.dry_run,
            "body_len": len(response.body or b"") if log_body_excerpt else 0,
        }
        if retry_in is not None:
            extra["retry_in"] = retry_in
            self._logger.warning("richpanel.retry", extra=extra)
        else:
            self._logger.info("richpanel.response", extra=extra)

    def _excerpt_body(self, body: bytes) -> str:
        if not body:
            return ""
        try:
            return body.decode("utf-8")
        except Exception:
            return "<binary>"

    def _resolve_dry_run(self, override: Optional[bool]) -> bool:
        if override is not None:
            return bool(override)
        enabled = _to_bool(os.environ.get("RICHPANEL_OUTBOUND_ENABLED"), default=False)
        return not enabled

    def _resolve_read_only(self, override: Optional[bool]) -> bool:
        if override is not None:
            return bool(override)
        env_override = os.environ.get("RICHPANEL_READ_ONLY") or os.environ.get(
            "RICH_PANEL_READ_ONLY"
        )
        if env_override is not None:
            return _to_bool(env_override, default=False)
        return self.environment in READ_ONLY_ENVIRONMENTS

    def _prod_write_ack_required(self) -> bool:
        if self.environment not in PRODUCTION_ENVIRONMENTS:
            return False
        return not self._prod_write_acknowledged()

    @staticmethod
    def _prod_write_acknowledged() -> bool:
        return prod_write_acknowledged(os.environ.get(PROD_WRITE_ACK_ENV))

    @staticmethod
    def _writes_disabled() -> bool:
        return _to_bool(os.environ.get("RICHPANEL_WRITE_DISABLED"), default=False)

    @staticmethod
    def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
        redacted = dict(headers or {})
        if "x-richpanel-key" in redacted:
            redacted["x-richpanel-key"] = "***"
        return redacted


class RichpanelExecutor:
    """
    Thin wrapper that keeps outbound Richpanel calls in dry-run mode until a
    feature flag explicitly enables side effects.
    """

    def __init__(
        self,
        *,
        client: Optional[RichpanelClient] = None,
        outbound_enabled: Optional[bool] = None,
    ) -> None:
        self._outbound_enabled = self._resolve_outbound_enabled(outbound_enabled)
        self._client = client or RichpanelClient(dry_run=not self._outbound_enabled)

    def execute(self, method: str, path: str, **kwargs: Any) -> RichpanelResponse:
        """
        Dispatch a request through the underlying client, forcing dry-run when
        outbound is disabled unless explicitly overridden by caller.
        """
        requested_dry_run = kwargs.pop("dry_run", None)
        log_body_excerpt = kwargs.pop("log_body_excerpt", True)
        effective_dry_run = (
            not self._outbound_enabled
            if requested_dry_run is None
            else bool(requested_dry_run)
        )
        return self._client.request(
            method,
            path,
            dry_run=effective_dry_run,
            log_body_excerpt=log_body_excerpt,
            **kwargs,
        )

    def get_ticket_metadata(
        self, ticket_id: str, *, dry_run: Optional[bool] = None
    ) -> TicketMetadata:
        requested_dry_run = dry_run
        effective_dry_run = (
            not self._outbound_enabled
            if requested_dry_run is None
            else bool(requested_dry_run)
        )
        return self._client.get_ticket_metadata(ticket_id, dry_run=effective_dry_run)

    def _resolve_outbound_enabled(self, override: Optional[bool]) -> bool:
        if override is not None:
            return bool(override)
        return _to_bool(os.environ.get("RICHPANEL_OUTBOUND_ENABLED"), default=False)


def _redact_url_path(url: str) -> str:
    try:
        path = urllib.parse.urlparse(url).path or "/"
    except Exception:
        path = url or "/"
    segments = [segment for segment in path.split("/") if segment]
    redacted_segments: List[str] = []
    for segment in segments:
        lowered = segment.lower()
        if lowered in TRACE_SAFE_SEGMENTS or (segment.startswith("v") and segment[1:].isdigit()):
            redacted_segments.append(segment)
            continue
        if segment.isalpha() and len(segment) <= 32:
            redacted_segments.append(segment)
            continue
        redacted_segments.append("redacted")
    return "/" + "/".join(redacted_segments)


__all__ = [
    "RichpanelClient",
    "RichpanelExecutor",
    "RichpanelResponse",
    "TicketMetadata",
    "Transport",
    "TransportRequest",
    "TransportResponse",
    "TransportError",
    "SecretLoadError",
    "RichpanelRequestError",
    "RichpanelWriteDisabledError",
    "HttpTransport",
    "TokenBucketRateLimiter",
    "get_rate_limiter_stats",
]
