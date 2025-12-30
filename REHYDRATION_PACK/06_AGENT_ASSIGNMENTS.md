# Agent Assignments (Build Mode Only)

This file is the **single source of truth** for “what each Cursor agent should do next”.

## When this file is active
- Active only when: `REHYDRATION_PACK/MODE.yaml` has `mode: build`
- In `foundation` mode: this file should remain a **template** and is not executed.

---

## Required header (PM must fill in)
- **RUN_ID:** `RUN_<YYYYMMDD>_<HHMMZ>` (UTC)
- **Mode:** build
- **Run objective (1–2 sentences):** <FILL_ME>
- **Stop conditions (when to stop and report back):** <FILL_ME>

---

## Agent A — Assignment

### Context (read first)
- <PATH_1>
- <PATH_2>

### Objective
<FILL_ME>

### Deliverables (explicit)
- [ ] <DELIVERABLE_1>
- [ ] <DELIVERABLE_2>

### Tests / evidence required
- Tests to run: <FILL_ME>
- Evidence location: `qa/test_evidence/<RUN_ID>/` (or CI link)

### Output path
- `REHYDRATION_PACK/RUNS/<RUN_ID>/A/`

---

## Agent B — Assignment

### Context (read first)
- <PATH_1>
- <PATH_2>

### Objective
<FILL_ME>

### Deliverables (explicit)
- [ ] <DELIVERABLE_1>
- [ ] <DELIVERABLE_2>

### Tests / evidence required
- Tests to run: <FILL_ME>
- Evidence location: `qa/test_evidence/<RUN_ID>/` (or CI link)

### Output path
- `REHYDRATION_PACK/RUNS/<RUN_ID>/B/`

---

## Agent C — Assignment

### Context (read first)
- <PATH_1>
- <PATH_2>

### Objective
<FILL_ME>

### Deliverables (explicit)
- [ ] <DELIVERABLE_1>
- [ ] <DELIVERABLE_2>

### Tests / evidence required
- Tests to run: <FILL_ME>
- Evidence location: `qa/test_evidence/<RUN_ID>/` (or CI link)

### Output path
- `REHYDRATION_PACK/RUNS/<RUN_ID>/C/`

---

## Notes
- Per-run report templates: `REHYDRATION_PACK/_TEMPLATES/`
- Cursor prompt template: `REHYDRATION_PACK/_TEMPLATES/Cursor_Agent_Prompt_TEMPLATE.md`
