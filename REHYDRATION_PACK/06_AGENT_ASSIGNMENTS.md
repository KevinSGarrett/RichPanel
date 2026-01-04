# Current Cursor Agent Prompts (build mode)

This file must contain **only the currently active prompts** for the current run/cycle.

If you are starting a new run:
1) Create a run folder skeleton:
```bash
python scripts/new_run_folder.py --now
```
2) Paste the active prompts here (Agent A/B/C), then run agents sequentially to avoid merge conflicts.
3) When the cycle ends, archive the prior prompt text under `REHYDRATION_PACK/RUNS/<RUN_ID>/C/`.

## Archive pointer (do not edit)
- Prior prompt content for `RUN_20260103_2300Z` was archived to:
  - `REHYDRATION_PACK/RUNS/RUN_20260103_2300Z/C/AGENT_PROMPTS_ARCHIVE.md`

## Current prompts
> No active prompts are declared in this file right now. Use:
> - `REHYDRATION_PACK/05_TASK_BOARD.md` for what to do next
> - `REHYDRATION_PACK/02_CURRENT_STATE.md` for the current truth snapshot
