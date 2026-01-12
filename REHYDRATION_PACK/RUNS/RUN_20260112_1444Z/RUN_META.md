# Run Meta

- RUN_ID: `RUN_20260112_1444Z`
- Mode: build
- Objective: Close worker flag wiring coverage gap and refresh run artifacts.
- Stop conditions: Codecov/CI green locally with updated run docs.

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
