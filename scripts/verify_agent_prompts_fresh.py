#!/usr/bin/env python3
"""
Ensure current agent prompts are not a repeat of recent archives.

This script compares `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` against the
most recent prompt archives and fails if an exact (whitespace-insensitive)
match is found. Use `Prompt-Repeat-Override: true` in the current file to
explicitly bypass the guard when needed.
"""
from __future__ import annotations

import re
from pathlib import Path

ARCHIVE_DEPTH = 5
ROOT = Path(__file__).resolve().parents[1]
CURRENT_PROMPTS_PATH = ROOT / "REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md"
ARCHIVE_GLOB = "REHYDRATION_PACK/RUNS/RUN_*/C/AGENT_PROMPTS_ARCHIVE*.md"
OVERRIDE_TOKEN = "prompt-repeat-override: true"


def normalize(content: str) -> str:
    # Remove all whitespace so formatting differences do not matter.
    return re.sub(r"\s+", "", content)


def archive_sort_key(path: Path) -> tuple[str, float]:
    # Sort primarily by run folder name, then by file mtime as a fallback.
    run_dir = path.parent.parent.name
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    return (run_dir, mtime)


def ordinal_label(idx: int) -> str:
    labels = ["newest", "2nd newest", "3rd newest", "4th newest", "5th newest"]
    if idx < len(labels):
        return labels[idx]
    return f"{idx + 1}th newest"


def main() -> int:
    if not CURRENT_PROMPTS_PATH.exists():
        print(f"[FAIL] Missing prompts file: {CURRENT_PROMPTS_PATH}")
        return 1

    current_raw = CURRENT_PROMPTS_PATH.read_text(encoding="utf-8")
    if OVERRIDE_TOKEN in current_raw.lower():
        print("[OK] Prompt-Repeat-Override present; skipping repeat guard.")
        return 0

    normalized_current = normalize(current_raw)
    archive_paths = sorted(ROOT.glob(ARCHIVE_GLOB), key=archive_sort_key, reverse=True)

    if not archive_paths:
        print("[OK] No prompt archives found; nothing to compare.")
        return 0

    archives_to_check = archive_paths[:ARCHIVE_DEPTH]
    for idx, archive in enumerate(archives_to_check):
        archive_raw = archive.read_text(encoding="utf-8")
        if normalize(archive_raw) == normalized_current:
            label = ordinal_label(idx)
            rel_path = archive.relative_to(ROOT)
            print(f"[FAIL] Current prompts match the {label} archive: {rel_path}")
            return 1

    print(f"[OK] Current prompts differ from the last {len(archives_to_check)} archive(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

