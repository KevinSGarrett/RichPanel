#!/usr/bin/env python3
"""
branch_budget_check.py

Helps prevent "branch explosion" (50-100 remote branches) by reporting the number
of remote branches and warning/failing when thresholds are exceeded.

This is a helper tool for agents/integrator. It is not required for foundation mode.

Usage:
  python scripts/branch_budget_check.py
  python scripts/branch_budget_check.py --max 10
  python scripts/branch_budget_check.py --strict
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--max",
        type=int,
        default=10,
        help="Max allowed active remote branches (default: 10)",
    )
    ap.add_argument(
        "--strict", action="store_true", help="Exit non-zero if over budget"
    )
    args = ap.parse_args()

    root = repo_root()
    try:
        subprocess.run(
            ["git", "fetch", "--prune"],
            cwd=str(root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        p = subprocess.run(
            ["git", "branch", "-r"], cwd=str(root), capture_output=True, text=True
        )
        if p.returncode != 0:
            print("[WARN] Could not list remote branches.")
            return 0
        branches = []
        for line in p.stdout.splitlines():
            b = line.strip()
            if not b or b.endswith("-> origin/main") or b.endswith("-> origin/HEAD"):
                continue
            branches.append(b)

        count = len(branches)
        print(f"[INFO] Active remote branches: {count} (budget={args.max})")
        if count > args.max:
            print(
                "[WARN] Branch budget exceeded. Consider deleting merged run branches."
            )
            # show a few
            for b in branches[:25]:
                print(f"- {b}")
            return 2 if args.strict else 0

        print("[OK] Branch budget within limits.")
        return 0
    except Exception as e:
        print(f"[WARN] branch budget check skipped: {e}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
