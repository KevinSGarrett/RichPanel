# Wave F01c — Mode Clarification Changelog

Date: 2025-12-28

## Why
We clarified that **foundation mode** (structure + documentation architecture) does **not** require Cursor prompts/summaries/run outputs.
Those artifacts are only required once we flip to **build mode**.

## Key changes
- Added `REHYDRATION_PACK/MODE.yaml` to explicitly track `foundation` vs `build`.
- Updated rehydration pack entrypoint, spec, and guardrails to be mode-aware.
- Converted `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` into a build-mode-only template.
  - Preserved previous draft assignments under `REHYDRATION_PACK/_DRAFTS/`.
- Updated meta pack (`PM_REHYDRATION_PACK/`) to reflect the corrected workflow and updated wave plan.

## Files added/updated
- `REHYDRATION_PACK/MODE.yaml` (new)
- `REHYDRATION_PACK/00_START_HERE.md` (updated)
- `REHYDRATION_PACK/MANIFEST.yaml` (updated)
- `REHYDRATION_PACK/PM_GUARDRAILS.md` (updated)
- `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` (updated)
- `REHYDRATION_PACK/_DRAFTS/06_AGENT_ASSIGNMENTS_DRAFT_BUILD.md` (new)
- `docs/98_Agent_Ops/Rehydration_Pack_Spec.md` (updated)
- `REHYDRATION_PACK/WAVE_SCHEDULE.md` (updated)
- `REHYDRATION_PACK/03_ACTIVE_WORKSTREAMS.md` (updated)
- `REHYDRATION_PACK/05_TASK_BOARD.md` (updated)
- `REHYDRATION_PACK/02_CURRENT_STATE.md` (updated)
- `PM_REHYDRATION_PACK/*` (updated multiple files)

