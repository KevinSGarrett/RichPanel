# Agent Run Report (Template)

> High-detail, durable run history artifact. This file is **required** per agent per run.

## Metadata (required)
- **Run ID:** `RUN_<YYYYMMDD>_<HHMMZ>`
- **Agent:** A | B | C
- **Date (UTC):** YYYY-MM-DD
- **Worktree path:** <ABSOLUTE_PATH>
- **Branch:** <branch>
- **PR:** <none | link>
- **PR merge strategy:** merge commit (required)

## Objective + stop conditions
- **Objective:** <FILL_ME>
- **Stop conditions:** <FILL_ME>

## What changed (high-level)
- <CHANGE_1>
- <CHANGE_2>

## Diffstat (required)
Paste `git diff --stat` (or PR diffstat) here:

<PASTE_DIFFSTAT>

## Files touched (required)
List key files touched (grouped by area):
- <PATH_1> - <why>
- <PATH_2> - <why>

## Tests run (required)
List commands + results:
- <COMMAND_1> - pass/fail - evidence: <PATH_OR_LINK>
- <COMMAND_2> - pass/fail - evidence: <PATH_OR_LINK>

## CI / validate evidence (required)
Paste output snippet proving you ran:
`AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 python scripts/run_ci_checks.py`

<PASTE_OUTPUT_SNIPPET>

## Docs impact (summary)
- **Docs updated:** <NONE or list>
- **Docs to update next:** <NONE or list>

## Risks / edge cases considered
- <RISK_1 + mitigation>
- <RISK_2 + mitigation>

## Blockers / open questions
- <NONE or list>

## Follow-ups (actionable)
- [ ] <FOLLOW_UP_1>
- [ ] <FOLLOW_UP_2>

<!-- End of template -->
