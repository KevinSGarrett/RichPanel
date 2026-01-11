#!/usr/bin/env python3
"""
regen_reference_registry.py

Regenerates machine-readable registries for the `reference/` library.

Outputs
- reference/_generated/reference_registry.json
- reference/_generated/reference_registry.compact.json
- reference/richpanel/_generated/reference_registry.json
- reference/richpanel/_generated/reference_registry.compact.json

Design goals
- Standard library only
- Fast enough to run frequently
- AI-first: paths + titles + tags for retrieval without grepping

Usage
  python scripts/regen_reference_registry.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
REF_ROOT = REPO_ROOT / "reference"

IGNORE_DIRS = {"_generated"}

WORD_SPLIT_RE = re.compile(r"[\s_\-–—]+")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def deterministic_size(path: Path) -> int:
    """
    Return a size that is stable across platforms by normalizing newline handling
    for UTF-8 text files. Binary files fall back to the on-disk byte size.
    """
    try:
        txt = path.read_text(encoding="utf-8")
        return len(txt.encode("utf-8"))
    except Exception:
        return path.stat().st_size


def title_guess_for(path: Path) -> str:
    stem = path.stem.replace("_", " ").replace("-", " ").strip()
    ext = path.suffix.lower()
    try:
        if ext == ".md":
            txt = read_text(path)
            m = re.search(r"^#\s+(.+?)\s*$", txt, flags=re.M)
            return m.group(1).strip() if m else stem
        if ext == ".txt":
            txt = read_text(path)
            for line in txt.splitlines():
                s = line.strip()
                if not s:
                    continue
                s = re.sub(r"^\s*#\s*", "", s)
                s = re.sub(r"^\s*Title:\s*", "", s, flags=re.I)
                if 5 <= len(s) <= 120:
                    return s
                break
    except Exception:
        pass
    return stem


def tags_for(rel_parts: Tuple[str, ...], stem: str) -> List[str]:
    tags = set()
    for part in rel_parts[:-1]:
        if part:
            tags.add(part.lower().replace(" ", "_"))
    for token in WORD_SPLIT_RE.split(stem.lower()):
        t = token.strip()
        if len(t) < 3:
            continue
        if t in {"the", "and", "for", "with", "your", "from", "into", "via"}:
            continue
        tags.add(t)
    return sorted(list(tags))[:12]


def scan_reference_files() -> List[Dict]:
    records: List[Dict] = []
    if not REF_ROOT.exists():
        return records

    for path in sorted(
        [p for p in REF_ROOT.rglob("*") if p.is_file()],
        key=lambda p: p.relative_to(REF_ROOT).as_posix(),
    ):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue

        rel_to_repo = path.relative_to(REPO_ROOT).as_posix()
        rel_under_ref = path.relative_to(REF_ROOT)
        parts = rel_under_ref.parts

        vendor = "root"
        if len(parts) > 1:
            vendor = parts[0]

        # Category is vendor-specific, but we keep a simple second-level hint when present
        category = ""
        if vendor != "root" and len(parts) > 2:
            category = parts[1]

        title = title_guess_for(path)
        tags = tags_for(parts, path.stem)

        records.append(
            {
                "path": rel_to_repo,
                "vendor": vendor,
                "category": category,
                "title_guess": title,
                "type": path.suffix.lower().lstrip("."),
                "size_bytes": deterministic_size(path),
                "tags": tags,
            }
        )
    return records


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def main() -> int:
    records = scan_reference_files()

    # Combined registry
    combined = {
        "count": len(records),
        "records": records,
    }
    write_json(REF_ROOT / "_generated" / "reference_registry.json", combined)
    write_json(
        REF_ROOT / "_generated" / "reference_registry.compact.json",
        [
            {
                "path": r["path"],
                "vendor": r["vendor"],
                "title": r["title_guess"],
                "type": r["type"],
                "tags": r["tags"],
            }
            for r in records
        ],
    )

    # Vendor-specific: Richpanel (if present)
    rp_root = REF_ROOT / "richpanel"
    if rp_root.exists():
        rp_records = [r for r in records if r["vendor"] == "richpanel"]
        rp_obj = {"count": len(rp_records), "records": rp_records}
        write_json(rp_root / "_generated" / "reference_registry.json", rp_obj)
        write_json(
            rp_root / "_generated" / "reference_registry.compact.json",
            [
                {
                    "path": r["path"],
                    "title": r["title_guess"],
                    "category": r.get("category", ""),
                    "type": r["type"],
                    "tags": r["tags"],
                }
                for r in rp_records
            ],
        )

    print(f"OK: reference registry regenerated ({len(records)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
