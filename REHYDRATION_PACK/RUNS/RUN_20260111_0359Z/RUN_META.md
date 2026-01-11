# Run Meta

- RUN_ID: `RUN_20260111_0359Z`
- Mode: build
- Objective: stabilize CI coverage + Codecov flow for PR #74
- Stop conditions: CI workflow updated, run evidence captured, PR ready for CI run

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
