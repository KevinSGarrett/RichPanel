#!/usr/bin/env python3
"""
pr_agent_comments.py

Upsert a single canonical PR-Agent comment on a PR.
Uses a DIFFERENT marker than Claude gate to avoid overwriting.

Pattern copied from scripts/claude_gate_comments.py with PR_AGENT_MARKER.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from pr_agent_constants import PR_AGENT_MARKER

_DEFAULT_ACCEPT = "application/vnd.github+json"
_API_VERSION = "2022-11-28"


def _parse_github_datetime(value: str) -> datetime:
    if not value:
        return datetime.max.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.max.replace(tzinfo=timezone.utc)


def _comment_has_marker(comment: dict) -> bool:
    body = comment.get("body") or ""
    return PR_AGENT_MARKER in body


def _canonical_sort_key(comment: dict) -> tuple[datetime, int]:
    created_at = _parse_github_datetime(comment.get("created_at", ""))
    try:
        comment_id_int = int(comment.get("id", 0))
    except (TypeError, ValueError):
        comment_id_int = 0
    return (created_at, comment_id_int)


def _github_request(
    url: str,
    token: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
) -> bytes:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", _DEFAULT_ACCEPT)
    request.add_header("X-GitHub-Api-Version", _API_VERSION)
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"GitHub API error {exc.code} for {url}: {body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API request failed for {url}: {exc}") from exc


def _github_request_json(url: str, token: str, **kwargs) -> dict | list:
    data = _github_request(url, token, **kwargs)
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GitHub API returned invalid JSON for {url}") from exc


def _list_issue_comments(repo: str, pr_number: int, token: str) -> list[dict]:
    comments: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
            f"?per_page=100&page={page}"
        )
        chunk = _github_request_json(url, token)
        if not chunk:
            break
        if not isinstance(chunk, list):
            raise RuntimeError("GitHub API returned unexpected comments payload.")
        comments.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return comments


def upsert_canonical_comment(repo: str, pr_number: int, token: str, body: str) -> dict:
    if PR_AGENT_MARKER not in body:
        body = f"{PR_AGENT_MARKER}\n{body}"
    comments = _list_issue_comments(repo, pr_number, token)
    canonical = [c for c in comments if _comment_has_marker(c)]
    canonical.sort(key=_canonical_sort_key)

    if canonical:
        comment_id = canonical[0].get("id")
        url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
        response = _github_request_json(url, token, method="PATCH", payload={"body": body})
        action = "update"
    else:
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        response = _github_request_json(url, token, method="POST", payload={"body": body})
        action = "create"

    if not isinstance(response, dict):
        raise RuntimeError("Unexpected response from GitHub API.")
    return {
        "action": action,
        "comment_id": response.get("id"),
        "comment_url": response.get("html_url"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Upsert canonical PR-Agent comment.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--comment-path", required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN is required.", file=sys.stderr)
        return 2

    try:
        with open(args.comment_path, "r", encoding="utf-8") as f:
            comment_body = f.read()
    except OSError as exc:
        print(f"ERROR: Unable to read comment file: {exc}", file=sys.stderr)
        return 2

    result = upsert_canonical_comment(args.repo, args.pr_number, token, comment_body)
    action = result.get("action")
    comment_id = result.get("comment_id")
    comment_url = result.get("comment_url")
    print(f"PR-Agent comment {action}: id={comment_id} url={comment_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
