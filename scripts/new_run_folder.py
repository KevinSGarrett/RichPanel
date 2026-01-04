#!/usr/bin/env python3
"""
new_run_folder.py

Create a build-mode RUN folder skeleton under:
  REHYDRATION_PACK/RUNS/<RUN_ID>/{A,B,C}/

It copies the required per-agent templates so Cursor agents can fill them in.

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
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

RUN_ID_PATTERN = r"^RUN_\d{8}_\d{4}Z$"
RUN_ID_RE = re.compile(RUN_ID_PATTERN)

TEMPLATE_MAP = {
    "Cursor_Run_Summary_TEMPLATE.md": "RUN_SUMMARY.md",
    "Git_Run_Plan_TEMPLATE.md": "GIT_RUN_PLAN.md",
    "Structure_Report_TEMPLATE.md": "STRUCTURE_REPORT.md",
    "Docs_Impact_Map_TEMPLATE.md": "DOCS_IMPACT_MAP.md",
    "Test_Matrix_TEMPLATE.md": "TEST_MATRIX.md",
    # Optional (still copied so agents can use it if needed):
    "Fix_Report_TEMPLATE.md": "FIX_REPORT.md",
}

AGENT_IDS = ["A", "B", "C"]


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
    templates_dir = pack / "_TEMPLATES"

    if not templates_dir.exists():
        print(f"ERROR: templates dir missing: {templates_dir}", file=sys.stderr)
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

    # Copy templates into each agent folder
    for aid in AGENT_IDS:
        agent_dir = run_root / aid
        for src_name, dst_name in TEMPLATE_MAP.items():
            src = templates_dir / src_name
            if not src.exists():
                print(f"WARN: template missing: {src}", file=sys.stderr)
                continue
            shutil.copyfile(src, agent_dir / dst_name)

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
        "- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)\n",
        encoding="utf-8",
    )

    print(f"OK: created {run_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
