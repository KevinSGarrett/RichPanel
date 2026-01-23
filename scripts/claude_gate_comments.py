#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

CANONICAL_MARKER = "<!-- CLAUDE_REVIEW_CANONICAL -->"
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
    return CANONICAL_MARKER in body


def _canonical_sort_key(comment: dict) -> tuple[datetime, int]:
    created_at = _parse_github_datetime(comment.get("created_at", ""))
    comment_id = comment.get("id")
    try:
        comment_id_int = int(comment_id)
    except (TypeError, ValueError):
        comment_id_int = 0
    return (created_at, comment_id_int)


def resolve_canonical_comment_action(comments: list[dict]) -> tuple[str, int | None, int]:
    canonical = [comment for comment in comments if _comment_has_marker(comment)]
    if not canonical:
        return ("create", None, 0)
    canonical.sort(key=_canonical_sort_key)
    comment_id = canonical[0].get("id")
    if comment_id is None:
        raise RuntimeError("Canonical comment missing id.")
    return ("update", int(comment_id), len(canonical))


def _github_request(
    url: str,
    token: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    accept: str = _DEFAULT_ACCEPT,
) -> bytes:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", accept)
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


def _github_request_json(
    url: str,
    token: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    accept: str = _DEFAULT_ACCEPT,
) -> dict | list:
    data = _github_request(url, token, method=method, payload=payload, accept=accept)
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


def _create_issue_comment(repo: str, pr_number: int, token: str, body: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    response = _github_request_json(url, token, method="POST", payload={"body": body})
    if not isinstance(response, dict):
        raise RuntimeError("GitHub API returned unexpected comment create response.")
    return response


def _update_issue_comment(repo: str, comment_id: int, token: str, body: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
    response = _github_request_json(url, token, method="PATCH", payload={"body": body})
    if not isinstance(response, dict):
        raise RuntimeError("GitHub API returned unexpected comment update response.")
    return response


def upsert_canonical_comment(repo: str, pr_number: int, token: str, body: str) -> dict:
    if CANONICAL_MARKER not in body:
        body = f"{CANONICAL_MARKER}\n{body}"
    comments = _list_issue_comments(repo, pr_number, token)
    action, comment_id, canonical_count = resolve_canonical_comment_action(comments)
    if canonical_count > 1:
        print(
            f"NOTE: Found {canonical_count} canonical comments; updating the oldest.",
            file=sys.stderr,
        )
    if action == "update":
        response = _update_issue_comment(repo, comment_id, token, body)
    else:
        response = _create_issue_comment(repo, pr_number, token, body)
    return {
        "action": action,
        "comment_id": response.get("id"),
        "comment_url": response.get("html_url"),
        "canonical_count": canonical_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Upsert canonical Claude gate comment.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--comment-path", required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN is required but missing.", file=sys.stderr)
        return 2

    try:
        with open(args.comment_path, "r", encoding="utf-8") as handle:
            comment_body = handle.read()
    except OSError as exc:
        print(f"ERROR: Unable to read comment file: {exc}", file=sys.stderr)
        return 2

    result = upsert_canonical_comment(args.repo, args.pr_number, token, comment_body)
    action = result.get("action")
    comment_id = result.get("comment_id")
    comment_url = result.get("comment_url")
    print(f"Claude review comment {action}: id={comment_id} url={comment_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
