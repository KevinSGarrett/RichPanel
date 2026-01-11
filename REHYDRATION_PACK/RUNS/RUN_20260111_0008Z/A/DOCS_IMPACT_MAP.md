# Docs Impact Map

**Run ID:** `RUN_20260111_0008Z`  
**Agent:** A  
**Date:** 2026-01-11

Goal: document what changed and where documentation must be updated.

## Docs updated in this run
- `docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md` — Added Codecov-specific epics (upload shipped, branch-protection required checks roadmap) and a middleware GPT-5.x-only defaults epic; refreshed total/shipped/in-progress/roadmap counts and percentages.
- `docs/08_Engineering/CI_and_Actions_Runbook.md` — Added a “Codecov verification (per-PR)” checklist describing how to capture the CI run URL and verify Codecov status checks on PRs using GitHub UI and `gh` CLI.
- `docs/00_Project_Admin/Progress_Log.md` — Advanced the progress log to RUN_20260111_0008Z and summarized this run’s docs/CI alignment work so admin-logs sync validation can pass.
- `REHYDRATION_PACK/RUNS/RUN_20260111_0008Z/A/RUN_REPORT.md` — Filled with run metadata, diffstat, commands, tests, and CI evidence.
- `REHYDRATION_PACK/RUNS/RUN_20260111_0008Z/A/RUN_SUMMARY.md` — Captured objectives, work completed, files changed, Git/GitHub status, and follow-up decisions.
- `REHYDRATION_PACK/RUNS/RUN_20260111_0008Z/A/STRUCTURE_REPORT.md` — Documented structural impact (no new files) and rationale for doc alignment.
- `REHYDRATION_PACK/RUNS/RUN_20260111_0008Z/A/TEST_MATRIX.md` — Logged CI-equivalent tests and evidence path.

## Docs that should be updated next (if any)
- `docs/04_LLM_Design_Evaluation/Model_Config_and_Versioning.md` — Once middleware OpenAI defaults are actually migrated to GPT-5.x family models, update this doc with the concrete deployed defaults (model names, env vars) and link to the implementing code/config.
- `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md` and related automation docs — After model defaults change, ensure any example model references and behavior descriptions match GPT-5.x defaults and do not mention GPT-4/4o.

## Index/registry updates
- `docs/INDEX.md` updated: no
- `docs/CODEMAP.md` updated: no
- `docs/_generated/*` regenerated: yes (via `python scripts/run_ci_checks.py`)
- `reference/_generated/*` regenerated: yes (via `python scripts/run_ci_checks.py`)

## Notes
- This run is documentation- and evidence-focused; middleware OpenAI defaults are not changed yet, but the requirement is now explicitly tracked in admin/checklist docs for a future implementation run.
