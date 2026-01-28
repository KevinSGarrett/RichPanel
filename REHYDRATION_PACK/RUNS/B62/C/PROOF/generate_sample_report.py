from __future__ import annotations

import json
from pathlib import Path
import sys


def _resolve_repo_root(start: Path) -> Path:
    start_path = start.parent if start.is_file() else start
    for candidate in [start_path] + list(start_path.parents):
        if (candidate / ".git").exists():
            return candidate
        if (candidate / "scripts").exists() and (candidate / "backend").exists():
            return candidate
    return start_path


def main() -> int:
    root = _resolve_repo_root(Path(__file__).resolve())
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

    summary_payload["drift_watch"] = shadow._compute_drift_watch(
        ticket_results=tickets,
        ticket_schema_total=ticket_schema_total,
        ticket_schema_new=len(ticket_schema_seen),
        shopify_schema_total=shopify_schema_total,
        shopify_schema_new=len(shopify_schema_seen),
    )

    counts["tracking_or_eta_available"] = counts.get(
        "tracking_or_eta_available",
        summary_payload.get("tracking_or_eta_available_count", 0),
    )

    proof_dir = root / "REHYDRATION_PACK" / "RUNS" / "B62" / "C" / "PROOF"
    proof_dir.mkdir(parents=True, exist_ok=True)

    summary_path = proof_dir / "live_shadow_summary.json"
    summary_md_path = proof_dir / "live_shadow_summary.md"
    trace_path = proof_dir / "live_shadow_http_trace.json"
    report_path = proof_dir / "live_shadow_report.json"

    source_target = report.get("target", {})
    source_target = source_target if isinstance(source_target, dict) else {}
    out_report = {
        "run_id": run_id,
        "timestamp": report.get("timestamp"),
        "environment": report.get("environment", "prod"),
        "env_flags": dict(shadow.REQUIRED_FLAGS),
        "target": {
            "env": report.get("environment", "prod"),
            "region": source_target.get("region"),
            "stack_name": source_target.get("stack_name"),
            "richpanel_base_url": source_target.get("richpanel_base_url")
            or "https://api.richpanel.com",
            "shop_domain": shadow._redact_shop_domain(source_target.get("shop_domain")),
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
