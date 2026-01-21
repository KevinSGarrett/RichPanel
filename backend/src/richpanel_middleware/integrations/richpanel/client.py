from __future__ import annotations

import base64
import json
import logging
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

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


def _resolve_env_name() -> str:
    """Choose an environment name for secret lookup; defaults to 'local'."""
    raw = (
        os.environ.get("RICHPANEL_ENV")
        or os.environ.get("RICH_PANEL_ENV")
        or os.environ.get("MW_ENV")
        or os.environ.get("ENVIRONMENT")
        or "local"
    )
    value = str(raw).strip().lower() or "local"
    return value


READ_ONLY_ENVIRONMENTS = {"prod", "production", "staging"}


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


class RichpanelClient:
    """
    Minimal Richpanel API client with safe defaults.

    - API key is sourced from AWS Secrets Manager (rp-mw/<env>/richpanel/api_key).
    - Retries + backoff for 429/5xx and transport errors.
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
        self.environment = _resolve_env_name()
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
        self._api_key = api_key or os.environ.get("RICHPANEL_API_KEY_OVERRIDE")
        self._secrets_client_obj = None
        self._sleeper = sleeper or time.sleep
        self._rng = rng or random.random

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
        if (self.read_only or self._writes_disabled()) and method_upper not in {
            "GET",
            "HEAD",
        }:
            self._logger.warning(
                "richpanel.write_blocked",
                extra={
                    "method": method_upper,
                    "read_only": self.read_only,
                    "write_disabled": self._writes_disabled(),
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
        attempt = 1
        last_response: Optional[RichpanelResponse] = None

        while attempt <= self.max_attempts:
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
                if attempt >= self.max_attempts:
                    raise RichpanelRequestError(
                        f"Richpanel transport failed after {attempt} attempts"
                    ) from exc

                delay = self._compute_backoff(attempt, retry_after=None)
                self._sleep(delay)
                attempt += 1
                continue

            latency_ms = int((time.monotonic() - start) * 1000)
            response = self._to_response(transport_response, url)
            last_response = response

            should_retry, delay = self._should_retry(response, attempt)
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
            delay = self._compute_backoff(attempt, response.headers.get("Retry-After"))
            return True, delay
        return False, 0.0

    def _compute_backoff(self, attempt: int, retry_after: Optional[str]) -> float:
        if retry_after:
            try:
                parsed = float(retry_after)
                if parsed > 0:
                    return min(parsed, self.backoff_max_seconds)
            except (TypeError, ValueError):
                pass

        base = min(
            self.backoff_seconds * (2 ** (attempt - 1)), self.backoff_max_seconds
        )
        jitter = base * 0.25 * self._rng()
        return min(base + jitter, self.backoff_max_seconds)

    def _sleep(self, delay: float) -> None:
        try:
            self._sleeper(delay)
        except Exception:
            # Sleeper is best-effort; failures should not crash the worker.
            self._logger.warning("richpanel.sleep_failed", extra={"delay": delay})

    def _load_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        if boto3 is None:
            raise SecretLoadError(
                "boto3 is required to load the Richpanel API key; provide api_key or RICHPANEL_API_KEY_OVERRIDE for local runs."
            )

        try:
            response = self._secrets_client().get_secret_value(
                SecretId=self.api_key_secret_id
            )
        except (BotoCoreError, ClientError) as exc:
            raise SecretLoadError(
                "Unable to load Richpanel API key from Secrets Manager"
            ) from exc

        secret_value = response.get("SecretString")
        if secret_value is None and response.get("SecretBinary") is not None:
            secret_value = base64.b64decode(response["SecretBinary"]).decode("utf-8")

        if not secret_value:
            raise SecretLoadError("Richpanel API key secret is empty")
        assert isinstance(secret_value, str)

        self._api_key = secret_value
        assert self._api_key is not None
        return str(self._api_key)

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
]
