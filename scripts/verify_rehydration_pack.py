#!/usr/bin/env python3
"""
verify_rehydration_pack.py

Mode-aware verifier for REHYDRATION_PACK invariants.

Design goals
- Standard library only (no PyYAML dependency).
- Deterministic: reads REHYDRATION_PACK/MODE.yaml and REHYDRATION_PACK/MANIFEST.yaml.
- Mode-aware strictness:
  - foundation mode: pack structure must exist; build artifacts are NOT required (warnings only)
  - build mode: strict enforcement of per-run artifacts

Usage
  python scripts/verify_rehydration_pack.py
  python scripts/verify_rehydration_pack.py --strict
  python scripts/verify_rehydration_pack.py --allow-partial   # build mode only

Exit code
  0 = ok
  1 = failure (missing required items for the active mode; or strict-mode failures)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
PACK = REPO_ROOT / "REHYDRATION_PACK"
MODE_FILE = PACK / "MODE.yaml"
MANIFEST_FILE = PACK / "MANIFEST.yaml"


# Baseline invariants: these MUST be declared in the manifest.
# (The manifest can include more, but must not omit these.)
BASELINE_MANIFEST_PATHS = {
    "00_START_HERE.md",
    "MANIFEST.yaml",
    "MODE.yaml",
    "LAST_REHYDRATED.md",
    "01_NORTH_STAR.md",
    "02_CURRENT_STATE.md",
    "03_ACTIVE_WORKSTREAMS.md",
    "04_DECISIONS_SNAPSHOT.md",
    "05_TASK_BOARD.md",
    "06_AGENT_ASSIGNMENTS.md",
    "POLICIES_SUMMARY.md",
    "PM_GUARDRAILS.md",
    "OPEN_QUESTIONS.md",
    "WAVE_SCHEDULE.md",
    "WAVE_SCHEDULE_FULL.md",
    "_TEMPLATES/",
}


VALID_MODES = {"foundation", "build"}


@dataclass
class ManifestEntry:
    path: str
    kind: str = "file"  # file|dir
    when: str = "common"  # common|foundation|build
    required: bool = True
    role: str = ""


@dataclass
class RunArtifactSpec:
    run_id_regex: str = r"^RUN_\d{8}_\d{4}Z$"
    agent_ids: List[str] = None  # type: ignore[assignment]
    required_files_per_agent: List[str] = None  # type: ignore[assignment]
    optional_files_per_agent: List[str] = None  # type: ignore[assignment]


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    return s


def parse_mode(mode_text: str) -> str:
    """
    Parse MODE.yaml without YAML libraries.
    Expects a simple line:
      mode: foundation|build
    """
    m = re.search(r"^\s*mode:\s*([A-Za-z0-9_-]+)\s*$", mode_text, flags=re.MULTILINE)
    if not m:
        raise ValueError("MODE.yaml missing required line: mode: <foundation|build>")
    return m.group(1).strip()


def parse_manifest(manifest_text: str) -> Tuple[List[ManifestEntry], RunArtifactSpec]:
    """
    Parse MANIFEST.yaml using a small YAML subset parser.

    Supported patterns:
    - 'paths:' section with entries like:
        - path: foo.md
          kind: file
          when: common
          required: true
          role: ...
    - 'run_artifacts:' section with simple scalars and lists.
    """
    entries: List[ManifestEntry] = []
    current: Optional[ManifestEntry] = None

    run_spec = RunArtifactSpec(
        run_id_regex=r"^RUN_\d{8}_\d{4}Z$",
        agent_ids=["A", "B", "C"],
        required_files_per_agent=["RUN_SUMMARY.md", "STRUCTURE_REPORT.md", "DOCS_IMPACT_MAP.md", "TEST_MATRIX.md"],
        optional_files_per_agent=["FIX_REPORT.md"],
    )

    section: Optional[str] = None
    list_target: Optional[str] = None

    lines = manifest_text.splitlines()
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if re.fullmatch(r"paths\s*:\s*", stripped):
            section = "paths"
            list_target = None
            continue

        if re.fullmatch(r"run_artifacts\s*:\s*", stripped):
            # flush last entry
            if current:
                entries.append(current)
                current = None
            section = "run_artifacts"
            list_target = None
            continue

        if section == "paths":
            m = re.match(r"^-+\s*path:\s*(.+?)\s*$", stripped)
            if m:
                if current:
                    entries.append(current)
                current = ManifestEntry(path=_strip_quotes(m.group(1)))
                list_target = None
                continue

            if current is None:
                # ignore until first "- path:"
                continue

            m = re.match(r"^kind:\s*(\w+)\s*$", stripped)
            if m:
                current.kind = m.group(1).strip()
                continue

            m = re.match(r"^when:\s*(\w+)\s*$", stripped)
            if m:
                current.when = m.group(1).strip()
                continue

            m = re.match(r"^required:\s*(true|false)\s*$", stripped, flags=re.IGNORECASE)
            if m:
                current.required = (m.group(1).lower() == "true")
                continue

            m = re.match(r"^role:\s*(.+?)\s*$", stripped)
            if m:
                current.role = _strip_quotes(m.group(1))
                continue

            continue

        if section == "run_artifacts":
            # list items
            if list_target and stripped.startswith("- "):
                item = stripped[2:].strip()
                if item:
                    if list_target == "required_files_per_agent":
                        run_spec.required_files_per_agent.append(item)
                    elif list_target == "optional_files_per_agent":
                        run_spec.optional_files_per_agent.append(item)
                continue

            # new key
            m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)\s*$", stripped)
            if not m:
                list_target = None
                continue

            key, value = m.group(1), m.group(2).strip()
            value = _strip_quotes(value)

            if key == "run_id_regex":
                if value:
                    run_spec.run_id_regex = value
                list_target = None
                continue

            if key == "agent_ids":
                if value:
                    # Accept YAML-ish inline list: ['A', 'B', 'C']
                    try:
                        parsed = ast.literal_eval(value)
                        if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                            run_spec.agent_ids = parsed
                    except Exception:
                        pass
                list_target = None
                continue

            if key == "required_files_per_agent":
                run_spec.required_files_per_agent = []
                list_target = "required_files_per_agent"
                continue

            if key == "optional_files_per_agent":
                run_spec.optional_files_per_agent = []
                list_target = "optional_files_per_agent"
                continue

            list_target = None
            continue

    if current:
        entries.append(current)

    return entries, run_spec


def applicable(entry: ManifestEntry, mode: str) -> bool:
    if entry.when == "common":
        return True
    if mode == "foundation" and entry.when == "foundation":
        return True
    if mode == "build" and entry.when == "build":
        return True
    return False


def check_manifest_completeness(entries: List[ManifestEntry]) -> List[str]:
    present = {e.path for e in entries}
    missing = sorted(p for p in BASELINE_MANIFEST_PATHS if p not in present)
    return missing


def check_paths(entries: List[ManifestEntry], mode: str, strict: bool) -> Tuple[List[str], List[str]]:
    """
    Returns (errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    for e in entries:
        if not applicable(e, mode):
            continue

        target = PACK / e.path
        is_dir_expected = e.kind.lower() == "dir" or e.path.endswith("/")

        if e.required:
            if not target.exists():
                errors.append(f"Missing required {e.kind} for mode '{mode}': {target}")
                continue
            if is_dir_expected and not target.is_dir():
                errors.append(f"Expected dir but found file: {target}")
            if (not is_dir_expected) and not target.is_file():
                errors.append(f"Expected file but found dir: {target}")
        else:
            if not target.exists():
                warnings.append(f"Missing optional {e.kind}: {target}")

    # In strict mode, promote warnings to errors
    if strict and warnings:
        errors.extend([f"(strict) {w}" for w in warnings])
        warnings = []

    return errors, warnings


def check_runs(run_spec: RunArtifactSpec, mode: str, strict: bool, allow_partial: bool) -> Tuple[List[str], List[str]]:
    """
    Validate RUNS structure.
    - build mode: strict by default, unless allow_partial is enabled.
    - foundation mode: warnings only (unless --strict).
    """
    errors: List[str] = []
    warnings: List[str] = []

    runs_dir = PACK / "RUNS"
    if not runs_dir.exists():
        if mode == "build":
            errors.append("RUNS/ is missing in build mode.")
        else:
            warnings.append("RUNS/ is missing (ok in foundation mode).")
        return errors, warnings

    run_id_re = re.compile(run_spec.run_id_regex)

    run_folders = [p for p in runs_dir.iterdir() if p.is_dir()]
    if not run_folders:
        if mode == "build":
            errors.append("RUNS/ is empty (no RUN_* folders found yet). In build mode, at least one RUN_* folder is required.")
        return (errors if not strict else errors + [f"(strict) {w}" for w in warnings], [] if strict else warnings)

    for run in sorted(run_folders, key=lambda p: p.name):
        if not run_id_re.match(run.name):
            msg = f"Run folder name does not match run_id_regex ({run_spec.run_id_regex}): {run.name}"
            (errors if (mode == "build" and not allow_partial) or strict else warnings).append(msg)

        # agent folders
        for aid in run_spec.agent_ids:
            agent_dir = run / aid
            if not agent_dir.exists():
                msg = f"{run.name}: missing agent folder {aid}/"
                if mode == "build" and not allow_partial:
                    errors.append(msg)
                else:
                    warnings.append(msg)
                continue

            for fn in run_spec.required_files_per_agent:
                f = agent_dir / fn
                if not f.exists():
                    msg = f"{run.name}/{aid}: missing required file {fn}"
                    if mode == "build" and not allow_partial:
                        errors.append(msg)
                    else:
                        warnings.append(msg)

            # optional files: no issue if missing

    if strict and warnings:
        errors.extend([f"(strict) {w}" for w in warnings])
        warnings = []

    return errors, warnings


def _count_non_empty_lines(text: str) -> int:
    return sum(1 for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip())


def _latest_run_dir(runs_dir: Path, run_id_re) -> Optional[Path]:
    candidates = [p for p in runs_dir.iterdir() if p.is_dir() and run_id_re.match(p.name)]
    if not candidates:
        return None
    # Run IDs are lexicographically sortable due to RUN_YYYYMMDD_HHMMZ format.
    return sorted(candidates, key=lambda p: p.name)[-1]


def check_latest_run_populated(
    run_spec: RunArtifactSpec, mode: str, strict: bool, allow_partial: bool
) -> Tuple[List[str], List[str]]:
    """
    Enforce that the latest run is fully reported (build mode).

    Requirements (MODE=build):
    - REHYDRATION_PACK/RUNS/ contains at least one RUN_* directory
    - latest run contains A/, B/, C/
    - each agent folder contains populated required docs:
        - RUN_REPORT.md (>= 25 non-empty lines)
        - RUN_SUMMARY.md (>= 10 non-empty lines)
        - STRUCTURE_REPORT.md (>= 10 non-empty lines)
        - DOCS_IMPACT_MAP.md (>= 10 non-empty lines)
        - TEST_MATRIX.md (>= 10 non-empty lines)
    """
    errors: List[str] = []
    warnings: List[str] = []

    if mode != "build":
        return errors, warnings

    runs_dir = PACK / "RUNS"
    if not runs_dir.exists():
        errors.append("RUNS/ is missing in build mode.")
        return errors, warnings

    run_id_re = re.compile(run_spec.run_id_regex)
    latest = _latest_run_dir(runs_dir, run_id_re)
    if latest is None:
        errors.append(f"RUNS/ must contain at least one run folder matching: {run_spec.run_id_regex}")
        return errors, warnings

    required_with_min_lines = {
        "RUN_REPORT.md": 25,
        "RUN_SUMMARY.md": 10,
        "STRUCTURE_REPORT.md": 10,
        "DOCS_IMPACT_MAP.md": 10,
        "TEST_MATRIX.md": 10,
    }

    for aid in run_spec.agent_ids:
        agent_dir = latest / aid
        if not agent_dir.exists():
            msg = f"{latest.name}: missing agent folder {aid}/ (latest run requirement)"
            (warnings if allow_partial else errors).append(msg)
            continue
        if not agent_dir.is_dir():
            msg = f"{latest.name}: expected {aid}/ to be a directory (latest run requirement)"
            (warnings if allow_partial else errors).append(msg)
            continue

        for fn, min_lines in required_with_min_lines.items():
            fpath = agent_dir / fn
            if not fpath.exists():
                msg = f"{latest.name}/{aid}: missing required file {fn} (latest run requirement)"
                (warnings if allow_partial else errors).append(msg)
                continue
            if not fpath.is_file():
                msg = f"{latest.name}/{aid}: expected file but found directory: {fn} (latest run requirement)"
                (warnings if allow_partial else errors).append(msg)
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                msg = f"{latest.name}/{aid}: could not read {fn}: {e}"
                (warnings if allow_partial else errors).append(msg)
                continue

            non_empty = _count_non_empty_lines(content)
            if non_empty < min_lines:
                msg = (
                    f"{latest.name}/{aid}: {fn} not populated: "
                    f"{non_empty} non-empty lines (min {min_lines})"
                )
                (warnings if allow_partial else errors).append(msg)

    if strict and warnings:
        errors.extend([f"(strict) {w}" for w in warnings])
        warnings = []

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures (useful for CI).")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Build mode: allow missing agent folders/files as warnings (use only for in-progress runs).",
    )
    args = parser.parse_args()

    if not PACK.exists():
        print("[FAIL] REHYDRATION_PACK/ folder is missing")
        return 1
    if not MODE_FILE.exists():
        print("[FAIL] REHYDRATION_PACK/MODE.yaml is missing")
        return 1
    if not MANIFEST_FILE.exists():
        print("[FAIL] REHYDRATION_PACK/MANIFEST.yaml is missing")
        return 1

    # Parse mode
    mode_text = MODE_FILE.read_text(encoding="utf-8", errors="replace")
    try:
        mode = parse_mode(mode_text)
    except Exception as e:
        print(f"[FAIL] Could not parse MODE.yaml: {e}")
        return 1

    if mode not in VALID_MODES:
        print(f"[FAIL] Unknown mode '{mode}'. Valid modes: {sorted(VALID_MODES)}")
        return 1

    # Parse manifest
    manifest_text = MANIFEST_FILE.read_text(encoding="utf-8", errors="replace")
    entries, run_spec = parse_manifest(manifest_text)

    if not entries:
        print("[FAIL] Could not parse any entries from MANIFEST.yaml (expected 'paths:' section)")
        return 1

    # Manifest must declare the baseline invariants
    missing_from_manifest = check_manifest_completeness(entries)
    if missing_from_manifest:
        print("[FAIL] MANIFEST.yaml is missing baseline required path declarations:")
        for p in missing_from_manifest:
            print(f"  - {p}")
        return 1

    # Validate pack paths for the active mode
    strict = args.strict
    allow_partial = args.allow_partial

    errors, warnings = check_paths(entries, mode=mode, strict=strict)
    run_errors, run_warnings = check_runs(run_spec, mode=mode, strict=strict, allow_partial=allow_partial)

    errors.extend(run_errors)
    warnings.extend(run_warnings)

    latest_errors, latest_warnings = check_latest_run_populated(
        run_spec, mode=mode, strict=strict, allow_partial=allow_partial
    )
    errors.extend(latest_errors)
    warnings.extend(latest_warnings)

    if warnings:
        print("[WARN] Issues found:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("[FAIL] REHYDRATION_PACK validation failed:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"[OK] REHYDRATION_PACK validated (mode={mode}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
