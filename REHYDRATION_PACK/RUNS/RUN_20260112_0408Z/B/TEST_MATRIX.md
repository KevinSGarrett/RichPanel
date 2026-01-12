# Test Matrix

**Run ID:** `RUN_20260112_0408Z`  
**Agent:** B (Engineering)  
**Date:** 2026-01-12

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI checks | `python scripts/run_ci_checks.py --ci` | PASS | PR #83 CI checks |
| Dev E2E smoke with PII sanitization | `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --idempotency-table rp_mw_dev_idempotency --wait-seconds 90 --profile richpanel-dev --ticket-number 1023 --run-id RUN_20260112_0408Z --apply-test-tag --proof-path REHYDRATION_PACK/RUNS/RUN_20260112_0408Z/B/e2e_outbound_proof.json` | PASS | `e2e_outbound_proof.json` |
| PII pattern scan | `rg -n "%40\|mail.\|%3C\|%3E\|@" REHYDRATION_PACK/RUNS/RUN_20260112_0408Z/B/e2e_outbound_proof.json` | CLEAN | No matches |

## PR Health Check Evidence
- **PR #83:** https://github.com/KevinSGarrett/RichPanel/pull/83 (merged)
- **PR #84:** https://github.com/KevinSGarrett/RichPanel/pull/84 (cleanup, merged)
- **Bugbot trigger:** https://github.com/KevinSGarrett/RichPanel/pull/83#issuecomment-3736827776
- **Codecov:** https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/83

## Notes
- The proof JSON shows `tags_added` includes `mw-smoke:RUN_20260112_0408Z`
- `updated_at_delta_seconds` is 20.684
- `result.status` is `PASS`
- All paths use `path_redacted` with `<redacted>` placeholders
- PII scan confirms no `%40`, `mail.`, `%3C`, `%3E`, or `@` in the proof JSON
