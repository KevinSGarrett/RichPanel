#!/usr/bin/env python3
"""
run_ci_checks.py

A single entrypoint for the "CI-equivalent" checks that agents must run locally
and that GitHub Actions should run in CI.

Design goals:
- Standard library only
- Cross-platform (Windows/macOS/Linux)
- Deterministic and repo-relative
- Helpful output for agent self-fix loops

Usage:
  python scripts/run_ci_checks.py          # local run (regen + verify)
  python scripts/run_ci_checks.py --ci     # CI run (regen + require clean git diff)

What it does:
1) Regenerates deterministic registries/checklists.
2) Runs validation scripts.
3) In --ci mode, fails if regeneration produced uncommitted diffs.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> int:
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=str(cwd))
    return int(p.returncode)


def git_available(cwd: Path) -> bool:
    try:
        p = subprocess.run(
            ["git", "--version"],
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return p.returncode == 0
    except Exception:
        return False


def git_status_porcelain(cwd: Path) -> str:
    p = subprocess.run(["git", "status", "--short"], cwd=str(cwd), capture_output=True, text=True)
    if p.returncode != 0:
        return ""
    return p.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--ci", action="store_true", help="CI mode: require no diffs after regen"
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]

    # 1) Regenerate deterministic files (should be committed).
    regen_steps = [
        ["python", "scripts/regen_doc_registry.py"],
        ["python", "scripts/regen_reference_registry.py"],
        ["python", "scripts/regen_plan_checklist.py"],
    ]
    for cmd in regen_steps:
        rc = run(cmd, cwd=root)
        if rc != 0:
            print("\n[FAIL] Regen step failed.")
            return rc

    # 2) Validate
    checks = [
        ["python", "scripts/verify_agent_prompts_fresh.py"],
        ["python", "scripts/verify_rehydration_pack.py"],
        ["python", "scripts/verify_doc_hygiene.py"],
        ["python", "scripts/verify_plan_sync.py"],
        ["python", "scripts/verify_secret_inventory_sync.py"],
        ["python", "scripts/verify_admin_logs_sync.py"],
        ["python", "scripts/test_pipeline_handlers.py"],
        ["python", "scripts/test_richpanel_client.py"],
        ["python", "scripts/test_openai_client.py"],
        ["python", "scripts/test_shopify_client.py"],
        ["python", "scripts/test_shipstation_client.py"],
        ["python", "scripts/test_order_lookup.py"],
        ["python", "scripts/test_llm_routing.py"],
        ["python", "scripts/test_llm_reply_rewriter.py"],
        ["python", "scripts/check_protected_deletes.py"]
        + (["--ci"] if args.ci else []),
    ]
    for cmd in checks:
        rc = run(cmd, cwd=root)
        if rc != 0:
            print("\n[FAIL] Validation failed.")
            return rc

    # 3) CI mode: ensure regen produced no uncommitted diffs.
    if args.ci and git_available(root):
        status = git_status_porcelain(root)
        if status:
            print(
                "\n[FAIL] Generated files changed after regen. Commit the regenerated outputs."
            )
            print(
                "Hint: run `python scripts/run_ci_checks.py` locally, commit, and push."
            )
            print("\nUncommitted changes:")
            print(status)
            return 2

    print("\n[OK] CI-equivalent checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
