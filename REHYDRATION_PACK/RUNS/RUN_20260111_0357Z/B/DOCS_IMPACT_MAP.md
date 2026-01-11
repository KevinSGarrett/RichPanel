# Docs Impact Map

**Run ID:** `RUN_20260111_0357Z`  
**Agent:** B  
**Date:** 2026-01-11

## Docs changed this run

| Doc path | Change type | Why |
|---|---|---|
| `docs/08_Engineering/CI_and_Actions_Runbook.md` | Updated | Added Codecov and lint enforcement sections (9-10), updated Section 1 with new CI steps |

## Docs that may need future updates

| Doc path | Potential change | Trigger |
|---|---|---|
| `docs/08_Engineering/CI_and_Actions_Runbook.md` | Remove continue-on-error from lint steps | When ruff/black/mypy pass cleanly |

## Notes
The CI runbook now accurately reflects the complete CI workflow including coverage collection with unittest discover and Codecov upload.
