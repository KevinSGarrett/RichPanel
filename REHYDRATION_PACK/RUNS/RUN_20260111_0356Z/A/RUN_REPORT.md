# Run Report
**Run ID:** `RUN_<YYYYMMDD>_<HHMMZ>`  
**Agent:** A | B | C  
**Date:** YYYY-MM-DD  
**Worktree path:** <ABSOLUTE_PATH_TO_WORKTREE>  
**Branch:** <run/<SHORT>_<YYYYMMDD> or run/<RUN_ID>_...>  
**PR:** <none | link>

## What shipped (TL;DR)
- <BULLET_1>
- <BULLET_2>
- <BULLET_3>

## Diffstat (required)
- Command: `git diff --stat <base>...HEAD`
- Output:
  - <PASTE_DIFFSTAT_HERE>

## Files touched (required)
- **Added**
  - <PATH_1>
- **Modified**
  - <PATH_1>
- **Deleted**
  - <NONE or list>

## Commands run (required)
- <COMMAND_1>
- <COMMAND_2>
- <COMMAND_3>

## Tests run (required)
- <TEST_COMMAND_1> — pass/fail
- <TEST_COMMAND_2> — pass/fail
- <TEST_COMMAND_3> — pass/fail

## CI / validation evidence (required)
- **Local CI-equivalent**: `python scripts/run_ci_checks.py`
  - Result: pass/fail
  - Evidence: <PASTE_OUTPUT_OR_POINT_TO_FILE>

## PR / merge status
- PR link: <LINK>
- Merge method: merge commit
- Auto-merge enabled: yes/no
- Branch deleted: yes/no

## Blockers
- <NONE or list>

## Risks / gotchas
- <NONE or list>

## Follow-ups
- <NONE or list>

## Notes
- <FILL_ME>

