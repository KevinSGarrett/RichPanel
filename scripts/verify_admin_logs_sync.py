#!/usr/bin/env python3
"""
verify_admin_logs_sync.py

Ensures the admin logs (Progress_Log.md) reference the latest run folder.

Design goals:
- Standard library only
- Cross-platform (Windows/macOS/Linux)
- Deterministic and repo-relative

Usage:
  python scripts/verify_admin_logs_sync.py

What it does:
1) Finds the latest RUN_* folder under REHYDRATION_PACK/RUNS/
2) Fails if that RUN_ID is not referenced in docs/00_Project_Admin/Progress_Log.md

Exit codes:
  0 = ok (latest RUN_ID found in Progress_Log.md)
  1 = failure (missing reference or no runs found)
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "REHYDRATION_PACK" / "RUNS"
PROGRESS_LOG = REPO_ROOT / "docs" / "00_Project_Admin" / "Progress_Log.md"

# Pattern to match run folder names (e.g., RUN_20260102_2148Z)
RUN_ID_PATTERN = re.compile(r"^RUN_\d{8}_\d{4}Z$")


def find_latest_run() -> str | None:
    """
    Find the latest RUN_* folder under REHYDRATION_PACK/RUNS/.
    Returns the folder name (RUN_ID) or None if no valid runs exist.
    """
    if not RUNS_DIR.exists():
        return None

    run_folders = [
        p.name
        for p in RUNS_DIR.iterdir()
        if p.is_dir() and RUN_ID_PATTERN.match(p.name)
    ]

    if not run_folders:
        return None

    # Sort lexicographically (works for YYYYMMDD_HHMMZ format)
    run_folders.sort()
    return run_folders[-1]


def check_progress_log_references(run_id: str) -> bool:
    """
    Check if the given RUN_ID is mentioned in Progress_Log.md.
    """
    if not PROGRESS_LOG.exists():
        return False

    content = PROGRESS_LOG.read_text(encoding="utf-8", errors="replace")
    return run_id in content


def main() -> int:
    print("[verify_admin_logs_sync] Checking admin logs sync...")

    latest_run = find_latest_run()

    if latest_run is None:
        print("[SKIP] No RUN_* folders found under REHYDRATION_PACK/RUNS/")
        print(
            "       (This is OK if you're still in foundation mode or haven't started build runs yet.)"
        )
        return 0

    print(f"  Latest run folder: {latest_run}")

    if not PROGRESS_LOG.exists():
        print(f"[FAIL] Progress_Log.md not found at: {PROGRESS_LOG}")
        return 1

    if check_progress_log_references(latest_run):
        print(f"[OK] {latest_run} is referenced in Progress_Log.md")
        return 0
    else:
        print(
            f"[FAIL] {latest_run} is NOT referenced in docs/00_Project_Admin/Progress_Log.md"
        )
        print()
        print("To fix:")
        print(
            f"  1. Add an entry for {latest_run} in docs/00_Project_Admin/Progress_Log.md"
        )
        print("  2. Commit and push the update")
        print()
        print("Example entry:")
        print(f"  ### <date> — {latest_run}")
        print("  - <summary of work done>")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
