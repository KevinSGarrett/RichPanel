#!/usr/bin/env python3
"""
verify_openai_model_defaults.py

Fail if GPT-4 family defaults creep into backend/src or config.
- Scans only backend/src and config (excludes docs/rehydration history by path).
- Denylists GPT-4 family strings.
- Ensures any GPT model tokens found use GPT-5 family prefixes.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [ROOT / "backend" / "src", ROOT / "config"]

# Explicit GPT-4 family denylist (order matters: more specific first).
DENY_PATTERN = re.compile(r"gpt-4o-mini|gpt-4o|gpt-4-turbo|gpt-4", re.IGNORECASE)

# Any GPT model tokens we allow for defaults must start with these prefixes.
ALLOWED_PREFIXES = (
    "gpt-5",
    "gpt-5.",
    "gpt-5-mini",
    "gpt-5-nano",
)

MODEL_TOKEN_PATTERN = re.compile(r"gpt-[A-Za-z0-9_.-]+", re.IGNORECASE)


def iter_text_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if not path.exists():
            continue
        for file_path in path.rglob("*"):
            if file_path.is_file():
                yield file_path


def scan_file(path: Path) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]]]:
    """
    Returns:
        deny_hits: list of (line_no, line) containing GPT-4 family strings
        non_gpt5_tokens: GPT tokens that do not start with allowed GPT-5 prefixes
    """
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return [], []

    lines = text.splitlines()
    deny_hits: List[Tuple[int, str]] = []
    non_gpt5_tokens: List[Tuple[int, str]] = []

    for idx, line in enumerate(lines, start=1):
        if DENY_PATTERN.search(line):
            deny_hits.append((idx, line.rstrip()))

        for token_match in MODEL_TOKEN_PATTERN.finditer(line):
            token = token_match.group(0).lower()
            if not token.startswith(ALLOWED_PREFIXES):
                non_gpt5_tokens.append((idx, line.rstrip()))
    return deny_hits, non_gpt5_tokens


def main() -> int:
    deny_results: List[Tuple[Path, int, str]] = []
    non_gpt5_results: List[Tuple[Path, int, str]] = []

    for file_path in iter_text_files(SCAN_ROOTS):
        deny_hits, non_gpt5 = scan_file(file_path)
        for line_no, line in deny_hits:
            deny_results.append((file_path, line_no, line))
        for line_no, line in non_gpt5:
            non_gpt5_results.append((file_path, line_no, line))

    if deny_results:
        print("[FAIL] Found GPT-4 family defaults in backend/src or config:")
        for path, line_no, line in deny_results:
            print(f"  {path.relative_to(ROOT)}:{line_no}: {line}")
        return 1

    if non_gpt5_results:
        print("[FAIL] Found GPT model tokens that are not GPT-5 family prefixes:")
        for path, line_no, line in non_gpt5_results:
            print(f"  {path.relative_to(ROOT)}:{line_no}: {line}")
        return 1

    print("[OK] GPT-5.x defaults enforced (no GPT-4 family strings found).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
