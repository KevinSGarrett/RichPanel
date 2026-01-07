#!/usr/bin/env python3
"""
Report checklist progress from MASTER_CHECKLIST.md.

This is a report-only script (does NOT fail CI). It parses the master checklist
and prints counts by status to help track epic-level progress.

Usage:
    python scripts/report_checklist_progress.py
    python scripts/report_checklist_progress.py --json

Exit code: Always 0 (report-only; does not block CI)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Force UTF-8 output on Windows to handle Unicode characters
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")


def parse_master_checklist(checklist_path: Path) -> Tuple[List[Dict[str, str]], str]:
    """Parse MASTER_CHECKLIST.md and extract epic rows + last verified date."""
    if not checklist_path.exists():
        return [], "unknown"

    content = checklist_path.read_text(encoding="utf-8")
    
    # Extract last verified date
    last_verified = "unknown"
    verified_match = re.search(r"Last verified:\s*(.+)", content)
    if verified_match:
        last_verified = verified_match.group(1).strip()

    # Extract table rows (skip header and separator rows)
    rows = []
    in_table = False
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Detect table start
        if line.startswith("| ID |"):
            in_table = True
            continue
        
        # Skip separator row
        if in_table and line.startswith("|---"):
            continue
        
        # Parse data rows
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            # parts[0] is empty (before first |), parts[-1] is empty (after last |)
            if len(parts) >= 6:
                epic_id = parts[1]
                epic_name = parts[2]
                status = parts[3]
                owner = parts[4]
                references = parts[5]
                
                # Stop at Notes or end of table
                if epic_id.startswith("Notes") or epic_id == "":
                    break
                
                rows.append({
                    "id": epic_id,
                    "epic": epic_name,
                    "status": status,
                    "owner": owner,
                    "references": references,
                })
    
    return rows, last_verified


def classify_status(status: str) -> str:
    """Classify status into normalized categories."""
    status_lower = status.lower()
    
    if "✅" in status or "done" in status_lower:
        return "done"
    elif "🚧" in status or "in progress" in status_lower:
        return "in_progress"
    elif "⏳" in status or "pending" in status_lower:
        return "pending"
    elif "not started" in status_lower:
        return "not_started"
    else:
        return "unknown"


def count_by_status(rows: List[Dict[str, str]]) -> Dict[str, int]:
    """Count epics by normalized status."""
    counts: Dict[str, int] = {
        "done": 0,
        "in_progress": 0,
        "pending": 0,
        "not_started": 0,
        "unknown": 0,
    }
    
    for row in rows:
        category = classify_status(row["status"])
        counts[category] += 1
    
    return counts


def print_report(rows: List[Dict[str, str]], last_verified: str, as_json: bool = False) -> None:
    """Print the progress report."""
    counts = count_by_status(rows)
    total = len(rows)
    
    if as_json:
        output = {
            "last_verified": last_verified,
            "total_epics": total,
            "status_counts": counts,
            "epics": rows,
        }
        print(json.dumps(output, indent=2))
    else:
        # Use ASCII-safe output for Windows compatibility
        print("=" * 60)
        print("MASTER CHECKLIST Progress Report")
        print("=" * 60)
        print(f"Last verified: {last_verified}")
        print(f"Total epics:   {total}")
        print()
        print("Status breakdown:")
        print(f"  [DONE]        {counts['done']:2d} ({counts['done']/total*100:5.1f}%)" if total > 0 else "  [DONE]        0")
        print(f"  [IN PROGRESS] {counts['in_progress']:2d} ({counts['in_progress']/total*100:5.1f}%)" if total > 0 else "  [IN PROGRESS] 0")
        print(f"  [PENDING]     {counts['pending']:2d} ({counts['pending']/total*100:5.1f}%)" if total > 0 else "  [PENDING]     0")
        print(f"  [NOT STARTED] {counts['not_started']:2d} ({counts['not_started']/total*100:5.1f}%)" if total > 0 else "  [NOT STARTED] 0")
        if counts['unknown'] > 0:
            print(f"  [UNKNOWN]     {counts['unknown']:2d} ({counts['unknown']/total*100:5.1f}%)")
        print("=" * 60)
        print()
        print("Epic details:")
        for row in rows:
            status_label = {
                "done": "[DONE]       ",
                "in_progress": "[IN PROGRESS]",
                "pending": "[PENDING]    ",
                "not_started": "[NOT STARTED]",
                "unknown": "[UNKNOWN]    ",
            }.get(classify_status(row["status"]), "             ")
            print(f"  {status_label} {row['id']:8s} {row['epic'][:60]}")
        print("=" * 60)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Report checklist progress (report-only; never fails)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of human-readable format",
    )
    parser.add_argument(
        "--checklist",
        type=Path,
        default=Path("docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md"),
        help="Path to MASTER_CHECKLIST.md (default: docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md)",
    )
    args = parser.parse_args()

    rows, last_verified = parse_master_checklist(args.checklist)
    
    if not rows:
        print(f"Warning: No epics found in {args.checklist}", file=sys.stderr)
        return 0
    
    print_report(rows, last_verified, as_json=args.json)
    
    # Always exit 0 (report-only)
    return 0


if __name__ == "__main__":
    sys.exit(main())

