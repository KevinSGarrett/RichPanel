from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import boto3
import requests
from boto3.dynamodb.conditions import Attr


WORKER_LOG_GROUP = "/aws/lambda/rp-mw-prod-worker"
FAILURE_TERMS = [
    "error",
    "exception",
    "traceback",
    "task timed out",
    "automation.order_status_reply.allowlist_blocked",
    "automation.order_status_reply.author_missing",
    "missing_order_status_action",
    "send_message_failed",
    "reply_close_failed",
    "read_only_guard",
    "richpanel.write_blocked",
]
ISSUE_TERMS = [
    "automation.order_status_reply.skip",
    "automation.order_status_context_missing",
    "order_lookup_failed",
    "openai_intent_disabled",
]
ORDER_STATUS_INTENTS = {"order_status_tracking", "shipping_delay_not_shipped"}


def _default_out_dir() -> str:
    # Keep a deterministic local default while remaining cross-platform.
    return str(Path.cwd() / "MONITORING")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor prod worker logs and order-status classification findings."
    )
    parser.add_argument("--profile", default="rp-admin-prod")
    parser.add_argument("--region", default="us-east-2")
    parser.add_argument("--hours", type=int, default=3)
    parser.add_argument("--interval-minutes", type=int, default=10)
    parser.add_argument(
        "--out-dir",
        default=_default_out_dir(),
    )
    return parser.parse_args()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ms(ts: datetime) -> int:
    return int(ts.timestamp() * 1000)


def _safe_get(mapping: Any, key: str, default: Any = None) -> Any:
    if isinstance(mapping, dict):
        return mapping.get(key, default)
    return default


def _extract_api_key(secret_str: str) -> str:
    try:
        parsed = json.loads(secret_str)
        if isinstance(parsed, dict):
            for k in ("api_key", "RICHPANEL_KEY", "key", "token"):
                value = parsed.get(k)
                if value:
                    return str(value).strip()
    except Exception:
        pass
    return str(secret_str).strip()


def _load_richpanel_key(sm_client, env: str = "prod") -> str:
    secret_id = f"rp-mw/{env}/richpanel/api_key"
    resp = sm_client.get_secret_value(SecretId=secret_id)
    return _extract_api_key(resp.get("SecretString") or "")


