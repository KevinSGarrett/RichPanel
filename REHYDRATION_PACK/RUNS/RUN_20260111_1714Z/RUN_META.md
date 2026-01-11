# Run Meta

- RUN_ID: `RUN_20260111_1714Z`
- Mode: build
- Objective: Ship docs-only PR health check updates (templates, runbook, E2E runbook, Next 10) with clean run artifacts and CI proof
- Stop conditions: CI (`python scripts/run_ci_checks.py --ci`) passes; run artifacts contain no placeholders; scope limited to allowed docs paths

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
