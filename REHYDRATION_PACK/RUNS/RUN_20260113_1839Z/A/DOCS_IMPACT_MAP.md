# Docs Impact Map

**Run ID:** `RUN_20260113_1839Z`  
**Agent:** A  
**Date:** 2026-01-13

Goal: document what changed and where documentation must be updated.

## Docs updated in this run
- `REHYDRATION_PACK/_TEMPLATES/Cursor_Agent_Prompt_TEMPLATE.md` — added mandatory wait-for-green polling loop and “no auto-merge until green or documented fallback.”
- `REHYDRATION_PACK/_TEMPLATES/Run_Report_TEMPLATE.md` — added wait-for-green evidence section (timestamps, rollup links, Codecov/Bugbot status).
- `docs/08_Engineering/CI_and_Actions_Runbook.md` — PR Health Check updated with wait-loop guidance and Bugbot quota fallback while still requiring Codecov.
- `REHYDRATION_PACK/09_NEXT_10_SUGGESTED_ITEMS.md` — synced with PM pack priorities (10 items).
- `docs/00_Project_Admin/Progress_Log.md` — added RUN_20260113_1839Z entry and updated last verified.
- `docs/_generated/*` — registries regenerated after doc edits.

## Docs that should be updated next (if any)
- None identified.

## Index/registry updates
- `docs/INDEX.md` updated: no
- `docs/CODEMAP.md` updated: no
- `docs/_generated/*` regenerated: yes
- `reference/_generated/*` regenerated: no

## Notes
- CI must be rerun (`python scripts/run_ci_checks.py --ci`) after isolating changes; wait-loop and PR evidence to be captured post-PR creation.
