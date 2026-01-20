#!/usr/bin/env python3
"""
Order-status intent evaluation harness (PII-safe).

Runs deterministic routing + optional OpenAI routing on a JSONL dataset or
on live Richpanel tickets in read-only mode.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from richpanel_middleware.automation.llm_routing import (  # type: ignore
    suggest_llm_routing,
)
from richpanel_middleware.automation.router import (  # type: ignore
    classify_routing,
    extract_customer_message,
)
from richpanel_middleware.integrations.richpanel.client import (  # type: ignore
    RichpanelClient,
    RichpanelRequestError,
    RichpanelWriteDisabledError,
    SecretLoadError,
    TransportError,
)

LOGGER = logging.getLogger("order_status_intent_eval")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

ORDER_STATUS_INTENTS = {"order_status_tracking", "shipping_delay_not_shipped"}
VALID_LABELS = {"order_status", "non_order_status"}
PROD_RICHPANEL_BASE_URL = "https://api.richpanel.com"


@dataclass
class EvalExample:
    example_id: str
    text: str
    expected: Optional[str]


def _label_from_intent(intent: str) -> str:
    return "order_status" if intent in ORDER_STATUS_INTENTS else "non_order_status"


def _normalize_expected(value: Any, *, example_id: str) -> str:
    if value is None:
        raise ValueError(f"Missing expected label for {example_id}")
    expected = str(value).strip()
    if expected not in VALID_LABELS:
        raise ValueError(
            f"Invalid expected label '{expected}' for {example_id}; "
            f"must be one of {sorted(VALID_LABELS)}"
        )
    return expected


def _fingerprint(text: str, *, length: int = 12) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest[:length]


def _redact_identifier(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return f"redacted:{_fingerprint(text)}"


def load_jsonl_dataset(path: Path) -> List[EvalExample]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    examples: List[EvalExample] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_no}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"Expected object at line {line_no}")
            example_id = str(payload.get("id") or f"line-{line_no}")
            text = payload.get("text")
            if text is None:
                raise ValueError(f"Missing text for {example_id}")
            expected = _normalize_expected(payload.get("expected"), example_id=example_id)
            examples.append(
                EvalExample(
                    example_id=example_id,
                    text=str(text),
                    expected=expected,
                )
            )
    return examples


def _coerce_ticket_list(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("tickets", "data", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _fetch_recent_ticket_ids(client: RichpanelClient, *, limit: int) -> List[str]:
    resp = client.request(
        "GET",
        "/v1/tickets",
        params={"limit": str(limit)},
        dry_run=False,
        log_body_excerpt=False,
    )
    if resp.dry_run or resp.status_code >= 400:
        raise SystemExit(
            f"Ticket list fetch failed: status={resp.status_code} dry_run={resp.dry_run}"
        )
    payload = resp.json()
    tickets = _coerce_ticket_list(payload)
    ticket_ids: List[str] = []
    for ticket in tickets:
        ticket_id = ticket.get("id") or ticket.get("ticket_id") or ticket.get("_id")
        if ticket_id:
            ticket_ids.append(str(ticket_id))
    if not ticket_ids:
        raise SystemExit("Ticket list response contained no ids")
    return ticket_ids[:limit]


def _fetch_ticket_payload(client: RichpanelClient, ticket_id: str) -> Dict[str, Any]:
    encoded = urllib.parse.quote(ticket_id, safe="")
    resp = client.request(
        "GET",
        f"/v1/tickets/{encoded}",
        dry_run=False,
        log_body_excerpt=False,
    )
    if resp.dry_run or resp.status_code >= 400:
        return {}
    payload = resp.json()
    if isinstance(payload, dict) and isinstance(payload.get("ticket"), dict):
        payload = payload["ticket"]
    return payload if isinstance(payload, dict) else {}


def _fetch_conversation_payload(client: RichpanelClient, ticket_id: str) -> Dict[str, Any]:
    encoded = urllib.parse.quote(ticket_id, safe="")
    resp = client.request(
        "GET",
        f"/api/v1/conversations/{encoded}",
        dry_run=False,
        log_body_excerpt=False,
    )
    if resp.dry_run or resp.status_code >= 400:
        return {}
    payload = resp.json()
    return payload if isinstance(payload, dict) else {}


def _extract_message(ticket: Dict[str, Any], convo: Dict[str, Any]) -> str:
    text = extract_customer_message(ticket, default="")
    if text:
        return text
    text = extract_customer_message(convo, default="")
    if text:
        return text
    messages = convo.get("messages") or convo.get("conversation_messages") or []
    if isinstance(messages, list):
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            sender = str(message.get("sender_type") or message.get("author_type") or "")
            if sender and sender.lower() not in {"customer", "user", "end_user", "shopper"}:
                continue
            candidate = extract_customer_message(message, default="")
            if candidate:
                return candidate
    return ""


def _resolve_env_name() -> str:
    raw = (
        os.environ.get("RICHPANEL_ENV")
        or os.environ.get("RICH_PANEL_ENV")
        or os.environ.get("MW_ENV")
        or os.environ.get("ENVIRONMENT")
        or "local"
    )
    return str(raw).strip().lower() or "local"


def _is_prod_target(*, richpanel_base_url: str, richpanel_secret_id: Optional[str]) -> bool:
    env_name = _resolve_env_name()
    if env_name in {"prod", "production"}:
        return True
    if richpanel_secret_id and "/prod/" in richpanel_secret_id.lower():
        return True
    prod_key_present = bool(
        os.environ.get("PROD_RICHPANEL_API_KEY")
        or os.environ.get("RICHPANEL_API_KEY_OVERRIDE")
    )
    is_prod_base = richpanel_base_url.rstrip("/") == PROD_RICHPANEL_BASE_URL
    return prod_key_present and is_prod_base


def _require_env_flag(key: str, expected: str, *, context: str) -> None:
    actual = os.environ.get(key)
    if actual is None:
        raise SystemExit(f"{key} must be {expected} for {context} (unset)")
    if str(actual).strip().lower() != expected:
        raise SystemExit(f"{key} must be {expected} for {context} (found {actual})")


def _load_richpanel_examples(
    *, limit: int, richpanel_secret_id: Optional[str], base_url: str
) -> List[EvalExample]:
    client = RichpanelClient(
        api_key_secret_id=richpanel_secret_id,
        base_url=base_url,
        dry_run=False,
        read_only=True,
    )
    ticket_ids = _fetch_recent_ticket_ids(client, limit=limit)
    examples: List[EvalExample] = []
    for ticket_id in ticket_ids:
        ticket = _fetch_ticket_payload(client, ticket_id)
        convo = _fetch_conversation_payload(client, ticket_id)
        message = _extract_message(ticket, convo)
        if not message:
            LOGGER.warning(
                "Skipping ticket with no message",
                extra={"ticket_id": _redact_identifier(ticket_id)},
            )
            continue
        examples.append(
            EvalExample(
                example_id=_redact_identifier(ticket_id) or "redacted",
                text=message,
                expected=None,
            )
        )
    if not examples:
        raise SystemExit("No ticket messages available for evaluation")
    return examples


def _compute_metrics(pairs: Sequence[Tuple[str, str]]) -> Dict[str, Any]:
    tp = fp = tn = fn = 0
    for expected, predicted in pairs:
        if expected == "order_status":
            if predicted == "order_status":
                tp += 1
            else:
                fn += 1
        else:
            if predicted == "order_status":
                fp += 1
            else:
                tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
    }


def _evaluate_examples(
    examples: Sequence[EvalExample],
    *,
    use_openai: bool,
    allow_network: bool,
) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    deterministic_pairs: List[Tuple[str, str]] = []
    llm_pairs: List[Tuple[str, str]] = []
    llm_called_count = 0

    for example in examples:
        deterministic = classify_routing({"customer_message": example.text})
        deterministic_label = _label_from_intent(deterministic.intent)

        llm_label: Optional[str] = None
        llm_called = False
        llm_model = "deterministic"
        llm_confidence: Optional[float] = None

        if use_openai:
            suggestion = suggest_llm_routing(
                example.text,
                conversation_id=f"intent-eval-{example.example_id}",
                event_id=f"intent-eval-{example.example_id}",
                safe_mode=False,
                automation_enabled=True,
                allow_network=allow_network,
                outbound_enabled=allow_network,
            )
            llm_called = suggestion.llm_called
            llm_model = suggestion.model
            llm_confidence = (
                float(suggestion.confidence)
                if suggestion.confidence is not None
                else None
            )
            llm_label = _label_from_intent(suggestion.intent)
            if llm_called:
                llm_called_count += 1

        predicted = (
            llm_label if (llm_called and llm_label is not None) else deterministic_label
        )
        if not llm_called:
            llm_model = "deterministic"
            llm_confidence = None

        if example.expected in VALID_LABELS:
            deterministic_pairs.append((example.expected, deterministic_label))
            if llm_called and llm_label is not None:
                llm_pairs.append((example.expected, llm_label))

        results.append(
            {
                "id": example.example_id,
                "expected": example.expected or "unknown",
                "predicted": predicted,
                "llm_called": llm_called,
                "model": llm_model,
                "confidence": llm_confidence,
            }
        )

    metrics = {"deterministic": _compute_metrics(deterministic_pairs)}
    if llm_pairs:
        metrics["llm"] = _compute_metrics(llm_pairs)
    else:
        metrics["llm"] = {"available": False, "reason": "llm_not_called"}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "total": len(examples),
            "with_expected": len(deterministic_pairs),
            "llm_called": llm_called_count,
        },
        "metrics": metrics,
        "results": results,
    }


def run_dataset_eval(
    dataset_path: Path,
    *,
    output_path: Path,
    use_openai: bool,
    allow_network: bool,
) -> Dict[str, Any]:
    examples = load_jsonl_dataset(dataset_path)
    summary = _evaluate_examples(
        examples, use_openai=use_openai, allow_network=allow_network
    )
    summary["source"] = {"type": "dataset", "path": str(dataset_path)}
    write_summary(output_path, summary)
    return summary


def run_richpanel_eval(
    *,
    limit: int,
    richpanel_secret_id: Optional[str],
    base_url: str,
    output_path: Path,
    use_openai: bool,
    allow_network: bool,
) -> Dict[str, Any]:
    examples = _load_richpanel_examples(
        limit=limit, richpanel_secret_id=richpanel_secret_id, base_url=base_url
    )
    summary = _evaluate_examples(
        examples, use_openai=use_openai, allow_network=allow_network
    )
    summary["source"] = {
        "type": "richpanel",
        "limit": limit,
        "base_url": base_url,
    }
    write_summary(output_path, summary)
    return summary


def write_summary(path: Path, summary: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=True, indent=2)


def _print_metrics(label: str, metrics: Dict[str, Any]) -> None:
    if not metrics or metrics.get("available") is False:
        LOGGER.info("%s metrics: unavailable (%s)", label, metrics.get("reason"))
        return
    LOGGER.info(
        "%s metrics: precision=%s recall=%s (tp=%s fp=%s fn=%s tn=%s)",
        label,
        metrics.get("precision"),
        metrics.get("recall"),
        metrics.get("tp"),
        metrics.get("fp"),
        metrics.get("fn"),
        metrics.get("tn"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate order-status intent detection (PII-safe)."
    )
    parser.add_argument(
        "--dataset",
        help="Path to JSONL dataset (id/text/expected).",
    )
    parser.add_argument(
        "--from-richpanel",
        action="store_true",
        help="Fetch the latest tickets from Richpanel (GET-only, read-only).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Number of recent tickets to evaluate (richpanel mode).",
    )
    parser.add_argument(
        "--richpanel-secret-id",
        help="Optional override for rp-mw/<env>/richpanel/api_key secret id.",
    )
    parser.add_argument(
        "--richpanel-base-url",
        help="Override Richpanel API base URL (default: env or prod).",
    )
    parser.add_argument(
        "--output",
        help="Output JSON summary path (default: artifacts/intent_eval_results.json).",
    )
    parser.add_argument(
        "--use-openai",
        action="store_true",
        help="Attempt OpenAI routing for intent classification (requires OPENAI_ALLOW_NETWORK=true).",
    )
    args = parser.parse_args()

    output_path = Path(args.output or ROOT / "artifacts" / "intent_eval_results.json")
    use_openai = bool(args.use_openai)
    allow_network = use_openai and os.environ.get("OPENAI_ALLOW_NETWORK", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if args.from_richpanel:
        base_url = (
            args.richpanel_base_url
            or os.environ.get("RICHPANEL_API_BASE_URL")
            or PROD_RICHPANEL_BASE_URL
        ).rstrip("/")
        if _is_prod_target(
            richpanel_base_url=base_url, richpanel_secret_id=args.richpanel_secret_id
        ):
            _require_env_flag(
                "RICHPANEL_WRITE_DISABLED",
                "true",
                context="production Richpanel access",
            )
        try:
            summary = run_richpanel_eval(
                limit=args.limit,
                richpanel_secret_id=args.richpanel_secret_id,
                base_url=base_url,
                output_path=output_path,
                use_openai=use_openai,
                allow_network=allow_network,
            )
        except (RichpanelRequestError, RichpanelWriteDisabledError, SecretLoadError, TransportError) as exc:
            raise SystemExit(f"Richpanel evaluation failed: {exc}") from exc
    else:
        if not args.dataset:
            raise SystemExit("--dataset is required unless --from-richpanel is set")
        summary = run_dataset_eval(
            Path(args.dataset),
            output_path=output_path,
            use_openai=use_openai,
            allow_network=allow_network,
        )

    LOGGER.info("Saved summary to %s", output_path)
    _print_metrics("Deterministic", summary["metrics"]["deterministic"])
    _print_metrics("LLM", summary["metrics"]["llm"])
    if use_openai and not allow_network:
        LOGGER.info("OpenAI disabled (set OPENAI_ALLOW_NETWORK=true to enable calls).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
