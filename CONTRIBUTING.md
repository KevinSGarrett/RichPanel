# Contributing (AI-managed repo)

This project is built using:
- ChatGPT (PM / planner / reviewer)
- Cursor agents (builders)

## Non-negotiable workflow rules
- Follow policies in `docs/98_Agent_Ops/Policies/`
- Keep `REHYDRATION_PACK/` updated every run set
- No orphan docs/files (update `docs/INDEX.md`, `docs/CODEMAP.md`, registry)

## Required artifacts per run set
Store under: `REHYDRATION_PACK/RUNS/<RUN_ID>/`

- `RUN_SUMMARY.md`
- `STRUCTURE_REPORT.md`
- `DOCS_IMPACT_MAP.md`
- `TEST_MATRIX.md`
- `FIX_REPORTS/` (only if needed)

Templates are in:
- `REHYDRATION_PACK/_TEMPLATES/`
- `docs/98_Agent_Ops/Templates/`

## Repo hygiene
- Do not commit secrets.
- Put large outputs under `/artifacts/` or `/runs/` and reference them from the rehydration pack.



## GitHub workflow (agents)
- Branch strategy: `run/<RUN_ID>` (preferred) or `run/<RUN_ID>-A/B/C` in parallel mode.
- Always run before pushing:
  ```bash
  python scripts/run_ci_checks.py
  ```
- See the full playbook:
  - `docs/08_Engineering/Multi_Agent_GitOps_Playbook.md`
