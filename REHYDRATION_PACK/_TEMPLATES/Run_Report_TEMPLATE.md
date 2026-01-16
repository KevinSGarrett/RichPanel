# Agent Run Report

## Metadata (required)
- **Run ID:** `RUN_<YYYYMMDD>_<HHMMZ>`
- **Agent:** A | B | C
- **Date (UTC):** YYYY-MM-DD
- **Worktree path:** `<pwd output>`
- **Branch:** `<branch-name>`
- **PR:** `#<number>` or none
- **PR merge strategy:** merge commit
- **Risk label:** `risk:R<#>-<level>` (R0-docs / R1-low / R2-medium / R3-high / R4-critical)
- **Risk justification:** <Why this risk level was chosen>

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

## Wait-for-green evidence (required)
- **Wait loop executed:** yes/no (sleep interval used)
- **Status timestamps:** <e.g., `2026-01-13T18:45Z` `gh pr checks <PR#>` output attached/redacted>
- **Check rollup proof:** <link to PR Checks tab or screenshot (redacted)>
- **GitHub Actions run:** <link to CI run that carried checks>
- **Codecov status:** <codecov/patch state + link/screenshot>
- **Bugbot status:** <comment link or "quota exhausted; manual review documented">

## PR Health Check (required for PRs)

### Risk and gate status
- **Risk label applied:** `risk:R<#>-<level>`
- **Required gates for this risk level:**
  - R0: CI optional, no Bugbot/Codecov/Claude/E2E
  - R1: CI required, Codecov advisory, Bugbot optional, Claude optional
  - R2: CI + Codecov patch + Bugbot + Claude required
  - R3: CI + Codecov (patch+project) + Bugbot (stale-rerun) + Claude (security, stale-rerun) + E2E if outbound
  - R4: All R3 gates + double-review + rollback plan
- **Gate lifecycle labels applied:** `gates:ready` → `gates:passed` (or `gates:stale` if re-run needed)

### CI validation (R1+ required)
- **CI validate status:** pass/fail
- **Local CI-equivalent run:** `python scripts/run_ci_checks.py --ci` → <PASS/FAIL>
- **CI run link:** <GITHUB_ACTIONS_RUN_URL>

### Bugbot Findings (R2+ required)
- **Bugbot required for risk level:** yes/no
- **Bugbot triggered:** yes/no (`@cursor review` or `bugbot run`)
- **Bugbot comment link:** <LINK_TO_PR_COMMENT> or "quota exceeded, fallback to manual review"
- **Findings summary:**
  - <FINDING_1>: <fixed | deferred | not applicable>
  - <FINDING_2>: <fixed | deferred | not applicable>
- **Action taken:** <description of fixes or deferral rationale>
- **Manual review (if quota exhausted):** <description of manual review process and findings>

### Codecov Findings (R2+ required)
- **Codecov required for risk level:** yes/no (patch for R2+, patch+project for R3+)
- **Codecov patch status:** pass/fail (<percentage>) or "N/A for R0/R1"
- **Codecov project status:** pass/fail (<percentage change>) or "N/A for R0/R1/R2"
- **Coverage issues identified:**
  - <ISSUE_1>: <fixed | acceptable as-is | deferred>
  - <ISSUE_2>: <fixed | acceptable as-is | deferred>
- **Action taken:** <description of test additions or rationale>

### Claude Review (R2+ required)
- **Claude required for risk level:** yes/no (required for R2/R3/R4, optional for R0/R1)
- **Claude triggered:** yes/no (method: GitHub comment | manual review | API call)
- **Claude review link:** <LINK_TO_REVIEW_OUTPUT> or "manual review documented below"
- **Claude verdict:** PASS | CONCERNS | FAIL | "manual review: no blocking issues"
- **Security prompt used (R3/R4):** yes/no
- **Findings:**
  - <FINDING_1>: <fixed | waived with justification>
  - <FINDING_2>: <fixed | waived with justification>
- **Action taken:** <description of fixes or waivers>
- **Waiver applied:** yes/no (if yes, `waiver:active` label applied and justification below)
- **Waiver justification (if applicable):** <reason for waiver + alternate evidence>

### E2E Proof (R3/R4 or outbound changes)
- **E2E required:** yes/no (yes if changes touch outbound/automation OR risk R3/R4)
- **E2E test run:** <workflow-name> or "not applicable"
- **E2E run URL:** <GITHUB_ACTIONS_RUN_URL> or "N/A"
- **E2E result:** pass/fail or "N/A"
- **Evidence:** <link to TEST_MATRIX.md section> or "N/A"

### Staleness check (R2+ required)
- **New commits after gates:** yes/no
- **If yes, gates re-run:** yes/no
- **Label transition:** `gates:ready` → `gates:stale` → `gates:passed` (if applicable)

**Gate compliance:** All required gates for risk level addressed and non-stale: yes/no

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
