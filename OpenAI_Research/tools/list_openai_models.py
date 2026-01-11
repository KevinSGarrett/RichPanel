#!/usr/bin/env python3
"""
List OpenAI model IDs available to the current API key.

Why this exists:
- This repo's docs recommend GPT-5 family models (gpt-5-mini, gpt-5-nano, gpt-5.2).
- Some accounts also expose pins like gpt-5.1 and dated snapshots.
- We should *never* guess model IDs in production config; we should confirm what's enabled.

Usage (PowerShell):
  $env:OPENAI_API_KEY = "<your key>"
  python OpenAI_Research/tools/list_openai_models.py

Optional:
  $env:OPENAI_BASE_URL = "https://api.openai.com/v1"   # default
  $env:OPENAI_MODEL_FILTER = "gpt-5"                   # substring filter
  $env:OPENAI_TIMEOUT_SECONDS = "10"                   # default 10
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[FAIL] OPENAI_API_KEY is not set.", file=sys.stderr)
        return 2

    base_url = (os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    timeout = float(os.environ.get("OPENAI_TIMEOUT_SECONDS") or 10.0)
    needle = (os.environ.get("OPENAI_MODEL_FILTER") or "gpt-5").strip().lower()

    url = f"{base_url}/models"
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as exc:
        print(f"[FAIL] Request failed: {exc}", file=sys.stderr)
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("[FAIL] Response was not valid JSON.", file=sys.stderr)
        print(raw[:1000], file=sys.stderr)
        return 1

    items = data.get("data") or []
    ids = []
    for item in items:
        mid = item.get("id")
        if isinstance(mid, str):
            if not needle or needle in mid.lower():
                ids.append(mid)

    ids = sorted(set(ids))
    print(f"[OK] Found {len(ids)} model IDs matching filter {needle!r}:")
    for mid in ids:
        print(f"- {mid}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


