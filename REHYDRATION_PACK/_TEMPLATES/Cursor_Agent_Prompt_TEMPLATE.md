# Cursor Agent Prompt

**Run ID:** `RUN_<YYYYMMDD>_<HHMMZ>`  
**Agent:** Agent A | Agent B | Agent C  
**Task ID(s):** `<TASK-###, TASK-###>`

---

## Model + MAX mode + Cycle (REQUIRED)
- **Model used:** `<model-name>` (see `REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md`)
- **MAX mode:** ON | OFF
- **Cycle:** 1× | 2×

**Note:** Always check Cursor's model picker for the current model list. If you can't find the exact model name, pick the closest family (see catalog).

---

## Context (read first)
- Current goal: <FILL_ME>
- Relevant docs/paths:
  - `<PATH_1>`
  - `<PATH_2>`
  - `<PATH_3>` (optional)

## Objective
<FILL_ME>

## Deliverables (explicit)
- [ ] <DELIVERABLE_1>
- [ ] <DELIVERABLE_2>
- [ ] <DELIVERABLE_3> (optional)

## Tests / evidence required
- Tests to run: <FILL_ME>
- Evidence location:
  - `qa/test_evidence/<RUN_ID>/` (or CI link)

## Required run artifacts (write to your agent folder)
Write to:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT_ID>/`

Required files:
- `RUN_SUMMARY.md`
- `STRUCTURE_REPORT.md`
- `DOCS_IMPACT_MAP.md`
- `TEST_MATRIX.md`

Optional:
- `FIX_REPORT.md` (only if needed)

## Step-by-step
1) Read the referenced docs/paths.
2) Make the changes.
3) Run the planned tests and record evidence.
4) Update docs/maps/registry if needed.
5) Fill out the required run artifacts.
