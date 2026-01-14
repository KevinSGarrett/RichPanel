# Run Meta

- RUN_ID: `RUN_20260114_0707Z`
- Mode: build
- Objective: Add DEV-only outbound toggle workflow with auto-revert, document DEV proof window steps, and land with CI/Bugbot/Codecov evidence.
- Stop conditions: Workflow + docs shipped, CI-equivalent and PR checks green (including Bugbot/Codecov), run artifacts captured, branch set to auto-merge.

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
