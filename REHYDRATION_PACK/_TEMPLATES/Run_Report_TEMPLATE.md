# Agent Run Report

## Metadata (required)
- **Run ID:** `RUN_<YYYYMMDD>_<HHMMZ>`
- **Agent:** A | B | C
- **Date (UTC):** YYYY-MM-DD
- **Worktree path:** `<pwd output>`
- **Branch:** `<branch-name>`
- **PR:** `#<number>` or none
- **PR merge strategy:** merge commit

## Objective + stop conditions
- **Objective:** <FILL_ME>
- **Stop conditions:** <FILL_ME>

## What changed (high-level)
- <ITEM_1>
- <ITEM_2>

## Diffstat (required)
```
<git diff --stat output>
```

## Files Changed (required)
- `<PATH_1>`: <description>
- `<PATH_2>`: <description>

## Commands Run (required)
```bash
# List all commands run with outputs
<COMMAND_1>
# output:
<OUTPUT_1>

<COMMAND_2>
# output:
<OUTPUT_2>
```

## Tests / Proof (required)
- **Tests run:** <FILL_ME>
- **Evidence location:** `qa/test_evidence/<RUN_ID>/` or <CI_LINK>
- **Results:** <pass/fail summary>

## PR Health Check (required for PRs)

### Bugbot Findings
- **Bugbot triggered:** yes/no (`@cursor review` or `bugbot run`)
- **Bugbot comment link:** <LINK_TO_PR_COMMENT> or "quota exceeded, fallback to manual review"
- **Findings summary:**
  - <FINDING_1>: <fixed | deferred | not applicable>
  - <FINDING_2>: <fixed | deferred | not applicable>
- **Action taken:** <description of fixes or deferral rationale>

### Codecov Findings
- **Codecov patch status:** pass/fail (<percentage>)
- **Codecov project status:** pass/fail (<percentage change>)
- **Coverage issues identified:**
  - <ISSUE_1>: <fixed | acceptable as-is | deferred>
  - <ISSUE_2>: <fixed | acceptable as-is | deferred>
- **Action taken:** <description of test additions or rationale>

### E2E Proof (if applicable)
- **E2E required:** yes/no (yes if changes touch outbound/automation)
- **E2E test run:** <workflow-name> or "not applicable"
- **E2E run URL:** <GITHUB_ACTIONS_RUN_URL> or "N/A"
- **E2E result:** pass/fail or "N/A"
- **Evidence:** <link to TEST_MATRIX.md section> or "N/A"

**Gate compliance:** All Bugbot/Codecov/E2E requirements addressed: yes/no

## Docs impact (summary)
- **Docs updated:** <list or none>
- **Docs to update next:** <list or none>

## Risks / edge cases considered
- <ITEM_1>
- <ITEM_2>

## Blockers / open questions
- <ITEM_1> or None

## Follow-ups (actionable)
- <ITEM_1> or None
