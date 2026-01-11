#!/usr/bin/env python3
"""
verify_plan_sync.py

Lightweight validation for docs navigation + generated indexes.

Design goals
- Standard library only
- Fast enough to run locally and in CI
- Clear failures (good for AI agents and humans)

Checks
DOCS
1) Required docs navigation files exist.
2) Required docs generated index files exist and are valid JSON.
3) Every relative link in docs/INDEX.md resolves to an existing file.
4) docs/_generated/doc_registry.json is consistent with the markdown files under docs/:
   - each registry entry path exists
   - registry count matches discovered *.md count
5) docs/_generated/heading_index.json references valid doc paths.
6) docs/_generated/doc_outline.json references valid doc paths.

REFERENCE
7) reference/_generated/reference_registry.json exists and parses as JSON.
8) Every reference registry entry path exists.
9) Reference registry count matches discovered reference files (excluding reference/_generated).

Usage
  python scripts/verify_plan_sync.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

DOCS = REPO_ROOT / "docs"
DOCS_INDEX = DOCS / "INDEX.md"
DOCS_GENERATED = DOCS / "_generated"

REF = REPO_ROOT / "reference"
REF_GENERATED = REF / "_generated"
REF_REGISTRY = REF_GENERATED / "reference_registry.json"

REQUIRED_DOC_FILES = [
    DOCS / "INDEX.md",
    DOCS / "CODEMAP.md",
    DOCS / "ROADMAP.md",
    DOCS / "REGISTRY.md",
]

REQUIRED_DOC_GENERATED_FILES = [
    DOCS_GENERATED / "doc_registry.json",
    DOCS_GENERATED / "doc_outline.json",
    DOCS_GENERATED / "heading_index.json",
]
REQUIRED_REPO_FILES = [
    # Repo-level living docs and templates
    REPO_ROOT / "CHANGELOG.md",
    REPO_ROOT / "config" / ".env.example",
    REPO_ROOT / "qa" / "test_evidence" / "README.md",
    DOCS / "08_Engineering" / "Branch_Protection_and_Merge_Settings.md",
    # Canonical living docs (system understanding)
    DOCS / "02_System_Architecture" / "System_Overview.md",
    DOCS / "02_System_Architecture" / "System_Matrix.md",
    # API surface
    DOCS / "04_API_Contracts" / "API_Reference.md",
    DOCS / "04_API_Contracts" / "openapi.yaml",
    # Config/env documentation
    DOCS / "09_Deployment_Operations" / "Environment_Config.md",
    # Logs and progress
    DOCS / "00_Project_Admin" / "Decision_Log.md",
    DOCS / "00_Project_Admin" / "Issue_Log.md",
    DOCS / "00_Project_Admin" / "Progress_Log.md",
    DOCS / "00_Project_Admin" / "To_Do" / "MASTER_CHECKLIST.md",
    # Testing evidence
    DOCS / "08_Testing_Quality" / "Test_Evidence_Log.md",
    # User documentation
    DOCS / "07_User_Documentation" / "User_Manual.md",
    # Agent ops / living docs definition
    DOCS / "98_Agent_Ops" / "Living_Documentation_Set.md",
    # Plan checklist extraction outputs (generated)
    DOCS / "00_Project_Admin" / "To_Do" / "_generated" / "plan_checklist.json",
    DOCS / "00_Project_Admin" / "To_Do" / "_generated" / "PLAN_CHECKLIST_EXTRACTED.md",
    DOCS / "00_Project_Admin" / "To_Do" / "_generated" / "PLAN_CHECKLIST_SUMMARY.md",
    # Foundation/build transition docs
    DOCS / "00_Project_Admin" / "Build_Mode_Activation_Checklist.md",
    DOCS / "00_Project_Admin" / "Legacy_Folder_Redirects.md",
    DOCS / "98_Agent_Ops" / "Placeholder_and_Draft_Standards.md",
    # Automation scripts present
    REPO_ROOT / "scripts" / "regen_plan_checklist.py",
    REPO_ROOT / "scripts" / "verify_doc_hygiene.py",
]


def relpath(p: Path) -> str:
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except Exception:
        return p.as_posix()


def parse_md_links(text: str) -> Iterable[str]:
    """Extract markdown link targets like [x](target)."""
    for m in re.finditer(r"\]\(([^)]+)\)", text):
        target = (m.group(1) or "").strip()
        if not target:
            continue
        if re.match(r"^(https?:)?//", target) or target.startswith("mailto:"):
            continue
        target = target.split("#", 1)[0].split("?", 1)[0]
        if target.startswith("./"):
            target = target[2:]
        if not target:
            continue
        yield target


def load_json(path: Path) -> Tuple[object, str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as e:
        return None, str(e)


def fail_list(title: str, items: List[str], limit: int = 30) -> List[str]:
    out = [title]
    for it in items[:limit]:
        out.append(f"  - {it}")
    if len(items) > limit:
        out.append(f"  - ... ({len(items) - limit} more)")
    return out


def discover_docs() -> List[Path]:
    """Discover docs/**/*.md excluding docs/_generated."""
    files: List[Path] = []
    for p in DOCS.rglob("*.md"):
        rel = p.relative_to(DOCS)
        # Only exclude the top-level docs/_generated folder (machine indexes).
        if rel.parts and rel.parts[0] == "_generated":
            continue
        if p.is_file():
            files.append(p)
    return sorted(files)


def discover_reference_files() -> List[Path]:
    """Discover reference/**/* excluding reference/_generated."""
    files: List[Path] = []
    if not REF.exists():
        return files
    for p in REF.rglob("*"):
        if "_generated" in p.parts:
            continue
        if p.is_file():
            files.append(p)
    return sorted(files)


def main() -> int:
    failures: List[str] = []

    # --- Docs required files ---
    missing_docs = [relpath(p) for p in REQUIRED_DOC_FILES if not p.exists()]
    if missing_docs:
        failures += fail_list("Missing required docs files:", missing_docs)

    missing_generated = [
        relpath(p) for p in REQUIRED_DOC_GENERATED_FILES if not p.exists()
    ]
    if missing_generated:
        failures += fail_list(
            "Missing required docs generated files:", missing_generated
        )

    missing_repo = [relpath(p) for p in REQUIRED_REPO_FILES if not p.exists()]
    if missing_repo:
        failures += fail_list("Missing required repo living docs/files:", missing_repo)

    # Validate generated JSON parses
    for p in REQUIRED_DOC_GENERATED_FILES:
        if not p.exists():
            continue
        obj, err = load_json(p)
        if err:
            failures.append(f"Invalid JSON: {relpath(p)} — {err}")

    # Validate docs index links
    if DOCS_INDEX.exists():
        index_text = DOCS_INDEX.read_text(encoding="utf-8", errors="ignore")
        bad_links = []
        for target in parse_md_links(index_text):
            resolved = (DOCS / target).resolve()
            if not resolved.exists():
                bad_links.append(f"{target} -> missing")
        if bad_links:
            failures += fail_list("Broken links in docs/INDEX.md:", bad_links)

    # Validate doc registry consistency
    registry_path = DOCS_GENERATED / "doc_registry.json"
    if registry_path.exists():
        obj, err = load_json(registry_path)
        if err:
            failures.append(f"Invalid JSON: {relpath(registry_path)} — {err}")
        else:
            if not isinstance(obj, list):
                failures.append("docs/_generated/doc_registry.json must be a JSON list")
            else:
                records = obj
                discovered = discover_docs()

                # Compare registry vs discovered docs (excluding docs/_generated).
                registry_paths = []
                for r in records:
                    if not isinstance(r, dict):
                        continue
                    rel = r.get("path")
                    if isinstance(rel, str):
                        registry_paths.append(rel)

                discovered_paths = [str(p.relative_to(DOCS)).replace("\\", "/") for p in discovered]

                missing_in_registry = sorted(
                    set(discovered_paths) - set(registry_paths)
                )
                extra_in_registry = sorted(set(registry_paths) - set(discovered_paths))

                if missing_in_registry or extra_in_registry:
                    failures.append(
                        "docs registry count mismatch: "
                        f"registry={len(registry_paths)} discovered={len(discovered_paths)}"
                    )
                    if missing_in_registry:
                        failures += fail_list(
                            "Docs missing from docs/_generated/doc_registry.json:",
                            missing_in_registry,
                        )
                    if extra_in_registry:
                        failures += fail_list(
                            "Extra docs in docs/_generated/doc_registry.json not found on disk:",
                            extra_in_registry,
                        )

                missing_paths = []
                for r in records:
                    if not isinstance(r, dict):
                        continue
                    rel = r.get("path")
                    if not isinstance(rel, str):
                        continue
                    p = DOCS / rel
                    if not p.exists():
                        missing_paths.append(rel)
                if missing_paths:
                    failures += fail_list(
                        "Docs registry contains missing paths:", missing_paths
                    )

    # Validate doc outline consistency
    outline_path = DOCS_GENERATED / "doc_outline.json"
    if outline_path.exists():
        obj, err = load_json(outline_path)
        if err:
            failures.append(f"Invalid JSON: {relpath(outline_path)} — {err}")
        else:
            if not isinstance(obj, list):
                failures.append("docs/_generated/doc_outline.json must be a JSON list")
            else:
                missing_outline_docs = []
                for entry in obj:
                    if not isinstance(entry, dict):
                        continue
                    rel = entry.get("path")
                    if isinstance(rel, str):
                        p = DOCS / rel
                        if not p.exists():
                            missing_outline_docs.append(rel)
                if missing_outline_docs:
                    failures += fail_list(
                        "Doc outline references missing doc paths:",
                        missing_outline_docs,
                    )

    # Validate heading index references
    heading_index_path = DOCS_GENERATED / "heading_index.json"
    if heading_index_path.exists():
        obj, err = load_json(heading_index_path)
        if err:
            failures.append(f"Invalid JSON: {relpath(heading_index_path)} — {err}")
        else:
            if not isinstance(obj, dict):
                failures.append(
                    "docs/_generated/heading_index.json must be a JSON object"
                )
            else:
                missing_heading_docs = []
                for heading, occ in obj.items():
                    if not isinstance(occ, list):
                        continue
                    for rec in occ:
                        if not isinstance(rec, dict):
                            continue
                        rel = rec.get("path")
                        if isinstance(rel, str):
                            p = DOCS / rel
                            if not p.exists():
                                missing_heading_docs.append(rel)
                if missing_heading_docs:
                    failures += fail_list(
                        "Heading index references missing doc paths:",
                        missing_heading_docs,
                    )

    # --- Reference checks ---
    if not REF_REGISTRY.exists():
        failures.append(f"Missing reference registry: {relpath(REF_REGISTRY)}")
    else:
        obj, err = load_json(REF_REGISTRY)
        if err:
            failures.append(f"Invalid JSON: {relpath(REF_REGISTRY)} — {err}")
        else:
            if not isinstance(obj, dict) or not isinstance(obj.get("records"), list):
                failures.append(
                    "reference/_generated/reference_registry.json must be an object with a 'records' list"
                )
            else:
                records = obj.get("records")  # type: ignore
                missing_ref_paths = []
                for r in records:
                    if not isinstance(r, dict):
                        continue
                    rel = r.get("path")
                    if not isinstance(rel, str):
                        continue
                    p = REPO_ROOT / rel
                    if not p.exists():
                        missing_ref_paths.append(rel)
                if missing_ref_paths:
                    failures += fail_list(
                        "Reference registry contains missing paths:", missing_ref_paths
                    )

                discovered = discover_reference_files()
                if len(records) != len(discovered):
                    failures.append(
                        f"reference registry count mismatch: registry={len(records)} discovered={len(discovered)}"
                    )

    # --- Final ---
    if failures:
        print("FAIL\n" + "\n".join(failures))
        return 1

    print("OK: docs + reference validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
