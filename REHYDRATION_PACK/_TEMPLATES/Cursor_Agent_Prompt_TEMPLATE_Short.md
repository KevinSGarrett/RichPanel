# Cursor Agent Prompt (Short)

**Run ID:** `RUN_<YYYYMMDD>_<HHMMZ>`  
**Task IDs:** `<TASK-###, ...>`  
**Model:** `<model-name>` (MAX: ON | OFF)  
**Cycle:** 1× | 2× | 3× | 4×

## Context
- Goal: <FILL_ME>
- Paths/refs:
  - `<PATH_1>`
  - `<PATH_2>`

## Plan / deliverables
- [ ] <DELIVERABLE_1>
- [ ] <DELIVERABLE_2>
- [ ] <DELIVERABLE_3> (optional)

## Tests / evidence
- Tests to run: <FILL_ME>
- Evidence path: `REHYDRATION_PACK/RUNS/<RUN_ID>/`

## Risk + gate (mandatory)
- Apply exactly one risk label: `risk:R0-docs | risk:R1-low | risk:R2-medium | risk:R3-high | risk:R4-critical`
- Apply `gate:claude` on the PR (no skips).
- PR description must follow `REHYDRATION_PACK/PR_DESCRIPTION/` and include the PR_QUALITY self-score (08) with gates:
  - R0/R1: title ≥95, body ≥95
  - R2: title ≥95, body ≥97
  - R3/R4: title ≥95, body ≥98
- Evidence:
  - PR labels: `gh pr view <PR#> --json labels --jq '.labels[].name'`
  - Claude PASS comment link with `response_id`

## Handoff (on completion)
- Summary of changes + files touched
- Tests run and results
- Evidence artifacts path
- Branch name, PR #, last commit SHA
- Prompt set fingerprint (from `python scripts/run_ci_checks.py` or `verify_agent_prompts_fresh.py`)
