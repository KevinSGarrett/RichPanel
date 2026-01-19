#!/usr/bin/env python3
"""
regen_plan_checklist.py

Extracts checklist items from the documentation plan and produces a consolidated
plan checklist for easy tracking.

Outputs:
- docs/00_Project_Admin/To_Do/_generated/plan_checklist.json
- docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md
- docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_SUMMARY.md

Notes:
- Standard library only.
- This is intentionally *mechanical* extraction of markdown checkboxes.
  The canonical status remains in the source docs; this file is a compiled view.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[(?P<state>[xX\s])\]\s+(?P<text>.+?)\s*$")
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")


@dataclass
class Task:
    id: str
    checked: bool
    text: str
    source_path: str
    line: int
    heading_path: str


def stable_id(source_path: str, heading_path: str, text: str) -> str:
    raw = f"{source_path}|{heading_path}|{text}".encode("utf-8")
    h = hashlib.sha1(raw).hexdigest()[:10].upper()
    return f"PLN-{h}"


def iter_plan_docs(docs_root: Path) -> List[Path]:
    """Return markdown files to scan for plan checklists."""
    all_md = sorted(docs_root.rglob("*.md"))
    keep: List[Path] = []
    for p in all_md:
        rel = p.relative_to(docs_root).as_posix()

        # Skip generated artifacts
        if rel.startswith("_generated/"):
            continue

        # Skip agent ops (policies/templates are operational, not plan tasks)
        if rel.startswith("98_Agent_Ops/"):
            continue

        # Skip To_Do folder itself (this is the output/tracking system)
        if rel.startswith("00_Project_Admin/To_Do/"):
            continue

        # Skip legacy redirect folders
        if rel.startswith("06_Data_Privacy_Observability/"):
            continue
        if rel.startswith("10_Governance_Continuous_Improvement/"):
            continue
        if rel.startswith("11_Cursor_Agent_Work_Packages/"):
            continue

        keep.append(p)
    return keep


def extract_tasks(md_path: Path, docs_root: Path) -> List[Task]:
    rel_path = md_path.relative_to(docs_root).as_posix()
    lines = md_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    # Track heading stack, keep up to H3 for context
    headings: Dict[int, str] = {}
    tasks: List[Task] = []

    for idx, line in enumerate(lines, start=1):
        h = HEADING_RE.match(line)
        if h:
            level = len(h.group("hashes"))
            title = h.group("title").strip()
            headings[level] = title
            # clear deeper levels
            for deeper in list(headings.keys()):
                if deeper > level:
                    del headings[deeper]
            continue

        m = CHECKBOX_RE.match(line)
        if not m:
            continue

        checked = m.group("state").lower() == "x"
        text = m.group("text").strip()

        # Build heading path from the nearest H1/H2/H3
        hp_parts: List[str] = []
        for level in (1, 2, 3):
            if level in headings:
                hp_parts.append(headings[level])
        heading_path = " > ".join(hp_parts) if hp_parts else "(no heading)"

        tid = stable_id(rel_path, heading_path, text)
        tasks.append(
            Task(
                id=tid,
                checked=checked,
                text=text,
                source_path=f"docs/{rel_path}",
                line=idx,
                heading_path=heading_path,
            )
        )
    return tasks


def group_tasks(tasks: List[Task]) -> Dict[str, Dict[str, List[Task]]]:
    """Group: source_path -> heading_path -> tasks."""
    grouped: Dict[str, Dict[str, List[Task]]] = {}
    for t in tasks:
        grouped.setdefault(t.source_path, {}).setdefault(t.heading_path, []).append(t)
    return grouped


def write_json(out_path: Path, tasks: List[Task]) -> None:
    out = []
    for t in tasks:
        out.append(
            {
                "id": t.id,
                "checked": t.checked,
                "text": t.text,
                "source_path": t.source_path,
                "line": t.line,
                "heading_path": t.heading_path,
            }
        )
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")


def write_extracted_md(out_path: Path, tasks: List[Task]) -> None:
    grouped = group_tasks(tasks)
    total = len(tasks)
    checked = sum(1 for t in tasks if t.checked)
    unchecked = total - checked

    md: List[str] = []
    md.append("# PLAN CHECKLIST — Extracted (Generated)")
    md.append("")
    md.append("Generated: (deterministic; see git history)  ")
    md.append(
        "Source: markdown checkboxes across docs/ (excluding Agent Ops and To_Do outputs)"
    )
    md.append("")
    md.append(f"Counts: total={total}, checked={checked}, unchecked={unchecked}")
    md.append("")
    md.append("**Do not edit this file by hand.** Edit the source docs and rerun:")
    md.append("- `python scripts/regen_plan_checklist.py`")
    md.append("")
    md.append("---")
    md.append("")

    for source_path in sorted(grouped.keys()):
        md.append(f"## {source_path}")
        md.append("")
        headings = grouped[source_path]
        for heading_path in sorted(headings.keys()):
            md.append(f"### {heading_path}")
            for t in headings[heading_path]:
                box = "x" if t.checked else " "
                md.append(f"- [{box}] {t.id} — {t.text}  ")
                md.append(f"  - Source line: {t.line}")
            md.append("")
        md.append("")

    out_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")


def write_summary_md(out_path: Path, tasks: List[Task]) -> None:
    """Write a small summary grouped by top-level docs section."""

    def top_section(source_path: str) -> str:
        # source_path is like docs/06_Security_Privacy_Compliance/...
        rel = source_path.removeprefix("docs/")
        return rel.split("/", 1)[0] if "/" in rel else rel

    by_section: Dict[str, Tuple[int, int]] = {}  # section -> (total, checked)
    for t in tasks:
        sec = top_section(t.source_path)
        total, checked = by_section.get(sec, (0, 0))
        by_section[sec] = (total + 1, checked + (1 if t.checked else 0))

    lines: List[str] = []
    lines.append("# PLAN CHECKLIST — Summary (Generated)")
    lines.append("")
    lines.append("Generated: (deterministic; see git history)  ")
    lines.append("")
    lines.append("Counts by docs section:")
    lines.append("")
    lines.append("| Docs section | Total | Checked | Unchecked |")
    lines.append("|---|---:|---:|---:|")
    for sec in sorted(by_section.keys()):
        total, checked = by_section[sec]
        lines.append(f"| `{sec}` | {total} | {checked} | {total - checked} |")
    lines.append("")
    lines.append("Full extracted list:")
    lines.append(
        "- `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md`"
    )
    lines.append("")
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    docs_root = repo_root / "docs"
    out_dir = docs_root / "00_Project_Admin" / "To_Do" / "_generated"
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks: List[Task] = []
    for md in iter_plan_docs(docs_root):
        tasks.extend(extract_tasks(md, docs_root))

    # Deterministic ordering
    tasks.sort(key=lambda t: (t.source_path, t.heading_path, t.id))

    write_json(out_dir / "plan_checklist.json", tasks)
    write_extracted_md(out_dir / "PLAN_CHECKLIST_EXTRACTED.md", tasks)
    write_summary_md(out_dir / "PLAN_CHECKLIST_SUMMARY.md", tasks)

    print(f"[OK] Extracted {len(tasks)} checklist items.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
