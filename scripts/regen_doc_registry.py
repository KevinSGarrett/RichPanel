#!/usr/bin/env python3
"""
regen_doc_registry.py

Regenerates navigation artifacts for the docs library.

Outputs:
- docs/REGISTRY.md
- docs/_generated/doc_registry.json
- docs/_generated/doc_registry.compact.json
- docs/_generated/doc_outline.json
- docs/_generated/heading_index.json

Design goals:
- **AI-first retrieval**: fast lookup without grepping.
- **Low drift**: canonical docs are derived from docs/INDEX.md links.
- **No heavy deps**: standard library only.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
GENERATED_DIR = DOCS_ROOT / "_generated"
INDEX_FILE = DOCS_ROOT / "INDEX.md"

# Folders that exist for historical reasons (plan iterations). Treat as legacy by default.
ALWAYS_CANONICAL = {
    "INDEX.md",
    "CODEMAP.md",
    "REGISTRY.md",
    "ROADMAP.md",
}

LEGACY_SECTIONS = {
    "06_Data_Privacy_Observability",
    "10_Governance_Continuous_Improvement",
    "11_Cursor_Agent_Work_Packages",
    "Waves",
}

CODE_FENCE_RE = re.compile(r"^\s*```")
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.UNICODE)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")
LAST_UPDATED_RE = re.compile(r"(?im)^last updated:\s*(.+?)\s*$")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def die(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def slugify_github_like(text: str) -> str:
    """
    Approximate GitHub anchor slug rules well enough for internal indexing.
    """
    t = text.strip().lower()
    # Remove markdown formatting characters
    t = re.sub(r"[`*_~]", "", t)
    # Remove anything that is not alnum/space/hyphen
    t = re.sub(r"[^a-z0-9 \-]", "", t)
    # Collapse whitespace to hyphen
    t = re.sub(r"\s+", "-", t)
    # Collapse multiple hyphens
    t = re.sub(r"-{2,}", "-", t)
    return t.strip("-")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def extract_title(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        m = TITLE_RE.match(line.strip())
        if m:
            return m.group(1).strip()
    return fallback


def extract_last_updated(md_text: str) -> str:
    m = LAST_UPDATED_RE.search(md_text)
    if not m:
        return ""
    return m.group(1).strip()


def extract_outline(md_text: str, max_items: int = 80) -> List[Dict[str, object]]:
    outline: List[Dict[str, object]] = []
    in_code = False
    for raw in md_text.splitlines():
        if CODE_FENCE_RE.match(raw):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEADING_RE.match(raw)
        if not m:
            continue
        level = len(m.group(1))
        text = m.group(2).strip()
        # ignore empty headings
        if not text:
            continue
        # trim very long headings
        if len(text) > 140:
            text = text[:137] + "..."
        outline.append({"level": level, "text": text, "anchor": slugify_github_like(text)})
        if len(outline) >= max_items:
            break
    return outline


def parse_index_links(index_text: str) -> List[str]:
    links: List[str] = []
    for target in MD_LINK_RE.findall(index_text):
        target = target.strip()
        if not target:
            continue
        # ignore external
        if re.match(r"^(https?:)?//", target) or target.startswith("mailto:"):
            continue
        # strip anchor/query
        target = target.split("#", 1)[0].split("?", 1)[0]
        target = target.lstrip("./")
        if not target:
            continue
        links.append(target)
    return links


def status_for(rel_path: str, in_index: bool) -> str:
    parts = rel_path.split("/", 1)
    section = parts[0] if parts else "Root"
    if section == "_generated":
        return "generated"
    if section in LEGACY_SECTIONS:
        return "legacy"
    if in_index:
        return "canonical"
    return "supplemental"


def main() -> int:
    if not DOCS_ROOT.exists():
        return die(f"docs root not found: {DOCS_ROOT}")

    if not INDEX_FILE.exists():
        return die(f"missing docs/INDEX.md: {INDEX_FILE}")

    index_text = read_text(INDEX_FILE)
    index_links = set([p for p in parse_index_links(index_text) if p.endswith(".md")])

    md_files = sorted(
        [p for p in DOCS_ROOT.rglob("*.md") if p.is_file()],
        key=lambda p: p.relative_to(DOCS_ROOT).as_posix(),
    )

    # Build registry records
    records: List[Dict[str, object]] = []
    outlines: List[Dict[str, object]] = []
    heading_index: Dict[str, List[Dict[str, str]]] = {}

    for p in md_files:
        rel = str(p.relative_to(DOCS_ROOT)).replace("\\", "/")
        md_text = read_text(p)

        title = extract_title(md_text, fallback=p.stem.replace("_", " "))
        last_updated = extract_last_updated(md_text)
        in_index = (rel in index_links) or (rel in ALWAYS_CANONICAL)

        wc = len(re.findall(r"\b\w+\b", md_text))
        approx_tokens = int(wc * 1.3)

        st = status_for(rel, in_index)

        records.append(
            {
                "path": rel,
                "title": title,
                "section": rel.split("/")[0] if "/" in rel else "Root",
                "status": st,
                "in_index": in_index,
                "word_count": wc,
                "approx_tokens": approx_tokens,
                "last_updated": last_updated,
            }
        )

        outline = extract_outline(md_text)
        outlines.append({"path": rel, "outline": outline})

        # Build heading index (normalized heading text -> [path+anchor])
        for h in outline:
            key = str(h["text"]).strip().lower()
            if not key:
                continue
            heading_index.setdefault(key, []).append(
                {"path": rel, "anchor": str(h["anchor"])}
            )

    # Write docs/REGISTRY.md
    groups: Dict[str, List[Dict[str, object]]] = {}
    for rec in records:
        section = str(rec["section"])
        groups.setdefault(section, []).append(rec)

    def marker(st: str) -> str:
        return {
            "canonical": "✅",
            "supplemental": "📎",
            "legacy": "🗄️",
            "generated": "🛠️",
        }.get(st, "•")

    lines: List[str] = []
    lines.append("# Docs Registry (Complete Listing)\n")
    lines.append(
        "This registry lists **every markdown file** under `docs/` so nothing becomes orphaned.\n"
    )
    lines.append("Use `docs/INDEX.md` for curated navigation.\n")
    lines.append("Legend:\n")
    lines.append("- ✅ canonical (linked from `docs/INDEX.md`)\n")
    lines.append("- 📎 supplemental (not in index, but not marked legacy)\n")
    lines.append("- 🗄️ legacy/historical (duplicate/older plan paths)\n")
    lines.append("- 🛠️ generated (machine output under `_generated/`)\n")

    for section in sorted(groups.keys(), key=lambda x: (x != "Root", x)):
        lines.append(f"\n## {section}\n")
        for rec in sorted(groups[section], key=lambda r: str(r["path"])):
            rel = str(rec["path"])
            st = str(rec["status"])
            title = str(rec["title"])
            lines.append(f"- {marker(st)} [{title}]({rel})  (`{rel}`)")
    (DOCS_ROOT / "REGISTRY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Machine outputs
    GENERATED_DIR.mkdir(exist_ok=True)

    (GENERATED_DIR / "doc_registry.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (GENERATED_DIR / "doc_registry.compact.json").write_text(
        json.dumps(records, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
    )
    (GENERATED_DIR / "doc_outline.json").write_text(
        json.dumps(outlines, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (GENERATED_DIR / "heading_index.json").write_text(
        json.dumps(heading_index, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"OK: regenerated registry for {len(records)} docs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
