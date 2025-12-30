# Cursor Agent Prompt

**Run ID:** RUN_<YYYYMMDD>_<HHMMZ>  
**Agent:** Agent A | Agent B | Agent C  
**Task ID(s):** <TASK-###, ...>

## Context (read first)
- Current goal:
- Relevant docs:
  - `docs/...`
  - `REHYDRATION_PACK/...`
  - `reference/...` (if needed)

## Objective
<What you must deliver in this run>

## Constraints (must follow)
- Follow policies in `docs/98_Agent_Ops/Policies/`
- Follow project overrides: `docs/98_Agent_Ops/Policies/POL-OVR-001__Project_Overrides_(Agent_Rules).md`
- **No secrets** in repo or prompts (Secrets Manager only)
- Prefer minimal changes, but **refactors are allowed with guardrails** (tests + docs + stable contracts)
- Update navigation artifacts if structure changes (`docs/CODEMAP.md`, indexes, registry)

## Deliverables (must write to run folder)
Write into:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/`

Include:
- `RUN_SUMMARY.md`
- `STRUCTURE_REPORT.md`
- `DOCS_IMPACT_MAP.md`
- `TEST_MATRIX.md`
- `FIX_REPORT.md` (only if needed)

## Step-by-step
1. Read the referenced docs.
2. Make the change(s).
3. Run the planned tests and record evidence.
4. Update docs/maps/registry if needed.
5. Fill out the run folder files.
