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
                "Shopify shop domains are hashed.",
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

    summary_md_path.write_text(
        "\n".join(shadow._build_markdown_report(out_report, summary_payload)) + "\n",
        encoding="utf-8",
    )

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
