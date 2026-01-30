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
from typing import Any, Callable, Dict, Optional, Protocol, Tuple

from integrations.common import compute_retry_backoff

try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Placeholder exception so offline tests can run without boto3."""

    BotoCoreError = ClientError = _FallbackBotoError  # type: ignore


DEFAULT_API_BASE = "https://ssapi.shipstation.com"


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _truncate(text: str, limit: int = 512) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _resolve_env_name() -> str:
    raw = (
        os.environ.get("RICHPANEL_ENV")
        or os.environ.get("RICH_PANEL_ENV")
        or os.environ.get("MW_ENV")
        or os.environ.get("ENVIRONMENT")
        or "local"
    )
    return str(raw).strip().lower() or "local"


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
class ShipStationResponse:
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


class Transport(Protocol):
    def send(self, request: TransportRequest) -> TransportResponse: ...


class TransportError(Exception):
    """Raised when the HTTP transport cannot complete the request."""


class ShipStationRequestError(Exception):
    """Raised when ShipStation replies with repeated failures."""

    def __init__(
        self, message: str, *, response: Optional[ShipStationResponse] = None
    ) -> None:
        super().__init__(message)
        self.response = response


class HttpTransport:
    """Minimal urllib-based transport to avoid extra dependencies."""

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


class ShipStationClient:
    """
    Offline-first ShipStation API client with safety rails.

    - Dry-run by default (network blocked unless explicitly enabled).
    - Short-circuits with reasons safe_mode / automation_disabled / network_disabled / missing_credentials.
    - Credentials sourced from AWS Secrets Manager:
        rp-mw/<env>/shipstation/api_key
        rp-mw/<env>/shipstation/api_secret
        rp-mw/<env>/shipstation/api_base (optional; defaults to https://ssapi.shipstation.com)
    - Retries 429/5xx and transport errors with jittered backoff.
    - Redacts Authorization + ShipStation headers in logs.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_key_secret_id: Optional[str] = None,
        api_secret_secret_id: Optional[str] = None,
        api_base_secret_id: Optional[str] = None,
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
        explicit_base = (
            base_url
            or os.environ.get("SHIPSTATION_API_BASE_URL")
            or os.environ.get("SHIPSTATION_API_BASE_OVERRIDE")
        )
        self._base_url = (explicit_base or DEFAULT_API_BASE).rstrip("/")
        self._explicit_base_url = explicit_base
        self.api_key_secret_id = (
            api_key_secret_id
            or os.environ.get("SHIPSTATION_API_KEY_SECRET_ID")
            or f"rp-mw/{self.environment}/shipstation/api_key"
        )
        self.api_secret_secret_id = (
            api_secret_secret_id
            or os.environ.get("SHIPSTATION_API_SECRET_SECRET_ID")
            or f"rp-mw/{self.environment}/shipstation/api_secret"
        )
        self.api_base_secret_id = (
            api_base_secret_id
            or os.environ.get("SHIPSTATION_API_BASE_SECRET_ID")
            or f"rp-mw/{self.environment}/shipstation/api_base"
        )
        self.allow_network = (
            _to_bool(os.environ.get("SHIPSTATION_OUTBOUND_ENABLED"), default=False)
            if allow_network is None
            else bool(allow_network)
        )
        self.timeout_seconds = float(
            timeout_seconds or os.environ.get("SHIPSTATION_HTTP_TIMEOUT_SECONDS") or 5.0
        )
        self.max_attempts = max(
            1, int(os.environ.get("SHIPSTATION_HTTP_MAX_ATTEMPTS", max_attempts))
        )
        self.backoff_seconds = float(
            os.environ.get("SHIPSTATION_HTTP_BACKOFF_SECONDS", backoff_seconds)
        )
        self.backoff_max_seconds = float(
            os.environ.get("SHIPSTATION_HTTP_BACKOFF_MAX_SECONDS", backoff_max_seconds)
        )
        self.transport = transport or HttpTransport()
        self._logger = logger or logging.getLogger(__name__)
        self._api_key = api_key or os.environ.get("SHIPSTATION_API_KEY_OVERRIDE")
        self._api_secret = api_secret or os.environ.get(
            "SHIPSTATION_API_SECRET_OVERRIDE"
        )
        self._base_secret_loaded = False
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
    ) -> ShipStationResponse:
        url = self._build_url(path, params)
        body_bytes = self._encode_body(json_body)
        use_dry_run = self._resolve_dry_run(dry_run)

        reason = self._short_circuit_reason(safe_mode, automation_enabled, use_dry_run)
        if reason:
            self._logger.info(
                "shipstation.dry_run",
                extra={
                    "method": method.upper(),
                    "url": url,
                    "reason": reason,
                    "dry_run": True,
                },
            )
            return self._dry_run_response(url, reason)

        api_key, api_secret, credential_reason = self._load_credentials()
        if not api_key or not api_secret:
            reason = credential_reason or "missing_credentials"
            self._logger.warning(
                "shipstation.missing_credentials", extra={"url": url, "reason": reason}
            )
            return self._dry_run_response(url, "missing_credentials")

        request_headers = self._build_headers(
            headers, api_key, api_secret, has_body=body_bytes is not None
        )
        attempt = 1
        last_response: Optional[ShipStationResponse] = None

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
                    "shipstation.transport_error",
                    extra={"method": method.upper(), "url": url, "attempt": attempt},
                )
                if attempt >= self.max_attempts:
                    raise ShipStationRequestError(
                        f"ShipStation transport failed after {attempt} attempts"
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
            )

            if should_retry and attempt < self.max_attempts:
                self._sleep(delay)
                attempt += 1
                continue

            if response.status_code >= 500 or response.status_code == 429:
                raise ShipStationRequestError(
                    f"ShipStation request failed with status {response.status_code}",
                    response=response,
                )

            return response

        raise ShipStationRequestError(
            f"ShipStation request exhausted retries (last status: {last_response.status_code if last_response else 'unknown'})",
            response=last_response,
        )

    def list_shipments(
        self,
        *,
        params: Optional[Dict[str, str]] = None,
        dry_run: Optional[bool] = None,
        safe_mode: bool = False,
        automation_enabled: bool = True,
    ) -> ShipStationResponse:
        return self.request(
            "GET",
            "/shipments",
            params=params,
            dry_run=dry_run,
            safe_mode=safe_mode,
            automation_enabled=automation_enabled,
        )

    def _dry_run_response(self, url: str, reason: str) -> ShipStationResponse:
        return ShipStationResponse(
            status_code=0,
            headers={"x-dry-run": "1", "x-dry-run-reason": reason},
            body=b"",
            url=url,
            dry_run=True,
            reason=reason,
        )

    def _to_response(
        self, transport_response: TransportResponse, url: str
    ) -> ShipStationResponse:
        return ShipStationResponse(
            status_code=transport_response.status_code,
            headers=transport_response.headers,
            body=transport_response.body,
            url=url,
            dry_run=False,
        )

    def _should_retry(
        self, response: ShipStationResponse, attempt: int
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
            self._logger.warning("shipstation.sleep_failed", extra={"delay": delay})

    def _load_credentials(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        reasons = []
        if not self._api_key:
            value, error = self._fetch_secret_value(self.api_key_secret_id)
            if value:
                self._api_key = value
            elif error:
                reasons.append(error)

        if not self._api_secret:
            value, error = self._fetch_secret_value(self.api_secret_secret_id)
            if value:
                self._api_secret = value
            elif error:
                reasons.append(error)

        if not self._explicit_base_url and not self._base_secret_loaded:
            base_value, error = self._fetch_secret_value(self.api_base_secret_id)
            self._base_secret_loaded = True
            if base_value:
                self._base_url = base_value.rstrip("/")
            elif error:
                self._logger.info(
                    "shipstation.base_secret_unavailable", extra={"reason": error}
                )

        if self._api_key and self._api_secret:
            return self._api_key, self._api_secret, None

        return None, None, reasons[0] if reasons else "missing_credentials"

    def _fetch_secret_value(
        self, secret_id: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        if not secret_id:
            return None, "secret_id_missing"
        client = self._secrets_client_obj
        if client is None and boto3 is None:
            return None, "boto3_unavailable"
        if client is None:
            try:
                client = self._secrets_client()
            except Exception:
                return None, "secret_lookup_failed"
        try:
            response = client.get_secret_value(SecretId=secret_id)  # type: ignore[attr-defined]
        except (BotoCoreError, ClientError, Exception):
            return None, "secret_lookup_failed"

        secret_value = response.get("SecretString")
        if secret_value is None and response.get("SecretBinary") is not None:
            try:
                secret_value = base64.b64decode(response["SecretBinary"]).decode(
                    "utf-8"
                )
            except Exception:
                return None, "secret_decode_failed"

        if not secret_value:
            return None, "secret_empty"

        return secret_value.strip(), None

    def _secrets_client(self):
        if self._secrets_client_obj is None:
            if boto3 is None:
                raise ShipStationRequestError(
                    "boto3 is required to create a secretsmanager client."
                )
            self._secrets_client_obj = boto3.client("secretsmanager")
        return self._secrets_client_obj

    def _build_headers(
        self,
        headers: Optional[Dict[str, str]],
        api_key: str,
        api_secret: str,
        *,
        has_body: bool,
    ) -> Dict[str, str]:
        token = base64.b64encode(f"{api_key}:{api_secret}".encode("utf-8")).decode(
            "utf-8"
        )
        merged: Dict[str, str] = {
            "accept": "application/json",
            "authorization": f"Basic {token}",
        }
        if has_body:
            merged["content-type"] = "application/json"
        if headers:
            for key in headers:
                merged[key] = headers[key]
            merged["authorization"] = f"Basic {token}"
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
        url = urllib.parse.urljoin(f"{self._base_url}/", normalized_path.lstrip("/"))
        if params:
            query = urllib.parse.urlencode(sorted(params.items()))
            url = f"{url}?{query}"
        return url

    def _log_response(
        self,
        method: str,
        response: ShipStationResponse,
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
            self._logger.warning("shipstation.retry", extra=extra)
        else:
            snippet = ""
            if response.body:
                try:
                    snippet = _truncate(response.body.decode("utf-8"), limit=256)
                except Exception:
                    snippet = "<binary>"
            if snippet:
                extra["body_excerpt"] = snippet
            self._logger.info("shipstation.response", extra=extra)

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
        if not self.allow_network or dry_run:
            return "network_disabled"
        return None

    @staticmethod
    def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
        redacted = dict(headers or {})
        for key in list(redacted.keys()):
            lowered = key.lower()
            if lowered == "authorization" or "shipstation" in lowered:
                redacted[key] = "***"
        return redacted


class ShipStationExecutor:
    """
    Thin wrapper that keeps ShipStation outbound calls in dry-run mode unless explicitly enabled.
    """

    def __init__(
        self,
        *,
        client: Optional[ShipStationClient] = None,
        outbound_enabled: Optional[bool] = None,
    ) -> None:
        self._outbound_enabled = self._resolve_outbound_enabled(outbound_enabled)
        self._client = client or ShipStationClient(allow_network=self._outbound_enabled)

    def execute(self, method: str, path: str, **kwargs: Any) -> ShipStationResponse:
        requested_dry_run = kwargs.pop("dry_run", None)
        effective_dry_run = (
            not self._outbound_enabled
            if requested_dry_run is None
            else bool(requested_dry_run)
        )
        return self._client.request(method, path, dry_run=effective_dry_run, **kwargs)

    def _resolve_outbound_enabled(self, override: Optional[bool]) -> bool:
        if override is not None:
            return bool(override)
        return _to_bool(os.environ.get("SHIPSTATION_OUTBOUND_ENABLED"), default=False)


__all__ = [
    "ShipStationClient",
    "ShipStationExecutor",
    "ShipStationRequestError",
    "ShipStationResponse",
    "Transport",
    "TransportRequest",
    "TransportResponse",
    "TransportError",
    "HttpTransport",
]
