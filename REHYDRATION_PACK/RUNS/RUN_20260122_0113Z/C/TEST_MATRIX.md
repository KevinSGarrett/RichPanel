# Test Matrix

**Run ID:** `RUN_20260122_0113Z`  
**Agent:** C  
**Date:** 2026-01-22

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Dev E2E smoke (John scenario) | python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-dev --ticket-number <redacted> --run-id RUN_20260122_0113Z --scenario order_status_no_tracking_standard_shipping_3_5 --require-openai-routing --require-openai-rewrite --proof-path REHYDRATION_PACK/RUNS/RUN_20260122_0113Z/C/e2e_order_status_no_tracking_standard_shipping_3_5_proof.json | pass | REHYDRATION_PACK/RUNS/RUN_20260122_0113Z/C/e2e_order_status_no_tracking_standard_shipping_3_5_proof.json |
| CI-equivalent checks | python scripts/run_ci_checks.py --ci | pass | c:\Users\kevin\.cursor\projects\c-Users-kevin-AppData-Roaming-Cursor-Workspaces-1768173996229-workspace-json\agent-tools\a9c6be23-0133-45fa-9af0-c22579738345.txt |

## Notes
CI checks passed after committing regenerated outputs and run artifacts.
