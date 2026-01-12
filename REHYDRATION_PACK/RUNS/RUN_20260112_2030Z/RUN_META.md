# Run Meta

- RUN_ID: `RUN_20260112_2030Z`
- Mode: build
- Objective: Make order lookup payload-first so seeded payloads can drive order summaries without Shopify calls when shipping signals are present.
- Stop conditions: CI/Codecov/Bugbot green; payload-first helper working offline and online; run artifacts completed.

## Notes
- Each agent writes to its folder: A/, B/, C/
- Required deliverables are enforced by: `python scripts/verify_rehydration_pack.py` (build mode)
- Prompt archives are stored under: `C/AGENT_PROMPTS_ARCHIVE.md`
