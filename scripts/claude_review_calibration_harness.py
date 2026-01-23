#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import claude_gate_review as gate


def _split_fixtures_arg(value: str) -> list[str]:
    parts: list[str] = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts.extend(item for item in chunk.split() if item)
    return parts


def _list_fixture_names(fixtures_dir: Path) -> list[str]:
    names: list[str] = []
    for path in fixtures_dir.iterdir():
        if path.is_dir() and (path / "fixture_pr_metadata.json").exists():
            names.append(path.name)
    return sorted(names)


def _parse_fixture_names(value: str | None, fixtures_dir: Path) -> list[str]:
    if not value:
        return _list_fixture_names(fixtures_dir)
    names = _split_fixtures_arg(value)
    return sorted(dict.fromkeys(names))


def _parse_previous_state(raw: str) -> dict | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_false_positive_label(metadata: dict) -> bool | None:
    labels = metadata.get("kpi_labels")
    if not isinstance(labels, dict):
        return None
    value = labels.get("false_positive")
    if isinstance(value, bool):
        return value
    real_value = labels.get("action_required_real")
    if isinstance(real_value, bool):
        return not real_value
    return None


def _detect_truncation(metadata: dict, diff_text: str) -> bool:
    if isinstance(metadata.get("diff_truncated"), bool):
        return bool(metadata.get("diff_truncated"))
    return "[TRUNCATED]" in diff_text


def _evaluate_fixture(
    fixture_name: str,
    *,
    mode: str,
    review_config: dict,
) -> dict:
    bundle = gate._load_fixture_bundle(fixture_name)
    metadata = bundle.get("metadata", {})
    labels = metadata.get("labels", [])
    risk = metadata.get("risk_label") or gate._normalize_risk(labels or [])
    risk_defaults = gate._get_risk_defaults(review_config, risk)
    diff_text = bundle.get("diff", "")
    previous_state = _parse_previous_state(bundle.get("previous_state", ""))
    warnings: list[str] = []

    action_required_count = 0
    action_required_ids: list[str] = []
    action_required_severities: list[int] = []
    parse_error = False

    if mode == gate.MODE_LEGACY:
        verdict, findings = gate._evaluate_legacy_response(
            bundle.get("legacy_response", ""),
            max_findings=int(metadata.get("max_findings", gate.DEFAULT_MAX_FINDINGS)),
            bypass_enabled=False,
            warnings=warnings,
        )
        if verdict == "FAIL":
            normalized = [item.strip() for item in findings if isinstance(item, str)]
            if any(item != "No issues found." for item in normalized):
                action_required_count = len([item for item in normalized if item != "No issues found."])
    else:
        (
            _verdict,
            _payload,
            action_required,
            _fyi,
            summary,
            _state_payload,
            parse_error_message,
        ) = gate._evaluate_structured_response(
            bundle.get("structured_response", ""),
            diff_text=diff_text,
            mode=mode,
            bypass_enabled=False,
            warnings=warnings,
            risk_defaults=risk_defaults,
            previous_state=previous_state,
        )
        action_required_count = int(summary.get("action_required_count", 0))
        for item in action_required:
            fid = item.get("finding_id")
            if isinstance(fid, str) and fid:
                action_required_ids.append(fid)
            try:
                action_required_severities.append(int(item.get("severity", 0)))
            except (TypeError, ValueError):
                continue
        parse_error = parse_error_message is not None

    usage = metadata.get("usage") if isinstance(metadata, dict) else None
    token_total = None
    if isinstance(usage, dict):
        try:
            input_tokens = int(usage.get("input_tokens", 0))
            output_tokens = int(usage.get("output_tokens", 0))
        except (TypeError, ValueError):
            input_tokens = 0
            output_tokens = 0
        if input_tokens or output_tokens:
            token_total = input_tokens + output_tokens

    return {
        "fixture": fixture_name,
        "risk": risk,
        "action_required_count": action_required_count,
        "action_required_ids": action_required_ids,
        "action_required_severities": action_required_severities,
        "token_total": token_total,
        "diff_truncated": _detect_truncation(metadata, diff_text),
        "false_positive": _extract_false_positive_label(metadata),
        "parse_error": parse_error,
    }


