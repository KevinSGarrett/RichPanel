# Test Matrix

**Run ID:** RUN_20260113_1309Z  
**Agent:** B  
**Date:** 2026-01-13

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent checks | `python scripts/run_ci_checks.py --ci` | ✅ PASS (post-fix rerun) | Console excerpt in `RUN_REPORT.md` |
| Unit: Richpanel client | `python scripts/test_richpanel_client.py` | ✅ PASS | `RUN_REPORT.md` |
| Unit: Pipeline handlers | `python scripts/test_pipeline_handlers.py` | ✅ PASS | `RUN_REPORT.md` |
| Unit: Smoke encoding/criteria | `python scripts/test_e2e_smoke_encoding.py` | ✅ PASS | `RUN_REPORT.md` |
| Order-status E2E proof (DEV) | `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile richpanel-dev --ticket-number 1035 --run-id RUN_20260113_1309Z --scenario order_status --apply-test-tag --proof-path REHYDRATION_PACK/RUNS/RUN_20260113_1309Z/B/e2e_outbound_proof.json` | ✅ PASS | `REHYDRATION_PACK/RUNS/RUN_20260113_1309Z/B/e2e_outbound_proof.json` |

## Notes
- E2E PASS via deterministic middleware tag `mw-order-status-answered:RUN_20260113_1309Z`; no skip/escalation tags added this run; status remains OPEN by policy.  
- run_ci_checks regenerated doc registries; working tree clean after regen.  