def _fetch_logs(logs_client, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    paginator = logs_client.get_paginator("filter_log_events")
    for page in paginator.paginate(
        logGroupName=WORKER_LOG_GROUP,
        startTime=_ms(start),
        endTime=_ms(end),
    ):
        events.extend(page.get("events") or [])
    return events


def _scan_order_status_state(
    state_table, start: datetime, end: datetime
) -> List[Dict[str, Any]]:
    # recorded_at is ISO8601 string and lexicographically sortable for UTC timestamps.
    start_iso = _iso(start)
    end_iso = _iso(end)

    items: List[Dict[str, Any]] = []
    scan_kwargs = {
        "FilterExpression": Attr("updated_at").between(start_iso, end_iso)
        & Attr("routing.category").eq("order_status"),
        "ProjectionExpression": (
            "conversation_id, updated_at, routing, outbound_result, order_status_intent"
        ),
    }
    response = state_table.scan(**scan_kwargs)
    items.extend(response.get("Items") or [])
    while "LastEvaluatedKey" in response:
        response = state_table.scan(
            **scan_kwargs, ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items") or [])
    return items


def _resolve_ticket_number(
    conversation_id: str,
    *,
    api_key: str,
    cache: Dict[str, Optional[str]],
    timeout_seconds: int = 20,
) -> Optional[str]:
    if conversation_id in cache:
        return cache[conversation_id]
    if not conversation_id:
        cache[conversation_id] = None
        return None

    headers = {"x-richpanel-key": api_key, "accept": "application/json"}
    try:
        resp = requests.get(
            f"https://api.richpanel.com/v1/tickets/{conversation_id}",
            headers=headers,
            timeout=timeout_seconds,
        )
        if resp.status_code != 200:
            cache[conversation_id] = None
            return None
        payload = resp.json() if isinstance(resp.json(), dict) else {}
        ticket = payload.get("ticket") if isinstance(payload.get("ticket"), dict) else payload
        number = _safe_get(ticket, "conversation_no")
        cache[conversation_id] = str(number) if number is not None else None
        return cache[conversation_id]
    except Exception:
        cache[conversation_id] = None
        return None


def _aggregate_terms(events: List[Dict[str, Any]], terms: List[str]) -> Dict[str, int]:
    counts = {term: 0 for term in terms}
    for ev in events:
        msg = str(ev.get("message") or "").lower()
        for term in terms:
            if term in msg:
                counts[term] += 1
    return counts


def _build_interval_report(
    *,
    index: int,
    start: datetime,
    end: datetime,
    events: List[Dict[str, Any]],
    failure_counts: Dict[str, int],
    issue_counts: Dict[str, int],
    order_items: List[Dict[str, Any]],
    api_key: str,
    ticket_cache: Dict[str, Optional[str]],
) -> Dict[str, Any]:
    order_rows: List[Dict[str, Any]] = []
    seen_conv: Set[str] = set()
    for item in order_items:
        conv_id = str(item.get("conversation_id") or "")
        if not conv_id or conv_id in seen_conv:
            continue
        seen_conv.add(conv_id)
        routing = item.get("routing") if isinstance(item.get("routing"), dict) else {}
        intent = str(routing.get("intent") or "")
        if intent and intent not in ORDER_STATUS_INTENTS:
            continue
        intent_artifact = (
            item.get("order_status_intent")
            if isinstance(item.get("order_status_intent"), dict)
            else {}
        )
        intent_result = (
            intent_artifact.get("result")
            if isinstance(intent_artifact.get("result"), dict)
            else {}
        )
        intent_accepted = bool(intent_artifact.get("accepted") is True)
        intent_is_order_status = bool(intent_result.get("is_order_status") is True)
        # Strict intent filter: only include tickets explicitly accepted as
        # order-status intent by the intent classifier.
        if not (intent_accepted and intent_is_order_status):
            continue
        outbound = (
            item.get("outbound_result")
            if isinstance(item.get("outbound_result"), dict)
            else {}
        )
        ticket_number = _resolve_ticket_number(
            conv_id, api_key=api_key, cache=ticket_cache
        )
        order_rows.append(
            {
                "ticket_number": ticket_number,
                "conversation_id": conv_id,
                "updated_at": item.get("updated_at"),
                "intent": intent or None,
                "intent_confidence": intent_result.get("confidence"),
                "routing_category": routing.get("category"),
                "outbound_sent": outbound.get("sent"),
                "outbound_reason": outbound.get("reason"),
            }
        )

    report = {
        "interval_index": index,
        "window_start_utc": _iso(start),
        "window_end_utc": _iso(end),
        "worker_events_count": len(events),
        "failures": failure_counts,
        "issues": issue_counts,
        "order_status_tickets": sorted(
            order_rows, key=lambda r: (str(r.get("ticket_number") or ""), r["conversation_id"])
        ),
    }
    return report


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False))
        handle.write("\n")


