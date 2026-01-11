# Test Matrix

**Run ID:** `RUN_20260111_2301Z`  
**Agent:** B  
**Date:** 2026-01-11

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Outbound smoke (DEV) | `python scripts/dev_richpanel_outbound_smoke.py --profile richpanel-dev --env dev --region us-east-2 --conversation-id api-scentimenttesting3300-41afc455-345e-4c18-b17f-ee0f0e9166e0 --confirm-test-ticket --allow-non-test-ticket --run-id RUN_20260111_2301Z` | PASS (tags present; status OPEN) | `REHYDRATION_PACK/RUNS/RUN_20260111_2301Z/B/e2e_outbound_proof.json` |
| CI equivalent | `python scripts/run_ci_checks.py --ci` | PASS | command output |

## Notes
- Smoke proof shows tags applied; status remained OPEN. No PII captured (only hashes/IDs).
