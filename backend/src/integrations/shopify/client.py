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
class ShopifyResponse:
    status_code: int
    headers: Dict[str, str]
    body: bytes
    url: str
    dry_run: bool = False
    reason: Optional[str] = None

    def json(self) -> Any:
        try:
            payload = self.body.decode("utf-8") if isinstance(self.body, (bytes, bytearray)) else self.body
            return json.loads(payload)
        except Exception:
            return None


class Transport(Protocol):
    def send(self, request: TransportRequest) -> TransportResponse:
        ...


class TransportError(Exception):
    """Raised when the HTTP transport cannot complete the request."""


class ShopifyRequestError(Exception):
    """Raised when a Shopify request fails after retries."""

    def __init__(self, message: str, *, response: Optional[ShopifyResponse] = None) -> None:
        super().__init__(message)
        self.response = response


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
        except urllib.error.URLError as exc:  # pragma: no cover - exercised via higher-level tests
            raise TransportError(str(exc)) from exc


class ShopifyClient:
    """
    Offline-first Shopify Admin API client with safe defaults.

    - Dry-run by default (no network unless explicitly enabled).
    - Short-circuits when safe_mode is True, automation is disabled, network is
      disabled, or the access token is unavailable.
    - Retries 429/5xx and transport errors with jittered backoff.
    - Redacts Authorization headers in logs.
    - Access token is sourced from AWS Secrets Manager at
      rp-mw/<env>/shopify/admin_api_token (canonical, with a compatibility
      fallback to rp-mw/<env>/shopify/access_token).
    """

    def __init__(
        self,
        *,
        shop_domain: Optional[str] = None,
        api_version: Optional[str] = None,
        base_url: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret_id: Optional[str] = None,
        allow_network: Optional[bool] = None,
        timeout_seconds: Optional[float] = None,
        max_attempts: int = 3,
        backoff_seconds: float = 0.5,
        backoff_max_seconds: float = 4.0,
        transport: Optional[Transport] = None,
        logger: Optional[logging.Logger] = None,
        sleeper: Optional[Callable[[float], None]] = None,
        rng: Optional[Callable[[], float]] = None,
        secrets_client: Optional[Any] = None,
    ) -> None:
        self.environment = _resolve_env_name()
        self.shop_domain = (shop_domain or os.environ.get("SHOPIFY_SHOP_DOMAIN") or "example.myshopify.com").rstrip("/")
        version = (api_version or os.environ.get("SHOPIFY_API_VERSION") or "2024-01").strip("/")
        self.base_url = (base_url or f"https://{self.shop_domain}/admin/api/{version}").rstrip("/")
        canonical_secret = f"rp-mw/{self.environment}/shopify/admin_api_token"
        legacy_secret = f"rp-mw/{self.environment}/shopify/access_token"
        primary_secret = access_token_secret_id or os.environ.get("SHOPIFY_ACCESS_TOKEN_SECRET_ID") or canonical_secret
        candidates = [primary_secret]
        for secret_id in (canonical_secret, legacy_secret):
            if secret_id not in candidates:
                candidates.append(secret_id)

        self.access_token_secret_id = primary_secret
        self._secret_id_candidates: List[str] = candidates
        self.allow_network = (
            _to_bool(os.environ.get("SHOPIFY_OUTBOUND_ENABLED"), default=False)
            if allow_network is None
            else bool(allow_network)
        )
        self.timeout_seconds = float(timeout_seconds or os.environ.get("SHOPIFY_HTTP_TIMEOUT_SECONDS") or 5.0)
        self.max_attempts = max(1, int(os.environ.get("SHOPIFY_HTTP_MAX_ATTEMPTS", max_attempts)))
        self.backoff_seconds = float(os.environ.get("SHOPIFY_HTTP_BACKOFF_SECONDS", backoff_seconds))
        self.backoff_max_seconds = float(os.environ.get("SHOPIFY_HTTP_BACKOFF_MAX_SECONDS", backoff_max_seconds))
        self.transport = transport or HttpTransport()
        self._logger = logger or logging.getLogger(__name__)
        self._access_token = access_token or os.environ.get("SHOPIFY_ACCESS_TOKEN_OVERRIDE")
        self._secrets_client_obj = secrets_client
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
        safe_mode: bool = False,
        automation_enabled: bool = True,
    ) -> ShopifyResponse:
        url = self._build_url(path, params)
        body_bytes = self._encode_body(json_body)
        use_dry_run = self._resolve_dry_run(dry_run)

        reason = self._short_circuit_reason(safe_mode, automation_enabled, use_dry_run)
        if reason:
            self._logger.info(
                "shopify.dry_run",
                extra={"method": method.upper(), "url": url, "reason": reason, "dry_run": True},
            )
            return ShopifyResponse(
                status_code=0,
                headers={"x-dry-run": "1", "x-dry-run-reason": reason},
                body=b"",
                url=url,
                dry_run=True,
                reason=reason,
            )

        access_token, token_reason = self._load_access_token()
        if access_token is None:
            reason = token_reason or "missing_access_token"
            self._logger.warning(
                "shopify.missing_token",
                extra={"url": url, "reason": reason},
            )
            return ShopifyResponse(
                status_code=0,
                headers={"x-dry-run": "1", "x-dry-run-reason": reason},
                body=b"",
                url=url,
                dry_run=True,
                reason=reason,
            )

        request_headers = self._build_headers(headers, access_token, has_body=body_bytes is not None)
        attempt = 1
        last_response: Optional[ShopifyResponse] = None

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
                    "shopify.transport_error",
                    extra={"method": method.upper(), "url": url, "attempt": attempt},
                )
                if attempt >= self.max_attempts:
                    raise ShopifyRequestError(f"Shopify transport failed after {attempt} attempts") from exc

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
            )

            if should_retry and attempt < self.max_attempts:
                self._sleep(delay)
                attempt += 1
                continue

            if response.status_code >= 500 or response.status_code == 429:
                raise ShopifyRequestError(
                    f"Shopify request failed with status {response.status_code}",
                    response=response,
                )

            return response

        raise ShopifyRequestError(
            f"Shopify request exhausted retries (last status: {last_response.status_code if last_response else 'unknown'})",
            response=last_response,
        )

    def get_order(
        self,
        order_id: str,
        *,
        fields: Optional[List[str]] = None,
        dry_run: Optional[bool] = None,
        safe_mode: bool = False,
        automation_enabled: bool = True,
    ) -> ShopifyResponse:
        """
        Fetch a single order with optional field selection.
        Uses the primary request() entrypoint so all safety gates apply.
        """
        safe_order_id = urllib.parse.quote(str(order_id), safe="")
        params = None
        if fields:
            params = {"fields": ",".join(sorted(map(str, fields)))}

        return self.request(
            "GET",
            f"orders/{safe_order_id}.json",
            params=params,
            dry_run=dry_run,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
        )

    def _to_response(self, transport_response: TransportResponse, url: str) -> ShopifyResponse:
        return ShopifyResponse(
            status_code=transport_response.status_code,
            headers=transport_response.headers,
            body=transport_response.body,
            url=url,
            dry_run=False,
        )

    def _should_retry(self, response: ShopifyResponse, attempt: int) -> Tuple[bool, float]:
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

        base = min(self.backoff_seconds * (2 ** (attempt - 1)), self.backoff_max_seconds)
        jitter = base * 0.25 * self._rng()
        return min(base + jitter, self.backoff_max_seconds)

    def _sleep(self, delay: float) -> None:
        try:
            self._sleeper(delay)
        except Exception:
            # Sleeper is best-effort; failures should not crash the worker.
            self._logger.warning("shopify.sleep_failed", extra={"delay": delay})

    def _load_access_token(self) -> Tuple[Optional[str], Optional[str]]:
        if self._access_token:
            return self._access_token, None
        client = self._secrets_client_obj
        if client is None and boto3 is None:
            return None, "boto3_unavailable"
        if client is None:
            client = self._secrets_client()

        last_reason: Optional[str] = None

        for secret_id in self._secret_id_candidates:
            try:
                response = client.get_secret_value(SecretId=secret_id)  # type: ignore[attr-defined]
            except (BotoCoreError, ClientError, Exception):
                last_reason = "secret_lookup_failed"
                continue

            secret_value = response.get("SecretString")
            if secret_value is None and response.get("SecretBinary") is not None:
                secret_value = base64.b64decode(response["SecretBinary"]).decode("utf-8")

            if not secret_value:
                last_reason = "missing_access_token"
                continue

            self._access_token = secret_value
            self.access_token_secret_id = secret_id
            return self._access_token, None

        return None, last_reason or "missing_access_token"

    def _secrets_client(self):
        if self._secrets_client_obj is None:
            if boto3 is None:
                raise ShopifyRequestError("boto3 is required to create a secretsmanager client.")
            self._secrets_client_obj = boto3.client("secretsmanager")
        return self._secrets_client_obj

    def _build_headers(self, headers: Optional[Dict[str, str]], access_token: str, has_body: bool) -> Dict[str, str]:
        merged: Dict[str, str] = {
            "accept": "application/json",
            "x-shopify-access-token": access_token,
        }
        if has_body:
            merged["content-type"] = "application/json"
        if headers:
            for key in sorted(headers.keys()):
                merged[key] = headers[key]
            # Prevent accidental override of the access token.
            merged["x-shopify-access-token"] = access_token
        return merged

    def _encode_body(self, json_body: Optional[Any]) -> Optional[bytes]:
        if json_body is None:
            return None
        if isinstance(json_body, bytes):
            return json_body
        if isinstance(json_body, str):
            return json_body.encode("utf-8")
        return json.dumps(json_body, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _build_url(self, path: str, params: Optional[Dict[str, str]]) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = urllib.parse.urljoin(f"{self.base_url}/", normalized_path.lstrip("/"))
        if params:
            query = urllib.parse.urlencode(sorted(params.items()))
            url = f"{url}?{query}"
        return url

    def _log_response(
        self,
        method: str,
        response: ShopifyResponse,
        latency_ms: int,
        attempt: int,
        retry_in: Optional[float],
    ) -> None:
        extra = {
            "method": method,
            "url": response.url,
            "status": response.status_code,
            "latency_ms": latency_ms,
            "attempt": attempt,
            "dry_run": response.dry_run,
        }
        if retry_in is not None:
            extra["retry_in"] = retry_in
            self._logger.warning("shopify.retry", extra=extra)
        else:
            self._logger.info("shopify.response", extra=extra)

    def _resolve_dry_run(self, override: Optional[bool]) -> bool:
        if override is not None:
            return bool(override)
        return not self.allow_network

    def _short_circuit_reason(self, safe_mode: bool, automation_enabled: bool, dry_run: bool) -> Optional[str]:
        if safe_mode:
            return "safe_mode"
        if not automation_enabled:
            return "automation_disabled"
        if not self.allow_network:
            return "network_disabled"
        if dry_run:
            return "dry_run_forced"
        return None

    @staticmethod
    def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
        redacted = dict(headers or {})
        for key in ["x-shopify-access-token", "X-Shopify-Access-Token", "authorization", "Authorization"]:
            if key in redacted:
                redacted[key] = "***"
        return redacted


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

