# Fix Report (If Applicable)

**Run ID:** RUN_20260116_0236Z  
**Agent:** B  
**Date:** 2026-01-16

## Failure observed
- error: `[FAIL] Generated files changed after regen. Commit the regenerated outputs.`
- where: GitHub Actions validate job (https://github.com/KevinSGarrett/RichPanel/actions/runs/21054006892/job/60546233080)
- repro steps: push doc updates without regenerating `docs/_generated/*` outputs
- error: Claude review failed: "Claude Code is not installed on this repository."
- where: Claude review run (https://github.com/KevinSGarrett/RichPanel/actions/runs/21056411699/job/60553452409)
- repro steps: apply `gate:claude` label before installing Claude app or providing `github_token`

## Diagnosis
- likely root cause: CI runbook changes require doc registry regeneration; generated files were stale.

## Fix applied
- files changed: `docs/_generated/doc_registry.compact.json`, `docs/_generated/doc_registry.json`
- why it works: `python scripts/regen_doc_registry.py` updated generated registries to match the edited runbook and cleared the CI diff check.
- files changed: `.github/workflows/claude-review.yml`
- why it works: added `id-token: write` and `github_token: ${{ github.token }}` so the action can authenticate without the Claude GitHub App.

## Verification
- tests run: `python scripts/run_ci_checks.py --ci` (local pass; run artifacts stashed), GitHub Actions validate
- results: validate pass (https://github.com/KevinSGarrett/RichPanel/actions/runs/21056526718/job/60553783490), Codecov patch pass, Bugbot check pass, Claude review pass (https://github.com/KevinSGarrett/RichPanel/actions/runs/21056526726/job/60553783517)
