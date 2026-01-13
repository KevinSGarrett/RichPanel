# Run Meta

- RUN_ID: `RUN_20260113_1450Z`
- Mode: build
- Objective: Repair order-status automation (restore loop prevention, tighten smoke PASS criteria, produce PASS proof, keep Codecov/Bugbot green).
- Stop conditions: PASS proof with success tag/resolved and no skip/escalation tags added; CI (`python scripts/run_ci_checks.py --ci`) passes; Codecov patch green; Bugbot reports no issues before merge.

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
