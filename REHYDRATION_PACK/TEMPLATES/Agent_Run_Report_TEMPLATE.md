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

## PR Health Check (required before merge)

### CI Status
- **CI run URL**: <GITHUB_ACTIONS_RUN_URL>
- **CI result**: pass/fail
- **Failures fixed**: <yes/no/N/A — list fixes if applicable>

### Codecov Status
- **Patch coverage**: <PERCENTAGE>% (target: ≥50%)
- **Project coverage**: <PERCENTAGE>% change (threshold: ≤5% drop)
- **Codecov URL**: <CODECOV_PR_URL or "pending">
- **Coverage gaps addressed**: <yes/no/N/A — explain if gaps remain>

### Bugbot Review
- **Bugbot triggered**: <yes/no>
- **Bugbot review URL**: <PR_COMMENT_URL or "quota exhausted">
- **Findings count**: <NUMBER>
- **Findings addressed**: <yes/N/A — list key findings + resolutions>
- **Manual review (if Bugbot unavailable)**: <REVIEWER_NAME + summary or N/A>

### E2E Testing (if automation/outbound touched)
- **E2E tests required**: <yes/no>
- **Dev E2E run URL**: <GITHUB_ACTIONS_RUN_URL or N/A>
- **Staging E2E run URL**: <GITHUB_ACTIONS_RUN_URL or N/A>
- **Prod E2E run URL**: <GITHUB_ACTIONS_RUN_URL or N/A>
- **E2E results**: <all pass / failures documented / N/A>
- **Evidence location**: `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/TEST_MATRIX.md`

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

