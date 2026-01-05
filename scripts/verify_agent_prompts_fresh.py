#!/usr/bin/env python3
"""
verify_agent_prompts_fresh.py

Ensures the active Agent C assignments differ from the latest archived prompts.
Prevents accidental re-use of the previous prompt set unless explicitly overridden.
"""

from __future__ import annotations

import sys
from pathlib import Path

ASSIGNMENTS_PATH = Path("REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md")
ARCHIVE_PATTERN = "RUN_*/C/AGENT_PROMPTS_ARCHIVE*.md"
OVERRIDE_TOKEN = "Prompt-Repeat-Override: true"


def normalize(text: str) -> str:
    """Collapse all whitespace so comparisons ignore spacing differences."""
    return "".join(text.split())


def find_latest_archive(runs_dir: Path) -> Path | None:
    archive_paths = sorted(runs_dir.glob(ARCHIVE_PATTERN))
    if not archive_paths:
        return None
    return archive_paths[-1]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    assignments_file = root / ASSIGNMENTS_PATH
    if not assignments_file.exists():
        print(f"[WARN] Missing {ASSIGNMENTS_PATH}; skipping prompt freshness guard.")
        return 0

    current_text = assignments_file.read_text(encoding="utf-8")
    if OVERRIDE_TOKEN in current_text:
        print("[WARN] Prompt repeat override token detected; skipping freshness guard.")
        return 0

    runs_dir = root / "REHYDRATION_PACK" / "RUNS"
    latest_archive = find_latest_archive(runs_dir)
    if latest_archive is None:
        print("[WARN] No archived Agent C prompts found; skipping freshness guard.")
        return 0

    archive_text = latest_archive.read_text(encoding="utf-8")
    if normalize(current_text) == normalize(archive_text):
        print(
            "[FAIL] REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md matches the latest archived "
            f"Agent C prompts ({latest_archive.relative_to(root)}).\n"
            "Update the assignments or add 'Prompt-Repeat-Override: true' if reuse is intentional."
        )
        return 1

    print("[OK] Agent prompt assignments differ from the latest archive.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