def _write_markdown(path: Path, all_reports: List[Dict[str, Any]]) -> None:
    lines: List[str] = []
    lines.append("# Prod 3h Log Watch")
    lines.append("")
    lines.append(
        f"Generated at: {_iso(_utc_now())} | intervals captured: {len(all_reports)}"
    )
    lines.append("")
    for report in all_reports:
        lines.append(
            f"## Interval {report['interval_index']} ({report['window_start_utc']} -> {report['window_end_utc']})"
        )
        lines.append("")
        lines.append(f"- Worker events: {report['worker_events_count']}")
        fail_total = sum(report["failures"].values())
        issue_total = sum(report["issues"].values())
        lines.append(f"- Failure term hits: {fail_total}")
        lines.append(f"- Issue term hits: {issue_total}")
        lines.append(f"- Order-status tickets found: {len(report['order_status_tickets'])}")
        lines.append("")
        if fail_total:
            lines.append("### Failures")
            for k, v in report["failures"].items():
                if v:
                    lines.append(f"- `{k}`: {v}")
            lines.append("")
        if issue_total:
            lines.append("### Issues")
            for k, v in report["issues"].items():
                if v:
                    lines.append(f"- `{k}`: {v}")
            lines.append("")
        lines.append("### Order-Status Classified Tickets")
        if report["order_status_tickets"]:
            for row in report["order_status_tickets"]:
                lines.append(
                    "- ticket_number={ticket_number} conversation_id={conversation_id} intent={intent} "
                    "outbound_sent={outbound_sent} outbound_reason={outbound_reason}".format(
                        ticket_number=row.get("ticket_number") or "unknown",
                        conversation_id=row.get("conversation_id"),
                        intent=row.get("intent") or "unknown",
                        outbound_sent=row.get("outbound_sent"),
                        outbound_reason=row.get("outbound_reason"),
                    )
                )
        else:
            lines.append("- none")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "prod_log_watch_findings.jsonl"
    md_path = out_dir / "prod_log_watch_findings.md"
    status_path = out_dir / "prod_log_watch_status.json"

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    logs_client = session.client("logs")
    sm_client = session.client("secretsmanager")
    ddb = session.resource("dynamodb")
    cw = session.client("cloudwatch")

    api_key = _load_richpanel_key(sm_client, env="prod")
    state_table = ddb.Table("rp_mw_prod_conversation_state")

    start_ts = _utc_now()
    end_ts = start_ts + timedelta(hours=args.hours)
    interval = timedelta(minutes=args.interval_minutes)
    cursor = start_ts
    idx = 1
    ticket_cache: Dict[str, Optional[str]] = {}
    reports: List[Dict[str, Any]] = []

    # Fresh run marker.
    status_path.write_text(
        json.dumps(
            {
                "status": "running",
                "started_at_utc": _iso(start_ts),
                "scheduled_end_at_utc": _iso(end_ts),
                "interval_minutes": args.interval_minutes,
                "jsonl_path": str(jsonl_path),
                "markdown_path": str(md_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    while cursor < end_ts:
        interval_end = min(cursor + interval, _utc_now())
        if interval_end <= cursor:
            time.sleep(5)
            continue

        events = _fetch_logs(logs_client, cursor, interval_end)
        failure_counts = _aggregate_terms(events, FAILURE_TERMS)
        issue_counts = _aggregate_terms(events, ISSUE_TERMS)
        order_items = _scan_order_status_state(state_table, cursor, interval_end)

        report = _build_interval_report(
            index=idx,
            start=cursor,
            end=interval_end,
            events=events,
            failure_counts=failure_counts,
            issue_counts=issue_counts,
            order_items=order_items,
            api_key=api_key,
            ticket_cache=ticket_cache,
        )

        # Add interval-level Lambda metrics for operational health.
        metric_payload: Dict[str, int] = {}
        for metric in ("Invocations", "Errors", "Throttles"):
            resp = cw.get_metric_statistics(
                Namespace="AWS/Lambda",
                MetricName=metric,
                Dimensions=[{"Name": "FunctionName", "Value": "rp-mw-prod-worker"}],
                StartTime=cursor,
                EndTime=interval_end,
                Period=300,
                Statistics=["Sum"],
            )
            datapoints = resp.get("Datapoints") or []
            metric_payload[metric] = int(sum(float(d.get("Sum", 0.0)) for d in datapoints))
        report["worker_metrics"] = metric_payload

        _append_jsonl(jsonl_path, report)
        reports.append(report)
        _write_markdown(md_path, reports)

        status_path.write_text(
            json.dumps(
                {
                    "status": "running",
                    "started_at_utc": _iso(start_ts),
                    "last_interval_end_utc": report["window_end_utc"],
                    "scheduled_end_at_utc": _iso(end_ts),
                    "intervals_completed": idx,
                    "jsonl_path": str(jsonl_path),
                    "markdown_path": str(md_path),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"[interval {idx}] {report['window_start_utc']} -> {report['window_end_utc']} "
            f"| events={report['worker_events_count']} "
            f"| failures={sum(report['failures'].values())} "
            f"| issues={sum(report['issues'].values())} "
            f"| order_status_tickets={len(report['order_status_tickets'])}"
        )

        idx += 1
        cursor = interval_end
        if cursor >= end_ts:
            break
        sleep_seconds = max(1, int((cursor + interval - _utc_now()).total_seconds()))
        time.sleep(min(sleep_seconds, args.interval_minutes * 60))

    status_path.write_text(
        json.dumps(
            {
                "status": "completed",
                "started_at_utc": _iso(start_ts),
                "completed_at_utc": _iso(_utc_now()),
                "scheduled_end_at_utc": _iso(end_ts),
                "intervals_completed": len(reports),
                "jsonl_path": str(jsonl_path),
                "markdown_path": str(md_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
