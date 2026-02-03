from __future__ import annotations

import base64
import json
import logging
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

from integrations.common import (
    PROD_WRITE_ACK_ENV,
    PRODUCTION_ENVIRONMENTS,
    compute_retry_backoff,
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


def _redact_refresh_body(text: str) -> str:
    if not text:
        return text
    redacted = re.sub(r"[A-Fa-f0-9]{12,}", "***", text)
    return redacted




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
            payload = (
                self.body.decode("utf-8")
                if isinstance(self.body, (bytes, bytearray))
                else self.body
            )
            return json.loads(payload)
        except Exception:
            return None


@dataclass
class ShopifyTokenInfo:
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[float] = None
    raw_format: str = "plain"
    source_secret_id: Optional[str] = None

    def is_expired(self, *, skew_seconds: float = 60.0) -> bool:
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - skew_seconds)


class Transport(Protocol):
    def send(self, request: TransportRequest) -> TransportResponse: ...


class TransportError(Exception):
    """Raised when the HTTP transport cannot complete the request."""


class ShopifyRequestError(Exception):
    """Raised when a Shopify request fails after retries."""

    def __init__(
        self, message: str, *, response: Optional[ShopifyResponse] = None
    ) -> None:
        super().__init__(message)
        self.response = response


class ShopifyWriteDisabledError(ShopifyRequestError):
    """Raised when a Shopify write is attempted while writes are disabled."""


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
        except (
            urllib.error.URLError
        ) as exc:  # pragma: no cover - exercised via higher-level tests
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
        self.environment, env_source = resolve_env_name()
        self.shop_domain = (
            shop_domain
            or os.environ.get("SHOPIFY_SHOP_DOMAIN")
            or os.environ.get("SHOPIFY_SHOP")
            or "example.myshopify.com"
        ).rstrip("/")
        version = (
            api_version or os.environ.get("SHOPIFY_API_VERSION") or "2024-01"
        ).strip("/")
        self.base_url = (
            base_url or f"https://{self.shop_domain}/admin/api/{version}"
        ).rstrip("/")
        canonical_secret = f"rp-mw/{self.environment}/shopify/admin_api_token"
        legacy_secret = f"rp-mw/{self.environment}/shopify/access_token"
        primary_secret = (
            access_token_secret_id
            or os.environ.get("SHOPIFY_ACCESS_TOKEN_SECRET_ID")
            or canonical_secret
        )
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
        self.timeout_seconds = float(
            timeout_seconds or os.environ.get("SHOPIFY_HTTP_TIMEOUT_SECONDS") or 5.0
        )
        self.max_attempts = max(
            1, int(os.environ.get("SHOPIFY_HTTP_MAX_ATTEMPTS", max_attempts))
        )
        self.backoff_seconds = float(
            os.environ.get("SHOPIFY_HTTP_BACKOFF_SECONDS", backoff_seconds)
        )
        self.backoff_max_seconds = float(
            os.environ.get("SHOPIFY_HTTP_BACKOFF_MAX_SECONDS", backoff_max_seconds)
        )
        self.transport = transport or HttpTransport()
        self._logger = logger or logging.getLogger(__name__)
        log_env_resolution_warning(
            self._logger,
            service="shopify",
            env_source=env_source,
            environment=self.environment,
        )
        self._access_token = (
            access_token
            or os.environ.get("SHOPIFY_ACCESS_TOKEN_OVERRIDE")
            or os.environ.get("SHOPIFY_TOKEN")
        )
        self.refresh_token_secret_id = (
            os.environ.get("SHOPIFY_REFRESH_TOKEN_SECRET_ID")
            or f"rp-mw/{self.environment}/shopify/refresh_token"
        )
        self._refresh_token_override = os.environ.get("SHOPIFY_REFRESH_TOKEN_OVERRIDE")
        self._refresh_token_source: Optional[str] = None
        self.client_id_secret_id = (
            os.environ.get("SHOPIFY_CLIENT_ID_SECRET_ID")
            or f"rp-mw/{self.environment}/shopify/client_id"
        )
        self.client_secret_secret_id = (
            os.environ.get("SHOPIFY_CLIENT_SECRET_SECRET_ID")
            or f"rp-mw/{self.environment}/shopify/client_secret"
        )
        self._client_id = os.environ.get("SHOPIFY_CLIENT_ID_OVERRIDE")
        self._client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET_OVERRIDE")
        self._token_info: Optional[ShopifyTokenInfo] = None
        self._last_refresh_error: Optional[str] = None
        if self._access_token:
            self._token_info = ShopifyTokenInfo(
                access_token=str(self._access_token).strip(),
                refresh_token=None,
                expires_at=None,
                raw_format="override",
                source_secret_id=None,
            )
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
        method_upper = method.upper()
        url = self._build_url(path, params)
        body_bytes = self._encode_body(json_body)
        use_dry_run = self._resolve_dry_run(dry_run)

        reason = self._short_circuit_reason(safe_mode, automation_enabled, use_dry_run)
        if reason is None and self._prod_write_ack_required(method_upper):
            self._logger.warning(
                "shopify.write_blocked",
                extra={
                    "method": method_upper,
                    "url": url,
                    "reason": "prod_write_ack_required",
                    "environment": self.environment,
                },
            )
            raise ShopifyWriteDisabledError(
                "Shopify writes are disabled; request blocked"
            )
        if reason:
            self._logger.info(
                "shopify.dry_run",
                extra={
                    "method": method_upper,
                    "url": url,
                    "reason": reason,
                    "dry_run": True,
                },
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

        attempt = 1
        last_response: Optional[ShopifyResponse] = None
        refresh_attempted = False

        if (
            self._token_info
            and self._token_info.is_expired()
            and self._token_info.refresh_token
        ):
            refresh_attempted = True
            if self._refresh_access_token(self._token_info):
                access_token, _ = self._load_access_token(force_reload=True)
                if not access_token:
                    self._logger.warning(
                        "shopify.refresh_failed_pre_request",
                        extra={"secret_id": self.access_token_secret_id},
                    )
                    return ShopifyResponse(
                        status_code=0,
                        headers={
                            "x-dry-run": "1",
                            "x-dry-run-reason": "missing_access_token",
                        },
                        body=b"",
                        url=url,
                        dry_run=True,
                        reason="missing_access_token",
                    )
            else:
                self._logger.warning(
                    "shopify.refresh_failed_pre_request",
                    extra={"secret_id": self.access_token_secret_id},
                )

        request_headers = self._build_headers(
            headers, access_token, has_body=body_bytes is not None
        )

        while attempt <= self.max_attempts:
            start = time.monotonic()
            try:
                transport_response = self.transport.send(
                    TransportRequest(
                        method=method_upper,
                        url=url,
                        headers=request_headers,
                        body=body_bytes,
                        timeout=float(timeout_seconds or self.timeout_seconds),
                    )
                )
            except TransportError as exc:
                self._logger.warning(
                    "shopify.transport_error",
                    extra={"method": method_upper, "url": url, "attempt": attempt},
                )
                if attempt >= self.max_attempts:
                    raise ShopifyRequestError(
                        f"Shopify transport failed after {attempt} attempts"
                    ) from exc

                delay = self._compute_backoff(attempt, retry_after=None)
                self._sleep(delay)
                attempt += 1
                continue

            latency_ms = int((time.monotonic() - start) * 1000)
            response = self._to_response(transport_response, url)
            last_response = response

            if (
                response.status_code == 401
                and not refresh_attempted
                and self._token_info
                and self._token_info.refresh_token
            ):
                refreshed = self._refresh_access_token(self._token_info)
                refresh_attempted = True
                if refreshed:
                    access_token, _ = self._load_access_token(
                        force_reload=True
                    )
                    if access_token:
                        request_headers = self._build_headers(
                            headers, access_token, has_body=body_bytes is not None
                        )
                        if attempt < self.max_attempts:
                            attempt += 1
                            continue

            should_retry, delay = self._should_retry(response, attempt)
            self._log_response(
                method_upper,
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

    def get_shop(
        self,
        *,
        dry_run: Optional[bool] = None,
        safe_mode: bool = False,
        automation_enabled: bool = True,
    ) -> ShopifyResponse:
        """
        Fetch shop metadata (read-only).
        """
        return self.request(
            "GET",
            "shop.json",
            dry_run=dry_run,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
        )

    def refresh_access_token(self) -> bool:
        access_token, _ = self._load_access_token()
        if not access_token or not self._token_info:
            self._last_refresh_error = "missing_access_token"
            return False
        return self._refresh_access_token(self._token_info)

    def refresh_error(self) -> Optional[str]:
        return self._last_refresh_error

    def find_orders_by_name(
        self,
        order_name: str,
        *,
        fields: Optional[List[str]] = None,
        status: str = "any",
        limit: int = 5,
        dry_run: Optional[bool] = None,
        safe_mode: bool = False,
        automation_enabled: bool = True,
    ) -> ShopifyResponse:
        """
        Search orders by Shopify order name (e.g. #1001).
        Uses the primary request() entrypoint so all safety gates apply.
        """
        safe_name = str(order_name).strip()
        params: Dict[str, str] = {
            "status": status,
            "limit": str(limit),
            "name": safe_name,
        }
        if fields:
            params["fields"] = ",".join(sorted(map(str, fields)))
        query = urllib.parse.urlencode(sorted(params.items()))

        return self.request(
            "GET",
            f"orders.json?{query}",
            params=None,
            dry_run=dry_run,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
        )

    def find_order_by_name(
        self,
        order_name: str,
        *,
        fields: Optional[List[str]] = None,
        status: str = "any",
        limit: int = 5,
        dry_run: Optional[bool] = None,
        safe_mode: bool = False,
        automation_enabled: bool = True,
    ) -> ShopifyResponse:
        """
        Back-compat wrapper for name-based order search.
        """
        return self.find_orders_by_name(
            order_name,
            fields=fields,
            status=status,
            limit=limit,
            dry_run=dry_run,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
        )

    def list_orders_by_email(
        self,
        email: str,
        *,
        fields: Optional[List[str]] = None,
        status: str = "any",
        limit: int = 50,
        dry_run: Optional[bool] = None,
        safe_mode: bool = False,
        automation_enabled: bool = True,
    ) -> ShopifyResponse:
        """
        List orders by customer email.
        Uses the primary request() entrypoint so all safety gates apply.
        """
        safe_email = str(email).strip()
        params: Dict[str, str] = {
            "status": status,
            "limit": str(limit),
            "email": safe_email,
        }
        if fields:
            params["fields"] = ",".join(sorted(map(str, fields)))
        return self.request(
            "GET",
            "orders.json",
            params=params,
            dry_run=dry_run,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
        )

    def _to_response(
        self, transport_response: TransportResponse, url: str
    ) -> ShopifyResponse:
        return ShopifyResponse(
            status_code=transport_response.status_code,
            headers=transport_response.headers,
            body=transport_response.body,
            url=url,
            dry_run=False,
        )

    def _should_retry(
        self, response: ShopifyResponse, attempt: int
    ) -> Tuple[bool, float]:
        if response.status_code == 429 or 500 <= response.status_code < 600:
            delay = self._compute_backoff(attempt, response.headers.get("Retry-After"))
            return True, delay
        return False, 0.0

    def _compute_backoff(self, attempt: int, retry_after: Optional[str]) -> float:
        return compute_retry_backoff(
            attempt=attempt,
            retry_after=retry_after,
            backoff_seconds=self.backoff_seconds,
            backoff_max_seconds=self.backoff_max_seconds,
            rng=self._rng,
            retry_after_jitter_ratio=0.0,
        )

    def _sleep(self, delay: float) -> None:
        try:
            self._sleeper(delay)
        except Exception:
            # Sleeper is best-effort; failures should not crash the worker.
            self._logger.warning("shopify.sleep_failed", extra={"delay": delay})

    def _load_access_token(
        self, *, force_reload: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        if self._access_token and not force_reload:
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
                secret_value = base64.b64decode(response["SecretBinary"]).decode(
                    "utf-8"
                )

            if not secret_value:
                last_reason = "missing_access_token"
                continue

            token_info = self._parse_token_secret(
                secret_value, source_secret_id=secret_id
            )
            if not token_info.refresh_token:
                refresh_token = self._load_refresh_token(client)
                if refresh_token:
                    token_info.refresh_token = refresh_token
            self._token_info = token_info
            self._access_token = token_info.access_token
            self.access_token_secret_id = secret_id
            return self._access_token, None

        return None, last_reason or "missing_access_token"

    def _parse_token_secret(
        self, secret_value: str, *, source_secret_id: str
    ) -> ShopifyTokenInfo:
        try:
            parsed = json.loads(secret_value)
        except Exception:
            parsed = None

        if isinstance(parsed, dict) and parsed.get("access_token"):
            access_token = str(parsed.get("access_token"))
            refresh_token = parsed.get("refresh_token")
            refresh_token = str(refresh_token) if refresh_token else None
            expires_at = self._parse_expires_at(parsed)
            if refresh_token:
                self._refresh_token_source = "admin_api_token"
            return ShopifyTokenInfo(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                raw_format="json",
                source_secret_id=source_secret_id,
            )

        return ShopifyTokenInfo(
            access_token=str(secret_value).strip(),
            refresh_token=None,
            expires_at=None,
            raw_format="plain",
            source_secret_id=source_secret_id,
        )

    def _parse_expires_at(self, payload: Dict[str, Any]) -> Optional[float]:
        expires_at = payload.get("expires_at")
        if expires_at:
            parsed = self._parse_timestamp(expires_at)
            if parsed is not None:
                return parsed
        expires_in = payload.get("expires_in")
        if expires_in is None:
            return None
        try:
            expires_in_value = float(expires_in)
        except (TypeError, ValueError):
            return None
        issued_at = (
            payload.get("issued_at")
            or payload.get("obtained_at")
            or payload.get("created_at")
        )
        issued_at_value = self._parse_timestamp(issued_at) or time.time()
        return issued_at_value + expires_in_value

    def _parse_timestamp(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return None
        try:
            return float(text)
        except (TypeError, ValueError):
            pass
        try:
            normalized = text.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized).timestamp()
        except (TypeError, ValueError):
            return None

    def _load_client_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        if self._client_id and self._client_secret:
            return self._client_id, self._client_secret
        client = self._secrets_client_obj
        if client is None and boto3 is None:
            return None, None
        if client is None:
            client = self._secrets_client()

        if not self._client_id:
            client_id_value = self._load_secret_value(
                client, self.client_id_secret_id
            )
            self._client_id = self._extract_secret_field(
                client_id_value, ("client_id", "api_key", "key")
            )
        if not self._client_secret:
            client_secret_value = self._load_secret_value(
                client, self.client_secret_secret_id
            )
            self._client_secret = self._extract_secret_field(
                client_secret_value, ("client_secret", "secret", "value")
            )
        return self._client_id, self._client_secret

    def _load_refresh_token(self, client: Any) -> Optional[str]:
        if self._refresh_token_override:
            self._refresh_token_source = "override"
            return str(self._refresh_token_override).strip() or None
        if not self.refresh_token_secret_id:
            return None
        refresh_value = self._load_secret_value(client, self.refresh_token_secret_id)
        refresh_token = self._extract_secret_field(
            refresh_value, ("refresh_token", "token")
        )
        if refresh_token:
            self._refresh_token_source = "secret"
        return refresh_token

    @staticmethod
    def _extract_secret_field(
        secret_value: Optional[str], keys: Tuple[str, ...]
    ) -> Optional[str]:
        if not secret_value:
            return None
        try:
            parsed = json.loads(secret_value)
        except Exception:
            return secret_value
        if isinstance(parsed, dict):
            for key in keys:
                value = parsed.get(key)
                if value:
                    return str(value)
            return None
        return str(parsed)

    def _load_secret_value(self, client: Any, secret_id: str) -> Optional[str]:
        try:
            response = client.get_secret_value(SecretId=secret_id)  # type: ignore[attr-defined]
        except (BotoCoreError, ClientError, Exception):
            return None
        secret_value = response.get("SecretString")
        if secret_value is None and response.get("SecretBinary") is not None:
            secret_value = base64.b64decode(response["SecretBinary"]).decode("utf-8")
        if not secret_value:
            return None
        return str(secret_value)

    def _refresh_access_token(self, token_info: ShopifyTokenInfo) -> bool:
        client_id, client_secret = self._load_client_credentials()
        if not client_id or not client_secret:
            self._logger.warning(
                "shopify.refresh_missing_client_credentials",
                extra={
                    "client_id_secret_id": self.client_id_secret_id,
                    "client_secret_secret_id": self.client_secret_secret_id,
                },
            )
            self._last_refresh_error = "missing_client_credentials"
            return False

        url = f"https://{self.shop_domain}/admin/oauth/access_token"
        if token_info.refresh_token:
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": token_info.refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }
        else:
            payload = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }
        body = urllib.parse.urlencode(payload).encode("utf-8")
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        }

        try:
            response = self.transport.send(
                TransportRequest(
                    method="POST",
                    url=url,
                    headers=headers,
                    body=body,
                    timeout=float(self.timeout_seconds),
                )
            )
        except TransportError:
            self._logger.warning(
                "shopify.refresh_transport_error",
                extra={"url": url},
            )
            self._last_refresh_error = "transport_error"
            return False
        if response.status_code < 200 or response.status_code >= 300:
            body_excerpt = ""
            try:
                body_excerpt = _truncate(response.body.decode("utf-8"))
            except Exception:
                body_excerpt = ""
            body_excerpt = _redact_refresh_body(body_excerpt)
            self._logger.warning(
                "shopify.refresh_failed",
                extra={"status": response.status_code, "body_excerpt": body_excerpt},
            )
            error_code = None
            error_description = None
            try:
                error_payload = json.loads(response.body.decode("utf-8"))
                if isinstance(error_payload, dict):
                    error_code = error_payload.get("error")
                    error_description = error_payload.get("error_description")
            except Exception:
                error_payload = None
            if error_description:
                error_description = _redact_refresh_body(_truncate(str(error_description)))
            if error_code or error_description:
                self._last_refresh_error = (
                    f"status={response.status_code}"
                    + (f" error={error_code}" if error_code else "")
                    + (
                        f" description={error_description}"
                        if error_description
                        else ""
                    )
                )
            else:
                self._last_refresh_error = f"status={response.status_code}"
            return False
        refresh_payload = ShopifyResponse(
            status_code=response.status_code,
            headers=response.headers,
            body=response.body,
            url=url,
            dry_run=False,
        ).json()
        if not isinstance(refresh_payload, dict):
            self._logger.warning("shopify.refresh_invalid_payload")
            self._last_refresh_error = "invalid_payload"
            return False
        new_access_token = refresh_payload.get("access_token")
        new_refresh_token = refresh_payload.get("refresh_token") or token_info.refresh_token
        expires_in = refresh_payload.get("expires_in")
        if not new_access_token:
            self._logger.warning("shopify.refresh_missing_access_token")
            self._last_refresh_error = "missing_access_token"
            return False
        expires_at = None
        if expires_in is not None:
            try:
                expires_at = time.time() + float(expires_in)
            except (TypeError, ValueError):
                expires_at = None
        updated_info = ShopifyTokenInfo(
            access_token=str(new_access_token),
            refresh_token=str(new_refresh_token) if new_refresh_token else None,
            expires_at=expires_at,
            raw_format="json",
            source_secret_id=token_info.source_secret_id,
        )
        self._persist_token_info(updated_info)
        self._token_info = updated_info
        self._access_token = updated_info.access_token
        self._last_refresh_error = None
        return True

    def _persist_token_info(self, token_info: ShopifyTokenInfo) -> None:
        client = self._secrets_client_obj
        if client is None and boto3 is None:
            self._logger.warning("shopify.refresh_no_secrets_client")
            return
        if client is None:
            client = self._secrets_client()
        secret_id = token_info.source_secret_id or self.access_token_secret_id
        if not secret_id:
            self._logger.warning("shopify.refresh_missing_secret_id")
            return
        payload: Dict[str, Any] = {
            "access_token": token_info.access_token,
            "refresh_token": token_info.refresh_token,
            "expires_at": token_info.expires_at,
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            client.put_secret_value(  # type: ignore[attr-defined]
                SecretId=secret_id, SecretString=json.dumps(payload)
            )
        except (BotoCoreError, ClientError, Exception):
            self._logger.warning(
                "shopify.refresh_secret_write_failed",
                extra={"secret_id": secret_id},
            )

    def token_diagnostics(self) -> Dict[str, Any]:
        token_info = self._token_info
        if token_info is None:
            return {"status": "unknown"}
        token_type = "unknown"
        if token_info.access_token.startswith("shpat_"):
            token_type = "offline"
        elif token_info.access_token.startswith("shpua_"):
            token_type = "online"
        elif token_info.refresh_token:
            token_type = "online"
        return {
            "status": "loaded",
            "token_type": token_type,
            "raw_format": token_info.raw_format,
            "has_refresh_token": bool(token_info.refresh_token),
            "refresh_token_source": self._refresh_token_source,
            "expires_at": token_info.expires_at,
            "expired": token_info.is_expired() if token_info.expires_at else None,
            "source_secret_id": token_info.source_secret_id,
        }

    def _secrets_client(self):
        if self._secrets_client_obj is None:
            if boto3 is None:
                raise ShopifyRequestError(
                    "boto3 is required to create a secretsmanager client."
                )
            self._secrets_client_obj = boto3.client("secretsmanager")
        return self._secrets_client_obj

    def _build_headers(
        self, headers: Optional[Dict[str, str]], access_token: str, has_body: bool
    ) -> Dict[str, str]:
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
        return json.dumps(json_body, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

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
        if response.status_code == 429:
            self._logger.warning("shopify.rate_limited status=429")
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

    def _short_circuit_reason(
        self, safe_mode: bool, automation_enabled: bool, dry_run: bool
    ) -> Optional[str]:
        if safe_mode:
            return "safe_mode"
        if not automation_enabled:
            return "automation_disabled"
        if not self.allow_network:
            return "network_disabled"
        if dry_run:
            return "dry_run_forced"
        return None

    def _prod_write_ack_required(self, method: str) -> bool:
        if method.upper() in {"GET", "HEAD"}:
            return False
        if self.environment not in PRODUCTION_ENVIRONMENTS:
            return False
        return not self._prod_write_acknowledged()

    @staticmethod
    def _prod_write_acknowledged() -> bool:
        return prod_write_acknowledged(os.environ.get(PROD_WRITE_ACK_ENV))

    @staticmethod
    def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
        redacted = dict(headers or {})
        for key in [
            "x-shopify-access-token",
            "X-Shopify-Access-Token",
            "authorization",
            "Authorization",
        ]:
            if key in redacted:
                redacted[key] = "***"
        return redacted


__all__ = [
    "ShopifyClient",
    "ShopifyRequestError",
    "ShopifyResponse",
    "ShopifyWriteDisabledError",
    "Transport",
    "TransportRequest",
    "TransportResponse",
    "TransportError",
    "HttpTransport",
]
