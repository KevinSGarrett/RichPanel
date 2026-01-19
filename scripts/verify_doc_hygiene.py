#!/usr/bin/env python3
"""
verify_doc_hygiene.py

Scans canonical docs (linked from docs/INDEX.md) for ambiguous placeholders that
cause AI drift.

Default behavior:
- report warnings
- exit 0

Strict mode:
- exit non-zero if any issues are found

Design constraints:
- Standard library only
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Tuple


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+")

# Ambiguous placeholders to discourage in canonical docs.
BANNED_PATTERNS = [
    (re.compile(r"\.\.\."), "contains '...' (ambiguous placeholder)"),
    (re.compile(r"…"), "contains unicode ellipsis '…' (ambiguous placeholder)"),
]


def extract_local_links(index_md: str) -> List[str]:
    links: List[str] = []
    for m in LINK_RE.finditer(index_md):
        target = m.group(1).strip()

        # ignore anchors
        target = target.split("#", 1)[0].split("?", 1)[0].strip()
        if not target:
            continue

        # ignore external links
        if (
            target.startswith("http://")
            or target.startswith("https://")
            or target.startswith("mailto:")
        ):
            continue

        # normalize
        target = target.lstrip("./")
        links.append(target)
    # de-dup while preserving order
    seen = set()
    out: List[str] = []
    for t in links:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def scan_file(path: Path) -> List[Tuple[str, int, str]]:
    issues: List[Tuple[str, int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception as e:
        return [(path.as_posix(), 0, f"unable to read file: {e}")]

    for i, line in enumerate(lines, start=1):
        for rx, msg in BANNED_PATTERNS:
            if rx.search(line):
                issues.append((path.as_posix(), i, msg))
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--strict", action="store_true", help="Fail if hygiene issues found"
    )
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    docs_root = repo_root / "docs"
    index_path = docs_root / "INDEX.md"
    if not index_path.exists():
        print("FAIL: docs/INDEX.md not found")
        return 1

    index_md = index_path.read_text(encoding="utf-8", errors="ignore")
    links = extract_local_links(index_md)

    # Resolve links relative to docs/ (INDEX lives in docs/)
    canonical_files: List[Path] = []
    for link in links:
        # support links that go up to repo root (e.g. ../CHANGELOG.md)
        resolved = (docs_root / link).resolve()
        if not resolved.exists():
            # missing targets are handled by other validators
            pass
        if resolved.exists() and resolved.is_file():
            canonical_files.append(resolved)
        else:
            # allow directories
            if resolved.exists() and resolved.is_dir():
                continue

    # Scan
    all_issues: List[Tuple[str, int, str]] = []
    for f in canonical_files:
        all_issues.extend(scan_file(f))

    if not all_issues:
        print(
            "[OK] Doc hygiene check passed (no banned placeholders found in INDEX-linked docs)."
        )
        return 0

    print("WARN: Doc hygiene issues found in INDEX-linked docs:")
    for path, line, msg in all_issues:
        print(f"- {path}:{line} — {msg}")

    if args.strict:
        print("FAIL (strict): hygiene issues must be resolved")
        return 2

    print("[OK] (non-strict) hygiene issues reported as warnings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