def _percentile(values: list[int], percentile: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    index = max(0, math.ceil(percentile * len(sorted_values)) - 1)
    return float(sorted_values[index])


def _format_count(value: float | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.1f}"
    return str(int(value))


def _format_rate(count: int, total: int) -> str:
    if total <= 0:
        return "N/A"
    return f"{count / total * 100:.0f}% ({count}/{total})"


def _format_int(value: int | None) -> str:
    if value is None:
        return "N/A"
    return f"{int(value):,}"


def _compute_metrics(results: list[dict]) -> dict:
    total_runs = len(results)
    action_required_counts = [int(item.get("action_required_count", 0)) for item in results]
    action_required_runs = sum(1 for count in action_required_counts if count > 0)
    action_required_median = statistics.median(action_required_counts) if action_required_counts else None
    action_required_p90 = _percentile(action_required_counts, 0.9)

    parse_failures = sum(1 for item in results if item.get("parse_error"))
    truncation_runs = sum(1 for item in results if item.get("diff_truncated"))

    labeled_ar_runs = 0
    false_positive_runs = 0
    for item in results:
        if int(item.get("action_required_count", 0)) <= 0:
            continue
        label = item.get("false_positive")
        if isinstance(label, bool):
            labeled_ar_runs += 1
            if label:
                false_positive_runs += 1

    token_totals = [item.get("token_total") for item in results if isinstance(item.get("token_total"), int)]
    token_median = statistics.median(token_totals) if token_totals else None

    finding_ids: list[str] = []
    for item in results:
        finding_ids.extend(item.get("action_required_ids", []) or [])
    finding_counter = Counter(fid for fid in finding_ids if fid)
    duplicate_finding_total = sum(count - 1 for count in finding_counter.values() if count > 1)

    return {
        "total_runs": total_runs,
        "action_required_runs": action_required_runs,
        "action_required_median": action_required_median,
        "action_required_p90": action_required_p90,
        "parse_failures": parse_failures,
        "truncation_runs": truncation_runs,
        "false_positive_runs": false_positive_runs,
        "labeled_action_required_runs": labeled_ar_runs,
        "token_median": token_median,
        "token_samples": len(token_totals),
        "finding_counter": finding_counter,
        "duplicate_finding_total": duplicate_finding_total,
        "finding_total": len(finding_ids),
    }


def run_harness(
    fixtures: list[str],
    *,
    mode: str,
    fixtures_dir: Path | None = None,
) -> dict:
    fixtures_dir = fixtures_dir or gate.DEFAULT_FIXTURES_DIR
    review_config = gate._load_review_config()
    results = [_evaluate_fixture(name, mode=mode, review_config=review_config) for name in fixtures]
    overall = _compute_metrics(results)
    per_risk: dict[str, dict] = {}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        grouped[str(item.get("risk"))].append(item)
    for risk, items in grouped.items():
        per_risk[risk] = _compute_metrics(items)
    return {"overall": overall, "per_risk": per_risk, "results": results}


def _render_scoreboard(
    metrics: dict,
    *,
    fixtures: list[str],
    mode: str,
    start_date: str,
    end_date: str,
) -> str:
    overall = metrics["overall"]
    per_risk = metrics["per_risk"]

    duplicate_rate = (
        _format_rate(overall["duplicate_finding_total"], overall["finding_total"])
        if overall["finding_total"] > 0
        else "N/A"
    )
    false_positive_rate = _format_rate(
        overall["false_positive_runs"],
        overall["labeled_action_required_runs"],
    )

    lines = [
        "# Noise KPI Scoreboard (Calibration Harness)",
        "",
        "## Scoreboard metadata",
        f"- Period start: `{start_date}`",
        f"- Period end: `{end_date}`",
        "- Repo / branch protection check name: `Claude Review (gate:claude)`",
        f"- Source: `calibration_harness`",
        f"- Harness mode: `{mode}`",
        f"- Fixtures: `{', '.join(fixtures)}`",
        f"- Risk levels observed: `{', '.join(sorted(per_risk.keys()))}`",
        "",
        "## KPI summary (overall)",
        "| KPI | How to measure | Target (initial) | Actual | Notes / action |",
        "|---|---|---:|---:|---|",
        "| Action Required rate | `% of runs with >=1 Action Required` | `<20%` (non-R4) | "
        f"{_format_rate(overall['action_required_runs'], overall['total_runs'])} | Fixtures={overall['total_runs']} |",
        "| Action Required per run (median / p90) | counts | `median <=1`, `p90 <=2` | "
        f"{_format_count(overall['action_required_median'])} / {_format_count(overall['action_required_p90'])} | |",
        "| False positive proxy rate | `% Action Required runs labeled false positive` | `<10%` | "
        f"{false_positive_rate} | Labeled runs={overall['labeled_action_required_runs']} |",
        "| JSON parse failure rate | `% runs with malformed/missing JSON` | `0%` | "
        f"{_format_rate(overall['parse_failures'], overall['total_runs'])} | |",
        "| Diff truncation rate | `% runs where diff was truncated` | `<10%` | "
        f"{_format_rate(overall['truncation_runs'], overall['total_runs'])} | |",
        "| Token / PR (median input+output) | from stored usage fields | budgeted by risk | "
        f"{_format_int(overall['token_median'])} | Samples={overall['token_samples']} |",
        "| Duplicate rate (finding_id) | `% AR findings repeating across fixtures` | `<20%` | "
        f"{duplicate_rate} | Total findings={overall['finding_total']} |",
        "",
        "## KPI by risk level (recommended)",
        "Fill this table for the last **10-20 PR updates** per risk level (or best effort).",
        "",
        "| Risk | Runs observed | AR rate | AR median | Highest severity seen | FP rate (AR) | Token/PR median | Truncation rate | Notes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for risk in sorted(per_risk.keys()):
        data = per_risk[risk]
        false_positive_rate = _format_rate(
            data["false_positive_runs"],
            data["labeled_action_required_runs"],
        )
        highest_severity = 0
        for item in metrics["results"]:
            if item.get("risk") != risk:
                continue
            for severity in item.get("action_required_severities", []) or []:
                try:
                    highest_severity = max(highest_severity, int(severity))
                except (TypeError, ValueError):
                    continue
        lines.append(
            "| {risk} | {runs} | {ar_rate} | {ar_median} | {highest} | {fp_rate} | "
            "{token_median} | {trunc_rate} | |".format(
                risk=risk,
                runs=data["total_runs"],
                ar_rate=_format_rate(data["action_required_runs"], data["total_runs"]),
                ar_median=_format_count(data["action_required_median"]),
                highest=highest_severity or 0,
                fp_rate=false_positive_rate,
                token_median=_format_int(data["token_median"]),
                trunc_rate=_format_rate(data["truncation_runs"], data["total_runs"]),
            )
        )

    lines.extend(
        [
            "",
            "## Top recurring Action Required findings (deduped)",
            "List the top `finding_id` values that recur, and whether they were **real**.",
            "",
            "| finding_id | Severity | Confidence | Occurrences | Real issue? (Y/N) | Fix status | Notes |",
            "|---|---:|---:|---:|---|---|---|",
        ]
    )

    counter = metrics["overall"]["finding_counter"]
    if counter:
        for fid, count in counter.most_common(5):
            lines.append(f"| {fid} |  |  | {count} | TBD | TBD | |")
    else:
        lines.append("|  |  |  |  |  |  |  |")

    lines.extend(
        [
            "",
            "## Decisions for next period",
            "- Threshold changes (confidence, budgets, risk gating):",
            "  - None (calibration harness only).",
            "- Lens library changes (add/remove/tighten invariants):",
            "  - None (calibration harness only).",
            "- Diff selection / truncation improvements:",
            "  - TBD.",
            "- Enable structured gating for which risk levels (if any):",
            "  - TBD.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline calibration harness for Claude Review.")
    parser.add_argument("--fixtures", help="Comma/space-separated list of fixture names.")
    parser.add_argument("--fixtures-dir", default=str(gate.DEFAULT_FIXTURES_DIR))
    parser.add_argument(
        "--mode",
        choices=[gate.MODE_STRUCTURED, gate.MODE_SHADOW, gate.MODE_LEGACY],
        default=gate.MODE_STRUCTURED,
    )
    parser.add_argument("--start-date", default="")
    parser.add_argument("--end-date", default="")
    parser.add_argument("--output", help="Optional path to write the markdown scoreboard.")
    args = parser.parse_args()

    fixtures_dir = Path(args.fixtures_dir)
    fixtures = _parse_fixture_names(args.fixtures, fixtures_dir)
    if not fixtures:
        raise RuntimeError(f"No fixtures found in {fixtures_dir}")

    today = datetime.now(timezone.utc).date().isoformat()
    start_date = args.start_date or today
    end_date = args.end_date or today

    metrics = run_harness(fixtures, mode=args.mode, fixtures_dir=fixtures_dir)
    scoreboard = _render_scoreboard(
        metrics,
        fixtures=fixtures,
        mode=args.mode,
        start_date=start_date,
        end_date=end_date,
    )
    if args.output:
        Path(args.output).write_text(scoreboard, encoding="utf-8")
    print(scoreboard)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
