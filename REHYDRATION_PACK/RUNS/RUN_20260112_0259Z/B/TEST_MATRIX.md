# Test Matrix

**Run ID:** `RUN_20260112_0259Z`  
**Agent:** B (Engineering)  
**Date:** 2026-01-12

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI checks | `python scripts/run_ci_checks.py --ci` | PASS | CI output in PR #82 |
| Dev E2E smoke with tagging | `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --idempotency-table rp_mw_dev_idempotency --wait-seconds 90 --profile richpanel-dev --ticket-number 1023 --run-id RUN_20260112_0259Z --apply-test-tag --proof-path REHYDRATION_PACK/RUNS/RUN_20260112_0259Z/B/e2e_outbound_proof.json` | PASS | `e2e_outbound_proof.json` |

## Notes
- The proof JSON produced by this run contained a PII leak (URL-encoded email/message-id in path fields)
- This was identified by Bugbot review and fixed in follow-up run RUN_20260112_0408Z
- The proof JSON in this folder has been superseded by the sanitized version in RUN_20260112_0408Z
