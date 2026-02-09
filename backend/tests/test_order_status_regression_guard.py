from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("MW_OPENAI_INTENT_ENABLED", "true")
os.environ.setdefault("MW_OPENAI_SHADOW_ENABLED", "true")

from richpanel_middleware.automation.order_status_intent import (  # noqa: E402
    classify_order_status_intent,
    extract_order_number_from_text,
)
from richpanel_middleware.integrations.openai import ChatCompletionResponse  # noqa: E402


FIXTURES_PATH = ROOT / "backend" / "tests" / "fixtures" / "order_status_regression_samples.jsonl"


@dataclass
class _Sample:
    sample_id: str
    text: str
    expected_is_order_status: bool
    expected_order_number: str | None


def _load_samples() -> Iterable[_Sample]:
    lines = FIXTURES_PATH.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if not line.strip():
            continue
        payload = json.loads(line)
        yield _Sample(
            sample_id=payload["id"],
            text=payload["text"],
            expected_is_order_status=bool(payload["expected_is_order_status"]),
            expected_order_number=payload.get("expected_order_number"),
        )


class _StubClient:
    def __init__(self, message: str) -> None:
        self.message = message
        self.calls = 0

    def chat_completion(self, request, *, safe_mode: bool, automation_enabled: bool):
        self.calls += 1
        return ChatCompletionResponse(
            model=request.model,
            message=self.message,
            status_code=200,
            url="https://example.com",
            raw={"id": "resp_regression_guard"},
            dry_run=False,
        )


def _build_response(*, is_order_status: bool, order_number: str | None) -> str:
    payload = {
        "is_order_status": is_order_status,
        "confidence": 0.95 if is_order_status else 0.9,
        "reason": "fixture",
        "extracted_order_number": order_number,
        "language": "en",
    }
    return json.dumps(payload)


def test_regression_guard_extracts_order_numbers() -> None:
    for sample in _load_samples():
        if sample.expected_order_number:
            extracted = extract_order_number_from_text(sample.text)
            assert (
                extracted == sample.expected_order_number
            ), f"{sample.sample_id}: expected {sample.expected_order_number}, got {extracted}"


def test_regression_guard_intent_classification() -> None:
    for sample in _load_samples():
        client = _StubClient(
            _build_response(
                is_order_status=sample.expected_is_order_status,
                order_number=sample.expected_order_number,
            )
        )
        artifact = classify_order_status_intent(
            sample.text,
            conversation_id=f"conv-{sample.sample_id}",
            event_id=f"evt-{sample.sample_id}",
            safe_mode=False,
            automation_enabled=True,
            allow_network=True,
            outbound_enabled=True,
            client=client,
        )
        assert artifact.result is not None
        assert artifact.result.is_order_status is sample.expected_is_order_status
        assert artifact.accepted is sample.expected_is_order_status
