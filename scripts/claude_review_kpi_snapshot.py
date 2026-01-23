#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from claude_gate_constants import CANONICAL_MARKER
import claude_gate_comments as gate_comments


_MODE_RE = re.compile(r"^Mode:\s*(\S+)", re.MULTILINE)
_VERDICT_RE = re.compile(r"^CLAUDE_REVIEW:\s*(\S+)", re.MULTILINE)
_TOKEN_RE = re.compile(r"Token Usage:\s*input=(\d+), output=(\d+)")
_SUMMARY_RE = re.compile(r"Summary:\s*action_required=(\d+)", re.IGNORECASE)


def _extract_header_value(pattern: re.Pattern[str], body: str) -> str | None:
    match = pattern.search(body)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def _count_bullets_after(header: str, body: str) -> int | None:
    lines = body.splitlines()
    header_lower = header.lower()
    for index, line in enumerate(lines):
        if line.strip().lower() != header_lower:
            continue
        count = 0
        for next_line in lines[index + 1 :]:
            stripped = next_line.strip()
            if stripped == "":
                if count:
                    break
                continue
            if stripped.startswith("<details>") or stripped.startswith("FYI") or stripped.startswith("Structured JSON"):
                break
            if stripped.lower().startswith("summary:"):
                break
            if stripped.startswith("- "):
                normalized = stripped.lower()
                if normalized in ("- none", "- no issues found."):
                    return 0
                count += 1
            elif count:
                break
        return count
    return None


def _extract_action_required_count(body: str, mode: str | None) -> int | None:
    summary_match = _SUMMARY_RE.search(body)
    if summary_match:
        return int(summary_match.group(1))
    if mode == "LEGACY":
        findings_count = _count_bullets_after("Top findings:", body)
        return findings_count
    action_required_count = _count_bullets_after("Action Required:", body)
    return action_required_count


def parse_claude_review_comment(body: str) -> dict | None:
    if not body:
        return None
    mode = _extract_header_value(_MODE_RE, body)
    verdict = _extract_header_value(_VERDICT_RE, body)
    token_match = _TOKEN_RE.search(body)
    token_input = int(token_match.group(1)) if token_match else None
    token_output = int(token_match.group(2)) if token_match else None
    action_required_count = _extract_action_required_count(body, mode)
    return {
        "mode": mode,
        "verdict": verdict,
        "action_required_count": action_required_count,
        "token_input": token_input,
        "token_output": token_output,
        "parse_error": "Structured output parse failure" in body,
    }


def _select_canonical_comment(comments: list[dict]) -> dict | None:
    canonical = [comment for comment in comments if CANONICAL_MARKER in (comment.get("body") or "")]
    if not canonical:
        return None
    canonical.sort(
        key=lambda c: (
            c.get("updated_at") or c.get("created_at") or "",
            int(c.get("id", 0) or 0),
        ),
        reverse=True,
    )
    return canonical[0]


def _fetch_pr_numbers_since(repo: str, since_days: int, token: str) -> list[int]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    page = 1
    pr_numbers: list[int] = []
    while True:
        url = (
            f"https://api.github.com/repos/{repo}/pulls"
            f"?state=all&per_page=100&page={page}&sort=updated&direction=desc"
        )
        payload = gate_comments._github_request_json(url, token)
        if not payload:
            break
        if not isinstance(payload, list):
            raise RuntimeError("GitHub API returned unexpected PR payload.")
        stop = False
        for pr in payload:
            if not isinstance(pr, dict):
                continue
            updated_at = gate_comments._parse_github_datetime(pr.get("updated_at", ""))
            if updated_at < cutoff:
                stop = True
                break
            pr_number = pr.get("number")
            if pr_number is not None:
                pr_numbers.append(int(pr_number))
        if stop or len(payload) < 100:
            break
        page += 1
    return pr_numbers


def _load_comments_from_path(path: str) -> list[dict] | dict[int, list[dict]]:
    raw_text = Path(path).read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return [{"body": raw_text}]
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        if "comments" in parsed and isinstance(parsed["comments"], list):
            return [item for item in parsed["comments"] if isinstance(item, dict)]
        if "body" in parsed:
            return [parsed]
        mapping: dict[int, list[dict]] = {}
        for key, value in parsed.items():
            if not str(key).isdigit() or not isinstance(value, list):
                continue
            mapping[int(key)] = [item for item in value if isinstance(item, dict)]
        if mapping:
            return mapping
    if isinstance(parsed, str):
        return [{"body": parsed}]
    return []


