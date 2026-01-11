#!/usr/bin/env python3
"""
new_run_folder.py

Create a build-mode RUN folder skeleton under:
  REHYDRATION_PACK/RUNS/<RUN_ID>/{A,B,C}/

It copies the required per-agent templates so Cursor agents can fill them in.
It also snapshots the current prompt set to enable dedup checks.

Usage:
  python scripts/new_run_folder.py RUN_20251229_2315Z
  python scripts/new_run_folder.py --now
  python scripts/new_run_folder.py --now --force

Notes:
- RUN_ID must match: ^RUN_\\d{8}_\\d{4}Z$
- Standard library only.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from typing import Optional

RUN_ID_PATTERN = r"^RUN_\d{8}_\d{4}Z$"
RUN_ID_RE = re.compile(RUN_ID_PATTERN)

TEMPLATE_MAP = {
    "Agent_Run_Report_TEMPLATE.md": "RUN_REPORT.md",
    "Cursor_Run_Summary_TEMPLATE.md": "RUN_SUMMARY.md",
    "Git_Run_Plan_TEMPLATE.md": "GIT_RUN_PLAN.md",
    "Structure_Report_TEMPLATE.md": "STRUCTURE_REPORT.md",
    "Docs_Impact_Map_TEMPLATE.md": "DOCS_IMPACT_MAP.md",
    "Test_Matrix_TEMPLATE.md": "TEST_MATRIX.md",
    # Optional (still copied so agents can use it if needed):
    "Fix_Report_TEMPLATE.md": "FIX_REPORT.md",
}

AGENT_IDS = ["A", "B", "C"]
PROMPTS_SOURCE = "06_AGENT_ASSIGNMENTS.md"
PROMPTS_ARCHIVE_NAME = "AGENT_PROMPTS_ARCHIVE.md"


def resolve_template(templates_dirs: list[Path], template_name: str) -> Optional[Path]:
    for d in templates_dirs:
        p = d / template_name
        if p.exists():
            return p
    return None


def utc_run_id_now() -> str:
    now = datetime.now(timezone.utc)
    return f"RUN_{now:%Y%m%d}_{now:%H%M}Z"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id", nargs="?", help="RUN_<YYYYMMDD>_<HHMMZ> (UTC)")
    parser.add_argument("--now", action="store_true", help="Generate RUN_ID from current UTC time")
    parser.add_argument("--force", action="store_true", help="Overwrite existing run folder if it exists")
    args = parser.parse_args()

    if args.now:
        run_id = utc_run_id_now()
    else:
        run_id = args.run_id

    if not run_id:
        print("ERROR: provide RUN_ID or use --now", file=sys.stderr)
        return 2

    if not RUN_ID_RE.match(run_id):
        print(f"ERROR: invalid RUN_ID '{run_id}'. Must match {RUN_ID_RE.pattern}", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[1]
    pack = repo_root / "REHYDRATION_PACK"
    runs_dir = pack / "RUNS"
    templates_dirs = [pack / "TEMPLATES", pack / "_TEMPLATES"]
    templates_dirs = [d for d in templates_dirs if d.exists()]
    if not templates_dirs:
        print(
            "ERROR: templates dir missing (expected REHYDRATION_PACK/TEMPLATES or REHYDRATION_PACK/_TEMPLATES)",
            file=sys.stderr,
        )
        return 2

    run_root = runs_dir / run_id

    if run_root.exists():
        if not args.force:
            print(f"ERROR: run folder already exists: {run_root} (use --force to overwrite)", file=sys.stderr)
            return 2
        shutil.rmtree(run_root)

    # Create run root + agent folders
    for aid in AGENT_IDS:
        (run_root / aid).mkdir(parents=True, exist_ok=True)

    def find_template(src_name: str) -> Optional[Path]:
        for d in templates_dirs:
            candidate = d / src_name
            if candidate.exists():
                return candidate
        return None

    # Copy templates into each agent folder
    for aid in AGENT_IDS:
        agent_dir = run_root / aid
        for src_name, dst_name in TEMPLATE_MAP.items():
            src = resolve_template(templates_dirs, src_name)
            if not src:
                print(
                    f"WARN: template missing in {', '.join(str(d) for d in templates_dirs)}: {src_name}",
                    file=sys.stderr,
                )
                continue
            shutil.copyfile(src, agent_dir / dst_name)

    # Snapshot current prompts for dedup checks (C only)
    prompts_src = pack / PROMPTS_SOURCE
    prompts_dst = run_root / "C" / PROMPTS_ARCHIVE_NAME
    try:
        prompts_text = prompts_src.read_text(encoding="utf-8", errors="replace") if prompts_src.exists() else ""
    except Exception as e:
        prompts_text = f"[ERROR] Could not read {prompts_src}: {e}\n"
    prompts_dst.write_text(
        "# Archive — snapshot of `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md`\n"
        "\n"
        f"Archived at run creation for `{run_id}`.\n"
        "\n"
        "---\n"
        "\n"
        f"{prompts_text.rstrip()}\n",
        encoding="utf-8",
    )

    # Create a simple run meta file at the run root
    meta = run_root / "RUN_META.md"
    meta.write_text(
        "# Run Meta\n\n"
        f"- RUN_ID: `{run_id}`\n"
        "- Mode: build\n"
        "- Objective: <FILL_ME>\n"
        "- Stop conditions: <FILL_ME>\n\n"
        "## Notes\n"
        "- Each agent writes to its folder: A/, B/, C/\n"
        "- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)\n"
        "- Latest-run reports must include: RUN_REPORT.md, RUN_SUMMARY.md, STRUCTURE_REPORT.md, DOCS_IMPACT_MAP.md, TEST_MATRIX.md\n"
        "- Prompt archive snapshot is created at: C/AGENT_PROMPTS_ARCHIVE.md\n",
        encoding="utf-8",
    )

    print(f"OK: created {run_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
