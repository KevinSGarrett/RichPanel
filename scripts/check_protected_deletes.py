#!/usr/bin/env python3
"""check_protected_deletes.py

Prevents accidental deletion/renaming of protected repo paths.

Why this exists
- Multi-agent work + "cleanups" can accidentally delete critical docs/structure.
- We require explicit approval for destructive ops in:
  REHYDRATION_PACK/DELETE_APPROVALS.yaml

Design goals
- Standard library only
- Works in BOTH contexts:
  1) Local (agents before commit): check staged + working tree
  2) CI (PR/main): check commit range

Usage
  python scripts/check_protected_deletes.py              # local: staged + working tree
  python scripts/check_protected_deletes.py --ci         # CI: uses best-effort commit range
  python scripts/check_protected_deletes.py --range A...B

Exit codes
  0 = OK
  2 = Violations found (unapproved protected delete/rename)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

PROTECTED_PREFIXES = [
    "docs/",
    "REHYDRATION_PACK/",
    "PM_REHYDRATION_PACK/",
    "reference/",
    ".github/",
    "scripts/",
    "policies/",
]

PROTECTED_ROOT_FILES = {
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    ".gitignore",
}

APPROVALS_FILE = "REHYDRATION_PACK/DELETE_APPROVALS.yaml"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_git(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        p = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True)
        out = (p.stdout or "") + (p.stderr or "")
        return int(p.returncode), out
    except Exception as e:
        return 1, str(e)


def git_is_repo(cwd: Path) -> bool:
    rc, out = run_git(["rev-parse", "--is-inside-work-tree"], cwd)
    return rc == 0 and "true" in out.lower()


def read_approvals(cwd: Path) -> set[str]:
    p = cwd / APPROVALS_FILE
    if not p.exists():
        return set()
    out: set[str] = set()
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        # YAML-ish list items: - path/to/file
        if s.startswith("-"):
            s = s[1:].strip()
        s = s.strip().strip('"').strip("'")
        if s:
            out.add(s)
    return out


def is_protected(path: str) -> bool:
    path = path.replace("\\", "/")
    if path in PROTECTED_ROOT_FILES:
        return True
    return any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def parse_name_status(output: str) -> list[tuple[str, str, str | None]]:
    """Return list of (status, path, new_path_if_rename)."""
    changes: list[tuple[str, str, str | None]] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = re.split(r"\s+", line)
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            changes.append((status, parts[1], parts[2]))
        elif status == "D" and len(parts) >= 2:
            changes.append((status, parts[1], None))
    return changes


def diff_staged_and_working(cwd: Path) -> tuple[bool, str]:
    """Return (ok, output). Always best-effort; ok means git ran."""
    out_parts: list[str] = []
    ok_any = False

    for args in (
        ["diff", "--name-status", "--diff-filter=DR", "--cached"],
        ["diff", "--name-status", "--diff-filter=DR"],
    ):
        rc, out = run_git(args, cwd)
        if rc == 0:
            ok_any = True
            if out.strip():
                out_parts.append(out.strip())

    return ok_any, ("\n".join(out_parts) + ("\n" if out_parts else ""))


def resolve_ci_range(cwd: Path) -> str | None:
    """Best-effort diff range for CI contexts."""
    # PRs: GitHub provides base ref (e.g., 'main').
    base = (os.getenv("GITHUB_BASE_REF") or "").strip()
    if base:
        # Prefer origin/<base> if present; otherwise just use HEAD~1.
        rc, _ = run_git(["show-ref", "--verify", "--quiet", f"refs/remotes/origin/{base}"], cwd)
        if rc == 0:
            return f"origin/{base}...HEAD"

    # Main or other pushes: use last commit range when possible.
    rc, _ = run_git(["rev-parse", "--verify", "HEAD~1"], cwd)
    if rc == 0:
        return "HEAD~1...HEAD"

    # Initial commit: diff via show.
    rc, _ = run_git(["rev-parse", "--verify", "HEAD"], cwd)
    if rc == 0:
        return "HEAD"

    return None


def diff_for_range(cwd: Path, diff_range: str) -> tuple[bool, str, str]:
    """Return (ok, output, source_desc)."""
    if diff_range == "HEAD":
        rc, out = run_git(["show", "--name-status", "--format=", "--diff-filter=DR", "HEAD"], cwd)
        return (rc == 0), out, "git show HEAD"

    rc, out = run_git(["diff", "--name-status", "--diff-filter=DR", diff_range], cwd)
    return (rc == 0), out, f"git diff {diff_range}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ci", action="store_true", help="CI mode: check commit range (best-effort)")
    ap.add_argument("--range", dest="diff_range", help="Explicit diff range, e.g. HEAD~1...HEAD")
    args = ap.parse_args()

    root = repo_root()

    if not git_is_repo(root):
        print("[INFO] Protected delete check skipped (not a git work tree).")
        return 0

    approvals = read_approvals(root)

    # --- 1) Default local behavior: staged + working tree ---
    if not args.ci and not args.diff_range:
        ok, out = diff_staged_and_working(root)
        if not ok:
            print("[INFO] Protected delete check skipped (git diff unavailable).")
            return 0
        changes = parse_name_status(out)
        violations = []
        for status, path, new_path in changes:
            # For renames, treat old path as the protected-delete target.
            target = path
            if is_protected(target) and target not in approvals:
                violations.append((status, path, new_path))

        if violations:
            print("[FAIL] Unapproved delete/rename of protected paths detected (local diff).")
            for status, path, new_path in violations:
                if status.startswith("R"):
                    print(f"- {status}: {path} -> {new_path}")
                else:
                    print(f"- {status}: {path}")
            print("\nTo approve intentionally, add exact paths to:")
            print(f"- {APPROVALS_FILE}")
            return 2

        print("[OK] No unapproved protected deletes/renames detected (local diff).")
        return 0

    # --- 2) CI / explicit range behavior ---
    diff_range = args.diff_range or resolve_ci_range(root)
    if not diff_range:
        print("[INFO] Protected delete check: no diff range could be determined. Skipping.")
        return 0

    ok, out, source = diff_for_range(root, diff_range)
    if not ok:
        print(f"[INFO] Protected delete check: could not compute diff ({source}). Skipping.")
        return 0

    changes = parse_name_status(out)
    violations = []
    for status, path, new_path in changes:
        target = path
        if is_protected(target) and target not in approvals:
            violations.append((status, path, new_path))

    if violations:
        print(f"[FAIL] Unapproved delete/rename of protected paths detected ({source}).")
        for status, path, new_path in violations:
            if status.startswith("R"):
                print(f"- {status}: {path} -> {new_path}")
            else:
                print(f"- {status}: {path}")
        print("\nTo approve intentionally, add exact paths to:")
        print(f"- {APPROVALS_FILE}")
        return 2

    print(f"[OK] No unapproved protected deletes/renames detected ({source}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