def _format_rate(count: int, total: int) -> str:
    if total <= 0:
        return "N/A"
    return f"{count / total * 100:.0f}% ({count}/{total})"


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


def _format_int(value: int | None) -> str:
    if value is None:
        return "N/A"
    return f"{int(value):,}"


def _render_snapshot(
    *,
    repo: str,
    pr_numbers: list[int],
    parsed_results: list[dict],
    missing_comments: int,
) -> str:
    total = len(parsed_results)
    action_required_counts = [
        int(item.get("action_required_count", 0))
        for item in parsed_results
        if item.get("action_required_count") is not None
    ]
    action_required_runs = sum(1 for count in action_required_counts if count > 0)
    action_required_median = statistics.median(action_required_counts) if action_required_counts else None
    action_required_p90 = _percentile(action_required_counts, 0.9)
    parse_failures = sum(1 for item in parsed_results if item.get("parse_error"))

    token_totals = []
    for item in parsed_results:
        if item.get("token_input") is None or item.get("token_output") is None:
            continue
        token_totals.append(int(item["token_input"]) + int(item["token_output"]))
    token_median = statistics.median(token_totals) if token_totals else None
    token_median_int: int | None = int(token_median) if token_median is not None else None

    mode_counts = Counter(item.get("mode") or "UNKNOWN" for item in parsed_results)
    mode_summary = ", ".join(f"{mode}={count}" for mode, count in sorted(mode_counts.items()))

    lines = [
        "## Claude Review KPI Snapshot",
        f"- Repo: `{repo}`",
        f"- PRs sampled: `{', '.join(str(num) for num in pr_numbers)}`",
        f"- Sample size (canonical comments parsed): `{total}`",
        f"- Missing canonical comments: `{missing_comments}`",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Action Required rate | {_format_rate(action_required_runs, total)} |",
        f"| Action Required per run (median / p90) | {_format_count(action_required_median)} / {_format_count(action_required_p90)} |",
        f"| Token/PR median (input+output) | {_format_int(token_median_int)} (n={len(token_totals)}) |",
        f"| Structured parse failure rate | {_format_rate(parse_failures, total)} |",
        f"| Mode breakdown | {mode_summary or 'N/A'} |",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Claude Review KPI snapshot from GitHub.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--prs", help="Comma-separated PR numbers to sample (e.g. 150,151).")
    parser.add_argument("--since-days", type=int, help="Look back this many days for PRs (by updated_at).")
    parser.add_argument("--comment-path", help="Optional local comment fixture (JSON list or raw text).")
    args = parser.parse_args()

    if not args.prs and args.since_days is None:
        parser.error("Provide --prs or --since-days.")
    if args.prs and args.since_days is not None:
        parser.error("Use only one of --prs or --since-days.")

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    offline_comments = None
    if args.comment_path:
        offline_comments = _load_comments_from_path(args.comment_path)
        token = token or ""
    elif not token:
        print("ERROR: GITHUB_TOKEN is required but missing.")
        return 2

    if args.prs:
        pr_numbers = []
        for item in args.prs.split(","):
            item = item.strip()
            if not item:
                continue
            pr_numbers.append(int(item))
    else:
        pr_numbers = _fetch_pr_numbers_since(args.repo, args.since_days, token)

    parsed_results: list[dict] = []
    missing_comments = 0
    for pr_number in pr_numbers:
        if isinstance(offline_comments, dict):
            comments = offline_comments.get(pr_number, [])
        elif isinstance(offline_comments, list):
            comments = offline_comments
        else:
            comments = gate_comments._list_issue_comments(args.repo, pr_number, token)
        canonical = _select_canonical_comment(comments)
        if not canonical:
            missing_comments += 1
            continue
        parsed = parse_claude_review_comment(canonical.get("body") or "")
        if parsed:
            parsed_results.append(parsed)

    snapshot = _render_snapshot(
        repo=args.repo,
        pr_numbers=pr_numbers,
        parsed_results=parsed_results,
        missing_comments=missing_comments,
    )
    print(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
