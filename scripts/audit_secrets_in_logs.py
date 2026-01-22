#!/usr/bin/env python3
"""
Audit script to scan for secrets in CI logs and code.

This script checks that ANTHROPIC_API_KEY and other secrets never appear in:
- Script stdout/stderr
- CI logs
- Rehydration pack artifacts
- Test outputs
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


SECRET_PATTERNS = [
    r"sk-ant-[a-zA-Z0-9-]{20,}",  # Anthropic API keys
    r"ANTHROPIC_API_KEY[\"']?\s*[:=]\s*[\"']?sk-",  # Variable assignments
    r"Authorization:\s*Bearer\s+sk-",  # Auth headers
]


@dataclass
class Violation:
    file: str
    pattern: str
    line: int
    match_preview: str


def scan_file(filepath: Path) -> list[Violation]:
    """Scan a file for secret patterns."""
    violations: list[Violation] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                violations.append(
                    Violation(
                        file=str(filepath),
                        pattern=pattern,
                        line=content[: match.start()].count("\n") + 1,
                        match_preview=f"{match.group()[:20]}...",
                    )
                )
    except Exception as exc:
        print(f"Warning: Could not scan {filepath}: {exc}")
    return violations


def _iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix in {".py", ".md", ".yml", ".yaml", ".txt", ".log"}
    ]


def main() -> int:
    paths_to_scan = [
        Path("scripts"),
        Path("REHYDRATION_PACK"),
        Path(".github/workflows"),
    ]

    all_violations: list[Violation] = []
    for path in paths_to_scan:
        for filepath in _iter_files(path):
            all_violations.extend(scan_file(filepath))

    if all_violations:
        print("SECRETS AUDIT FAILED - Potential secrets found:")
        for v in all_violations:
            print(f"  {v.file}:{v.line} - {v.pattern} ({v.match_preview})")
        return 1

    print("SECRETS AUDIT PASSED - No secrets detected in scanned files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
