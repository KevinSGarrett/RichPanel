# Fix Report (If Applicable)

**Run ID:** RUN_20260116_0236Z  
**Agent:** B  
**Date:** 2026-01-16

## Failure observed
- error: `[FAIL] Generated files changed after regen. Commit the regenerated outputs.`
- where: GitHub Actions validate job (https://github.com/KevinSGarrett/RichPanel/actions/runs/21054006892/job/60546233080)
- repro steps: push doc updates without regenerating `docs/_generated/*` outputs

## Diagnosis
- likely root cause: CI runbook changes require doc registry regeneration; generated files were stale.

## Fix applied
- files changed: `docs/_generated/doc_registry.compact.json`, `docs/_generated/doc_registry.json`
- why it works: `python scripts/regen_doc_registry.py` updated generated registries to match the edited runbook and cleared the CI diff check.

## Verification
- tests run: `python scripts/run_ci_checks.py --ci` (local pass; run artifacts stashed), GitHub Actions validate
- results: validate pass (https://github.com/KevinSGarrett/RichPanel/actions/runs/21054059591/job/60546419572), Codecov patch pass, Bugbot review no findings
