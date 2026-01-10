# Run Meta

- RUN_ID: `RUN_20260110_0244Z`
- Mode: build
- Objective: Enforce durable run reports + prompt archive + checklist hygiene; make CI fail when latest run is missing/under-reported.
- Stop conditions: `python scripts/run_ci_checks.py` passes; latest run contains required populated artifacts (A/B/C + RUN_REPORT + required docs); docs + generated registries updated and committed.

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
