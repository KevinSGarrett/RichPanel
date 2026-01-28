from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    root = Path(r"C:\RichPanel_GIT")
    source_report = (
        root
        / "artifacts"
        / "readonly_shadow"
        / "live_readonly_shadow_eval_report_RUN_20260126_0319Z.json"
    )
    source_trace = (
        root
        / "artifacts"
        / "readonly_shadow"
        / "live_readonly_shadow_eval_http_trace_RUN_20260126_0319Z.json"
    )

    if not source_report.exists():
        raise SystemExit(f"Missing source report: {source_report}")

    sys.path.insert(0, str(root / "scripts"))
    import live_readonly_shadow_eval as shadow  # noqa: E402

    report = json.loads(source_report.read_text(encoding="utf-8"))
    tickets = report.get("tickets", [])
    counts = dict(report.get("counts", {}))
    run_id = report.get("run_id", "RUN_SAMPLE")
    tickets_requested = counts.get("tickets_requested", len(tickets))

    ticket_schema_seen: set[str] = set()
    shopify_schema_seen: set[str] = set()
    for result in tickets:
        ticket_schema = result.get("ticket_schema_fingerprint")
        if ticket_schema:
            ticket_schema_seen.add(ticket_schema)
        shopify_schema = result.get("shopify_schema_fingerprint")
        if shopify_schema:
            shopify_schema_seen.add(shopify_schema)

    ticket_schema_total = sum(
        1 for result in tickets if result.get("ticket_schema_fingerprint")
    )
    shopify_schema_total = sum(
        1 for result in tickets if result.get("shopify_schema_fingerprint")
    )

    drift_summary = shadow._build_drift_summary(
        ticket_total=ticket_schema_total,
        ticket_new=len(ticket_schema_seen),
        ticket_unique=len(ticket_schema_seen),
        shopify_total=shopify_schema_total,
        shopify_new=len(shopify_schema_seen),
        shopify_unique=len(shopify_schema_seen),
        threshold=shadow.DRIFT_WARNING_THRESHOLD,
    )

    timing_summary = shadow._summarize_timing([], run_duration_seconds=0.0)

    summary_payload = shadow._build_summary_payload(
        run_id=run_id,
        tickets_requested=tickets_requested,
        ticket_results=tickets,
        timing=timing_summary,
        drift=drift_summary,
        run_warnings=report.get("run_warnings", []),
    )

    tickets_evaluated = len(tickets)
    match_rate = (
        counts.get("orders_matched", 0) / tickets_evaluated
        if tickets_evaluated
        else 0.0
    )
    api_errors = sum(
        1
        for result in tickets
        if result.get("failure_source") in ("richpanel_fetch", "shopify_fetch")
    )
    api_error_rate = api_errors / tickets_evaluated if tickets_evaluated else 0.0
    order_number_matches = sum(
        1 for result in tickets if shadow._extract_match_method(result) == "order_number"
    )
    order_number_share = (
        order_number_matches / tickets_evaluated if tickets_evaluated else 0.0
    )
    schema_new_ratio = max(
        len(ticket_schema_seen) / ticket_schema_total if ticket_schema_total else 0.0,
        len(shopify_schema_seen) / shopify_schema_total
        if shopify_schema_total
        else 0.0,
    )
    summary_payload["drift_watch"] = shadow._build_drift_watch(
        match_rate=match_rate,
        api_error_rate=api_error_rate,
        order_number_share=order_number_share,
        schema_new_ratio=schema_new_ratio,
    )

    tracking_or_eta_available = sum(
        1
        for result in tickets
        if result.get("tracking_found") or result.get("eta_available")
    )
    counts["tracking_or_eta_available"] = tracking_or_eta_available

    proof_dir = root / "REHYDRATION_PACK" / "RUNS" / "B62" / "C" / "PROOF"
    proof_dir.mkdir(parents=True, exist_ok=True)

    summary_path = proof_dir / "live_shadow_summary.json"
    summary_md_path = proof_dir / "live_shadow_summary.md"
    trace_path = proof_dir / "live_shadow_http_trace.json"
    report_path = proof_dir / "live_shadow_report.json"

    out_report = {
        "run_id": run_id,
        "timestamp": report.get("timestamp"),
        "environment": report.get("environment", "prod"),
        "env_flags": dict(shadow.REQUIRED_FLAGS),
        "target": {
            "env": report.get("environment", "prod"),
            "region": None,
            "stack_name": None,
            "richpanel_base_url": report.get("target", {}).get("richpanel_base_url")
            or "https://api.richpanel.com",
            "shop_domain": None,
        },
        "prod_target": report.get("prod_target", True),
        "sample_mode": report.get("sample_mode", "explicit"),
        "ticket_count": summary_payload.get("ticket_count", len(tickets)),
        "match_success_rate": summary_payload.get("match_success_rate", 0.0),
        "match_failure_buckets": summary_payload.get("match_failure_buckets", {}),
        "tracking_or_eta_available_rate": summary_payload.get(
            "tracking_or_eta_available_rate", 0.0
        ),
        "would_reply_send": summary_payload.get("would_reply_send", False),
        "top_failure_reasons": summary_payload.get("top_failure_reasons", []),
        "counts": counts,
        "shopify_probe": report.get("shopify_probe", {}),
        "tickets": tickets,
        "summary_path": str(summary_path).replace("\\", "/"),
        "run_warnings": report.get("run_warnings", []),
        "http_trace_path": str(trace_path).replace("\\", "/"),
        "http_trace_summary": report.get("http_trace_summary", {}),
        "notes": report.get(
            "notes",
            [
                "Ticket identifiers are hashed.",
                "No message bodies or customer identifiers are stored.",
                "HTTP trace captures urllib.request and AWS SDK (botocore) calls; "
                "entries include source and AWS operation metadata.",
            ],
        ),
    }

    report_path.write_text(
        json.dumps(out_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    route_decisions = summary_payload.get("route_decisions", {})
    route_pcts = summary_payload.get("route_decision_percentages", {})
    match_methods = summary_payload.get("match_methods", {})
    match_pcts = summary_payload.get("match_method_percentages", {})
    failure_buckets = summary_payload.get("failure_buckets", {})
    match_failure_buckets = summary_payload.get("match_failure_buckets", {})
    drift_watch = summary_payload.get("drift_watch", {})
    trace_summary = report.get("http_trace_summary", {})

    md_lines = [
        "# Live Read-Only Shadow Eval Report",
        "",
        f"- Run ID: `{run_id}`",
        f"- Generated (UTC): {out_report['timestamp']}",
        f"- Environment: `{out_report['environment']}`",
        "- Region: `n/a`",
        "- Stack name: `n/a`",
        f"- Sample mode: `{out_report['sample_mode']}`",
        f"- Tickets requested: {counts.get('tickets_requested', len(tickets))}",
        f"- Tickets scanned: {counts.get('tickets_scanned', len(tickets))}",
        f"- Orders matched: {counts.get('orders_matched', 0)}",
        f"- Tracking found: {counts.get('tracking_found', 0)}",
        f"- ETA available: {counts.get('eta_available', 0)}",
        f"- Tracking or ETA available: {counts.get('tracking_or_eta_available', 0)}",
        f"- Match success rate: {summary_payload.get('match_success_rate', 0) * 100:.1f}%",
        f"- Would reply send: {summary_payload.get('would_reply_send', False)}",
        f"- Errors: {counts.get('errors', 0)}",
        f"- Shopify probe enabled: {out_report['shopify_probe'].get('enabled')}",
        f"- Shopify probe ok: {out_report['shopify_probe'].get('ok')}",
        f"- Shopify probe status: {out_report['shopify_probe'].get('status_code')}",
        f"- Summary path: `{summary_path}`",
        f"- Drift warning: {summary_payload['schema_drift']['warning']}",
        f"- Run warnings: {', '.join(summary_payload['run_warnings']) or 'none'}",
        "",
        "## Route Decision Distribution (B61/C)",
        f"- Order Status: {route_decisions.get('order_status', 0)} ({route_pcts.get('order_status', 0) * 100:.1f}%)",
        f"- Non-Order Status: {route_decisions.get('non_order_status', 0)} ({route_pcts.get('non_order_status', 0) * 100:.1f}%)",
        f"- Unknown: {route_decisions.get('unknown', 0)} ({route_pcts.get('unknown', 0) * 100:.1f}%)",
        "",
        "## Match Method Telemetry (B61/C)",
        f"- Order Number: {match_methods.get('order_number', 0)} ({match_pcts.get('order_number', 0) * 100:.1f}%)",
        f"- Name + Email: {match_methods.get('name_email', 0)} ({match_pcts.get('name_email', 0) * 100:.1f}%)",
        f"- Email Only: {match_methods.get('email_only', 0)} ({match_pcts.get('email_only', 0) * 100:.1f}%)",
        f"- No Match: {match_methods.get('none', 0)} ({match_pcts.get('none', 0) * 100:.1f}%)",
        f"- Parse Error: {match_methods.get('parse_error', 0)} ({match_pcts.get('parse_error', 0) * 100:.1f}%)",
        "",
        "## Failure Buckets (B61/C - PII Safe)",
        f"- No Identifiers: {failure_buckets.get('no_identifiers', 0)}",
        f"- Shopify API Error: {failure_buckets.get('shopify_api_error', 0)}",
        f"- Richpanel API Error: {failure_buckets.get('richpanel_api_error', 0)}",
        f"- Ambiguous Match: {failure_buckets.get('ambiguous_match', 0)}",
        f"- No Order Candidates: {failure_buckets.get('no_order_candidates', 0)}",
        f"- Parse Error: {failure_buckets.get('parse_error', 0)}",
        f"- Other Errors: {failure_buckets.get('other_error', 0) + failure_buckets.get('other_failure', 0)}",
        "",
        "## Match Failure Buckets (Deployment Gate)",
        f"- No Email: {match_failure_buckets.get('no_email', 0)}",
        f"- No Order Number: {match_failure_buckets.get('no_order_number', 0)}",
        f"- Ambiguous Customer: {match_failure_buckets.get('ambiguous_customer', 0)}",
        f"- No Order Candidates: {match_failure_buckets.get('no_order_candidates', 0)}",
        f"- Order Match Failed: {match_failure_buckets.get('order_match_failed', 0)}",
        f"- Parse Error: {match_failure_buckets.get('parse_error', 0)}",
        f"- API Error: {match_failure_buckets.get('api_error', 0)}",
        f"- Other/Unknown: {match_failure_buckets.get('other_failure', 0) + match_failure_buckets.get('unknown', 0)}",
        "",
        "## Drift Watch (B61/C)",
        f"- Match Rate: {drift_watch.get('current_values', {}).get('match_rate_pct', 0):.1f}% (threshold: drop > {shadow.DRIFT_THRESHOLDS['match_rate_drop_pct']}%)",
        f"- API Error Rate: {drift_watch.get('current_values', {}).get('api_error_rate_pct', 0):.1f}% (threshold: > {shadow.DRIFT_THRESHOLDS['api_error_rate_pct']}%)",
        f"- Order Number Share: {drift_watch.get('current_values', {}).get('order_number_share_pct', 0):.1f}% (threshold: drop > {shadow.DRIFT_THRESHOLDS['order_number_share_drop_pct']}%)",
        f"- Schema Drift: {drift_watch.get('current_values', {}).get('schema_new_ratio_pct', 0):.1f}% (threshold: > {shadow.DRIFT_THRESHOLDS['schema_drift_new_ratio'] * 100}%)",
        f"- Alerts: {len(drift_watch.get('alerts', []))}",
    ]
    for alert in drift_watch.get("alerts", []):
        md_lines.append(f"  - ALERT: {alert.get('message', 'Unknown alert')}")

    md_lines.extend(
        [
            "",
            "## HTTP Trace Summary",
            f"- Total requests: {trace_summary.get('total_requests', 0)}",
            f"- Methods: {json.dumps(trace_summary.get('methods', {}), sort_keys=True)}",
            f"- Services: {json.dumps(trace_summary.get('services', {}), sort_keys=True)}",
            f"- Sources: {json.dumps(trace_summary.get('sources', {}), sort_keys=True)}",
            f"- AWS operations: {json.dumps(trace_summary.get('aws_operations', {}), sort_keys=True)}",
            f"- AWS missing operations: {trace_summary.get('aws_missing_operations', 0)}",
            f"- Allowed methods only: {trace_summary.get('allowed_methods_only', False)}",
            f"- Trace path: `{trace_path}`",
            "",
            "## Notes",
            "- Ticket identifiers are hashed in the JSON report.",
            "- No message bodies or customer identifiers are stored.",
            "- HTTP trace captures urllib.request and AWS SDK (botocore) calls.",
        ]
    )
    summary_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    if source_trace.exists():
        trace_path.write_text(source_trace.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        trace_path.write_text(
            json.dumps({"note": "trace source unavailable"}, indent=2),
            encoding="utf-8",
        )

    print(f"Wrote {report_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {summary_md_path}")
    print(f"Wrote {trace_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
