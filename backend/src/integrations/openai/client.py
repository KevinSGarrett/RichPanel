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
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

    class _FallbackBotoError(Exception):
        """Placeholder exception to allow offline testing without boto3."""

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
    """
    Choose an environment name for secret lookup; defaults to 'local'.
    Mirrors other integrations (Shopify, Richpanel) to stay consistent.
    """

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
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatCompletionRequest:
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.0
    max_tokens: int = 256
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: Optional[float] = None

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass
class ChatCompletionResponse:
    model: str
    message: Optional[str]
    status_code: int
    url: str
    raw: Dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False
    reason: Optional[str] = None


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


class Transport(Protocol):
    def send(self, request: TransportRequest) -> TransportResponse:
        ...


class TransportError(Exception):
    """Raised when HTTP transport cannot complete."""


class OpenAIRequestError(Exception):
    """Raised when the OpenAI request fails after retries."""

    def __init__(self, message: str, *, response: Optional[ChatCompletionResponse] = None) -> None:
        super().__init__(message)
        self.response = response


class OpenAIConfigError(Exception):
    """Raised when required configuration (e.g., API key) is missing."""


class HttpTransport:
    """Minimal urllib-based transport to avoid external deps."""

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


class OpenAIClient:
    """
    Offline-first OpenAI chat completion client.

    - Defaults to blocking network calls unless explicitly allowed.
    - Short-circuits when safe_mode is True or automation_enabled is False.
    - Retries 429/5xx and transport errors with jittered backoff.
    - Redacts Authorization headers in logs.
    - API key is loaded from AWS Secrets Manager by default
      (rp-mw/<env>/openai/api_key); env var override remains supported.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_secret_id: Optional[str] = None,
        allow_network: Optional[bool] = None,
        timeout_seconds: Optional[float] = None,
        max_attempts: int = 3,
        backoff_seconds: float = 0.25,
        backoff_max_seconds: float = 2.0,
        transport: Optional[Transport] = None,
        logger: Optional[logging.Logger] = None,
        sleeper: Optional[Callable[[float], None]] = None,
        rng: Optional[Callable[[], float]] = None,
        secrets_client: Optional[Any] = None,
    ) -> None:
        self.environment = _resolve_env_name()
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip(
            "/"
        )
        self.api_key_secret_id = (
            api_key_secret_id
            or os.environ.get("OPENAI_API_KEY_SECRET_ID")
            or f"rp-mw/{self.environment}/openai/api_key"
        )
        # Explicit value or env var override; Secrets Manager is used if absent.
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.allow_network = (
            _to_bool(os.environ.get("OPENAI_ALLOW_NETWORK"), default=False)
            if allow_network is None
            else bool(allow_network)
        )
        self.timeout_seconds = float(timeout_seconds or os.environ.get("OPENAI_TIMEOUT_SECONDS") or 10.0)
        self.max_attempts = max(1, int(os.environ.get("OPENAI_MAX_ATTEMPTS", max_attempts)))
        self.backoff_seconds = float(os.environ.get("OPENAI_BACKOFF_SECONDS", backoff_seconds))
        self.backoff_max_seconds = float(os.environ.get("OPENAI_BACKOFF_MAX_SECONDS", backoff_max_seconds))
        self.transport = transport or HttpTransport()
        self._logger = logger or logging.getLogger(__name__)
        self._sleeper = sleeper or time.sleep
        self._rng = rng or random.random
        self._secrets_client_obj = secrets_client

    def chat_completion(
        self,
        request: ChatCompletionRequest,
        *,
        safe_mode: bool,
        automation_enabled: bool,
    ) -> ChatCompletionResponse:
        url = self._build_url("/chat/completions")
        reason = self._short_circuit_reason(safe_mode, automation_enabled)
        if reason:
            self._logger.info("openai.short_circuit", extra={"url": url, "reason": reason})
            return ChatCompletionResponse(
                model=request.model,
                message=None,
                status_code=0,
                url=url,
                raw={"reason": reason},
                dry_run=True,
                reason=reason,
            )

        api_key, load_reason = self._load_api_key()
        if not api_key:
            reason = load_reason or "missing_api_key"
            self._logger.warning(
                "openai.missing_api_key",
                extra={"url": url, "reason": reason, "secret_id": self.api_key_secret_id},
            )
            return ChatCompletionResponse(
                model=request.model,
                message=None,
                status_code=0,
                url=url,
                raw={"reason": reason},
                dry_run=True,
                reason=reason,
            )

        payload = self._encode_body(request)
        headers = self._build_headers(has_body=bool(payload))

        attempt = 1
        last_response: Optional[ChatCompletionResponse] = None

        while attempt <= self.max_attempts:
            start = time.monotonic()
            try:
                transport_response = self.transport.send(
                    TransportRequest(
                        method="POST",
                        url=url,
                        headers=headers,
                        body=payload,
                        timeout=float(request.timeout_seconds or self.timeout_seconds),
                    )
                )
            except TransportError as exc:
                self._logger.warning(
                    "openai.transport_error",
                    extra={"url": url, "attempt": attempt},
                )
                if attempt >= self.max_attempts:
                    raise OpenAIRequestError(
                        f"OpenAI transport failed after {attempt} attempts"
                    ) from exc
                delay = self._compute_backoff(attempt, retry_after=None)
                self._sleep(delay)
                attempt += 1
                continue

            latency_ms = int((time.monotonic() - start) * 1000)
            response = self._to_response(transport_response, url, request.model)
            last_response = response

            should_retry, delay = self._should_retry(response, attempt)
            self._log_response(response, latency_ms, attempt, delay if should_retry else None)

            if should_retry and attempt < self.max_attempts:
                self._sleep(delay)
                attempt += 1
                continue

            if response.status_code >= 500 or response.status_code == 429:
                raise OpenAIRequestError(
                    f"OpenAI request failed with status {response.status_code}",
                    response=response,
                )

            return response

        raise OpenAIRequestError(
            f"OpenAI request exhausted retries (last status: {last_response.status_code if last_response else 'unknown'})",
            response=last_response,
        )

    def _short_circuit_reason(self, safe_mode: bool, automation_enabled: bool) -> Optional[str]:
        if safe_mode:
            return "safe_mode"
        if not automation_enabled:
            return "automation_disabled"
        if not self.allow_network:
            return "network_blocked"
        return None

    def _load_api_key(self) -> Tuple[Optional[str], Optional[str]]:
        if self.api_key:
            return self.api_key, None

        client = self._secrets_client_obj
        if client is None and boto3 is None:
            return None, "boto3_unavailable"
        if client is None:
            client = self._secrets_client()

        try:
            response = client.get_secret_value(SecretId=self.api_key_secret_id)  # type: ignore[attr-defined]
        except (BotoCoreError, ClientError, Exception):
            return None, "secret_lookup_failed"

        secret_value = response.get("SecretString")
        if secret_value is None and response.get("SecretBinary") is not None:
            try:
                secret_value = base64.b64decode(response["SecretBinary"]).decode("utf-8")
            except Exception:
                return None, "secret_decode_failed"

        if not secret_value:
            return None, "missing_api_key"

        self.api_key = secret_value
        return self.api_key, None

    def _secrets_client(self):
        if self._secrets_client_obj is None:
            if boto3 is None:
                raise OpenAIConfigError("boto3 is required to create a secretsmanager client.")
            self._secrets_client_obj = boto3.client("secretsmanager")
        return self._secrets_client_obj

    def _build_headers(self, *, has_body: bool) -> Dict[str, str]:
        headers = {"authorization": f"Bearer {self.api_key}", "accept": "application/json"}
        if has_body:
            headers["content-type"] = "application/json"
        return headers

    def _build_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return urllib.parse.urljoin(f"{self.base_url}/", normalized_path.lstrip("/"))

    def _encode_body(self, request: ChatCompletionRequest) -> bytes:
        body = request.to_payload()
        return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _to_response(
        self, transport_response: TransportResponse, url: str, model: str
    ) -> ChatCompletionResponse:
        raw_json: Dict[str, Any] = {}
        message_content: Optional[str] = None
        if transport_response.body:
            try:
                raw_json = json.loads(transport_response.body.decode("utf-8"))
                choices = raw_json.get("choices") or []
                if choices and isinstance(choices[0], dict):
                    message_content = (
                        choices[0].get("message", {}) or choices[0].get("delta", {})
                    ).get("content")
            except Exception:
                raw_json = {}
                message_content = None

        return ChatCompletionResponse(
            model=raw_json.get("model") or model,
            message=message_content,
            status_code=transport_response.status_code,
            url=url,
            raw=raw_json,
            dry_run=False,
        )

    def _should_retry(self, response: ChatCompletionResponse, attempt: int) -> Tuple[bool, float]:
        if response.status_code == 429 or 500 <= response.status_code < 600:
            retry_after = None
            if response.raw:
                retry_after = response.raw.get("retry_after") or response.raw.get("Retry-After")
            delay = self._compute_backoff(attempt, retry_after)
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
            self._logger.warning("openai.sleep_failed", extra={"delay": delay})

    def _log_response(
        self,
        response: ChatCompletionResponse,
        latency_ms: int,
        attempt: int,
        retry_in: Optional[float],
    ) -> None:
        extra = {
            "url": response.url,
            "status": response.status_code,
            "latency_ms": latency_ms,
            "attempt": attempt,
            "dry_run": response.dry_run,
        }
        if retry_in is not None:
            extra["retry_in"] = retry_in
            self._logger.warning("openai.retry", extra=extra)
        else:
            preview = ""
            if response.message:
                preview = _truncate(response.message, limit=200)
            elif response.raw:
                preview = _truncate(json.dumps(response.raw, sort_keys=True), limit=200)
            if preview:
                extra["message_excerpt"] = preview
            self._logger.info("openai.response", extra=extra)

    @staticmethod
    def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
        redacted = dict(headers or {})
        for key in ["authorization", "Authorization", "api-key", "x-api-key"]:
            if key in redacted:
                redacted[key] = "***"
        return redacted


__all__ = [
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatMessage",
    "HttpTransport",
    "OpenAIClient",
    "OpenAIConfigError",
    "OpenAIRequestError",
    "Transport",
    "TransportError",
    "TransportRequest",
    "TransportResponse",
]


