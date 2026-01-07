#!/usr/bin/env python3
"""
Ensure current agent prompts are not a repeat of recent archives.

This script compares `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` against the
most recent prompt archives and fails if an exact (whitespace-insensitive)
match is found. Use `Prompt-Repeat-Override: true` in the current file to
explicitly bypass the guard when needed.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ARCHIVE_DEPTH = 5
ROOT = Path(__file__).resolve().parents[1]
CURRENT_PROMPTS_PATH = ROOT / "REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md"
ARCHIVE_GLOB = "REHYDRATION_PACK/RUNS/RUN_*/C/AGENT_PROMPTS_ARCHIVE*.md"
OVERRIDE_TOKEN = "prompt-repeat-override: true"


_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)\n```", re.DOTALL)


def _strip_non_semantic_lines(content: str) -> str:
    """
    Remove lines known to vary run-to-run without affecting the prompt body.

    This is intentionally conservative: we strip common "metadata" lines but
    preserve the actual instructions/tasks.
    """
    out_lines: list[str] = []
    for raw_line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        lower = line.strip().lower()

        # Guard override token: don't let it affect fingerprints/comparison.
        if lower == OVERRIDE_TOKEN:
            continue

        # Common non-semantic metadata that changes every run/cycle.
        if re.match(r"^\s*\*\*\s*run id\s*:\s*\*\*.*$", line, flags=re.IGNORECASE):
            continue
        if re.match(r"^\s*run[_\s-]*id\s*[:=].*$", line, flags=re.IGNORECASE):
            continue
        if re.match(r"^\s*agent\s*[:=]\s*[a-z]\s*$", line, flags=re.IGNORECASE):
            continue
        if re.match(r"^\s*\*\*\s*agent\s*:\s*\*\*.*$", line, flags=re.IGNORECASE):
            continue
        if re.match(r"^\s*(as[-\s]*of|timestamp)\s*[:=].*$", line, flags=re.IGNORECASE):
            continue
        if re.match(r"^\s*\*\*\s*as\s+of\s*:\s*\*\*.*$", line, flags=re.IGNORECASE):
            continue
        if re.match(
            r"^\s*(prompt\s*(hash|fingerprint)|fingerprint|prompt set fingerprint)\s*[:=].*$",
            line,
            flags=re.IGNORECASE,
        ):
            continue

        # Archive wrapper headers vary and shouldn't affect dedup.
        if re.match(r"^\s*#\s*archive\b.*$", line, flags=re.IGNORECASE):
            continue
        if re.match(r"^\s*archived\s+as\s+part\s+of\b.*$", line, flags=re.IGNORECASE):
            continue

        out_lines.append(line)

    return "\n".join(out_lines).strip()


def _extract_prompt_bodies(content: str) -> list[str]:
    """
    Extract likely prompt bodies from a markdown file.

    Primary: fenced code blocks (```text / ```markdown / ```).
    Fallback: the whole file with non-semantic lines stripped.
    """
    stripped = _strip_non_semantic_lines(content)
    blocks = [m.group(1).strip() for m in _FENCE_RE.finditer(stripped)]
    blocks = [b for b in blocks if b]
    return blocks if blocks else [stripped]


def _normalize_prompt_body(body: str) -> str:
    # Normalize line endings + whitespace; keep semantic characters.
    text = body.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip()
    text = re.sub(r"[ \t]+", " ", text)  # collapse runs of spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)  # collapse huge vertical whitespace
    return text.strip()


def prompt_set_fingerprint(content: str) -> tuple[str, list[str]]:
    """
    Returns:
      - a stable fingerprint for the whole prompt set
      - per-block fingerprints (stable, order-independent at the set level)
    """
    blocks = _extract_prompt_bodies(content)
    block_fps: list[str] = []
    for block in blocks:
        normalized = _normalize_prompt_body(block)
        fp = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        block_fps.append(fp)

    # Stable across prompt ordering: treat the prompt set as a multiset of blocks.
    set_material = "\n".join(sorted(block_fps))
    set_fp = hashlib.sha256(set_material.encode("utf-8")).hexdigest()
    return set_fp, block_fps


def archive_sort_key(path: Path) -> tuple[str, float]:
    # Sort primarily by run folder name, then by file mtime as a fallback.
    run_dir = path.parent.parent.name
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    return (run_dir, mtime)


def ordinal_label(idx: int) -> str:
    labels = ["newest", "2nd newest", "3rd newest", "4th newest", "5th newest"]
    if idx < len(labels):
        return labels[idx]
    return f"{idx + 1}th newest"


def main() -> int:
    if not CURRENT_PROMPTS_PATH.exists():
        print(f"[FAIL] Missing prompts file: {CURRENT_PROMPTS_PATH}")
        return 1

    current_raw = CURRENT_PROMPTS_PATH.read_text(encoding="utf-8")
    if OVERRIDE_TOKEN in current_raw.lower():
        print("[OK] Prompt-Repeat-Override present; skipping repeat guard.")
        return 0

    current_fp, _ = prompt_set_fingerprint(current_raw)
    archive_paths = sorted(ROOT.glob(ARCHIVE_GLOB), key=archive_sort_key, reverse=True)

    if not archive_paths:
        print("[OK] No prompt archives found; nothing to compare.")
        print(f"[INFO] Prompt set fingerprint: {current_fp}")
        return 0

    archives_to_check = archive_paths[:ARCHIVE_DEPTH]
    for idx, archive in enumerate(archives_to_check):
        archive_raw = archive.read_text(encoding="utf-8")
        archive_fp, _ = prompt_set_fingerprint(archive_raw)
        if archive_fp == current_fp:
            label = ordinal_label(idx)
            rel_path = archive.relative_to(ROOT)
            print(f"[FAIL] Current prompts match the {label} archive: {rel_path}")
            print(f"[FAIL] Prompt set fingerprint: {current_fp}")
            print(f"[FAIL] Matching archive fingerprint: {archive_fp}")
            return 1

    print(f"[OK] Current prompts differ from the last {len(archives_to_check)} archive(s).")
    print(f"[INFO] Prompt set fingerprint: {current_fp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

