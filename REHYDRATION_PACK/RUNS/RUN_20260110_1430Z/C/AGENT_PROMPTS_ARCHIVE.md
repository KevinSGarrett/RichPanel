# Agent Prompts Archive

Archived as part of `RUN_20260110_1430Z`.

---

# Current Cursor Agent Prompts (build mode)

This file must contain **only the currently active prompts** for the current run/cycle.

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
> No active prompts are declared in this file right now. Use:
> - `REHYDRATION_PACK/05_TASK_BOARD.md` for what to do next
> - `REHYDRATION_PACK/02_CURRENT_STATE.md` for the current truth snapshot
>
> **When you add prompts, remember to include the Model + MAX mode + Cycle section for each agent!**
