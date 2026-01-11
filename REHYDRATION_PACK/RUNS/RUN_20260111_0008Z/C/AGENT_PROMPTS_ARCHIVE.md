# Agent Prompts Archive

Archived as part of `RUN_20260111_0008Z`.

---

# Current Cursor Agent Prompts (build mode)

This file must contain **only the currently active prompts** for the current run/cycle.

prompt-repeat-override: true

**⚠️ REQUIRED IN EVERY PROMPT:** Model + MAX mode + Cycle metadata (see below)

---

## Model + MAX mode + Cycle (REQUIRED)

**Every prompt set MUST include this section for each agent:**

```markdown
## Model + MAX mode + Cycle
- **Model used:** <model-name> (see REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md)
- **MAX mode:** ON | OFF
- **Cycle:** 1× | 2× | 3× | 4×
```

**Why this matters:**
- Prevents drift where some prompts omit guidance
- Makes prompt archives searchable by model
- Helps PM/agents understand context budget and review depth

**Source of truth:**
- Model list: `REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md`
- Active model picker: Cursor IDE model picker (always check there first)

---

## Workflow (starting a new run)

If you are starting a new run:
1) Create a run folder skeleton:
```bash
python scripts/new_run_folder.py --now
```
2) Paste the active prompts here (Agent A/B/C), including the **Model + MAX mode + Cycle** section for each agent
3) Run agents sequentially to avoid merge conflicts
4) When the cycle ends, archive the prior prompt text under `REHYDRATION_PACK/RUNS/<RUN_ID>/C/`

---

## Archive pointer (do not edit)
- Prior prompt content for `RUN_20260103_2300Z` was archived to:
  - `REHYDRATION_PACK/RUNS/RUN_20260103_2300Z/C/AGENT_PROMPTS_ARCHIVE.md`

---

## Current prompts

### Agent C — TicketMetadata shadow fix + GPT-5.2 defaults

```markdown
# Cursor Agent Prompt

**Run ID:** `RUN_20260111_0008Z`  
**Agent:** Agent C  
**Task ID(s):** TicketMetadata shadowing fix + GPT-5.2 defaults + CI + PR/automerge

## Model + MAX mode + Cycle (REQUIRED)
- **Model used:** gpt-5.1-codex-max (Cursor picker)
- **MAX mode:** ON
- **Cycle:** 1×

## Objective
Resolve TicketMetadata shadowing in the automation pipeline, ensure middleware defaults use `gpt-5.2-chat-latest`, and deliver CI evidence plus PR/automerge setup with Bugbot trigger.

## Deliverables (explicit)
- [ ] Fix TicketMetadata shadowing using the shared richpanel tickets helper.
- [ ] Confirm/align GPT-5.2 defaults across routing/prompts/tests/.env.example.
- [ ] Run `python scripts/run_ci_checks.py` and capture evidence in `REHYDRATION_PACK/RUNS/RUN_20260111_0008Z/C/RUN_REPORT.md`.
- [ ] Open PR with auto-merge enabled (merge commit) and comment `@cursor review`.
```

### Agent A ??? WaveAudit checklist + rehydration drift fixes

```markdown
# Cursor Agent Prompt

**Run ID:** `RUN_20260110_1638Z`  
**Agent:** Agent A  
**Task ID(s):** WaveAudit midpoint audit checklist + template drift + verifier enforcement

## Model + MAX mode + Cycle (REQUIRED)
- **Model used:** <model-name> (see `REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md`)
- **MAX mode:** ON | OFF
- **Cycle:** 1??

## Context (read first)
- Current goal: Convert WaveAudit findings into repo checklists and fix REHYDRATION_PACK drift; run CI checks; open PR.
- Relevant docs/paths:
  - `docs/00_Project_Admin/To_Do/MIDPOINT_AUDIT_CHECKLIST.md`
  - `docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md`
  - `REHYDRATION_PACK/05_TASK_BOARD.md`
  - `REHYDRATION_PACK/_TEMPLATES/Cursor_Agent_Prompt_TEMPLATE.md`
  - `scripts/verify_rehydration_pack.py`

## Objective
Convert WaveAudit findings into a repo-native midpoint audit checklist and ensure REHYDRATION_PACK templates/verifiers enforce evidence-backed run reporting.

## Deliverables (explicit)
- [ ] Midpoint audit checklist created and wired into PM docs.
- [ ] Cursor agent prompt template requires: RUN_REPORT.md + RUN_SUMMARY.md + STRUCTURE_REPORT.md + DOCS_IMPACT_MAP.md + TEST_MATRIX.md.
- [ ] `scripts/verify_rehydration_pack.py` enforces required RUN_REPORT sections (Diffstat / Commands Run / Tests / Proof / Files Changed).
- [ ] `python scripts/run_ci_checks.py` passes and output is captured in `REHYDRATION_PACK/RUNS/RUN_20260110_1638Z/A/RUN_REPORT.md`.
- [ ] PR opened; auto-merge enabled (merge commit); Bugbot triggered with `@cursor review`.

## Tests / evidence required
- Tests to run: `python scripts/run_ci_checks.py`
- Evidence location:
  - `REHYDRATION_PACK/RUNS/RUN_20260110_1638Z/A/RUN_REPORT.md` (commands + outputs)
```

---

### Agent B ??? Review routing + personalization alignment (WaveAudit)

```markdown
# Cursor Agent Prompt

**Run ID:** `RUN_20260110_1638Z`  
**Agent:** Agent B  
**Task ID(s):** Midpoint audit review (routing + personalization)

## Model + MAX mode + Cycle (REQUIRED)
- **Model used:** <model-name> (see `REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md`)
- **MAX mode:** ON | OFF
- **Cycle:** 1??

## Context (read first)
- `docs/00_Project_Admin/To_Do/MIDPOINT_AUDIT_CHECKLIST.md`

## Objective
Review the Midpoint Audit checklist for routing/personalization correctness (including the shift to guardrailed OpenAI rewrite) and propose any missing tasks/evidence requirements.

## Deliverables (explicit)
- [ ] PR comment or patch improving checklist items related to routing + personalization.
- [ ] Any required follow-ups added to the checklist with clear evidence requirements.

## Tests / evidence required
- Tests to run: N/A (docs-only), unless code is changed.
```

---

### Agent C ??? Review QA/ops readiness items (WaveAudit)

```markdown
# Cursor Agent Prompt

**Run ID:** `RUN_20260110_1638Z`  
**Agent:** Agent C  
**Task ID(s):** Midpoint audit review (QA + Richpanel ops)

## Model + MAX mode + Cycle (REQUIRED)
- **Model used:** <model-name> (see `REHYDRATION_PACK/07_CURSOR_MODEL_CATALOG.md`)
- **MAX mode:** ON | OFF
- **Cycle:** 1??

## Context (read first)
- `docs/00_Project_Admin/To_Do/MIDPOINT_AUDIT_CHECKLIST.md`

## Objective
Review QA/test-evidence + Richpanel configuration checklist items for completeness and make sure each item has clear, objective evidence requirements.

## Deliverables (explicit)
- [ ] PR comment or patch improving checklist items related to QA evidence + Richpanel ops configuration.

## Tests / evidence required
- Tests to run: N/A (docs-only), unless code is changed.
```
