# Test Matrix

**Run ID:** RUN_20260214_0300Z  
**Agent:** B  
**Date:** 2026-02-14

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| Runtime flags (before) | aws ssm get-parameters --names /rp-mw/prod/safe_mode /rp-mw/prod/automation_enabled | pass | REHYDRATION_PACK/RUNS/RUN_20260214_0300Z/B/prod_runtime_flags_before.json |
| Runtime flags (after) | aws ssm get-parameters --names /rp-mw/prod/safe_mode /rp-mw/prod/automation_enabled | pass | REHYDRATION_PACK/RUNS/RUN_20260214_0300Z/B/prod_runtime_flags_after.json |
| Deploy-prod workflow | gh workflow run deploy-prod.yml --ref main | pass | https://github.com/KevinSGarrett/RichPanel/actions/runs/22010351142
 |
| Preflight (prod) | python scripts/order_status_preflight_check.py --env prod --skip-refresh-lambda-check | pass | REHYDRATION_PACK/RUNS/RUN_20260214_0300Z/B/preflight_prod.json |
| Runtime flags (postdeploy) | aws ssm get-parameters --names /rp-mw/prod/safe_mode /rp-mw/prod/automation_enabled | pass | REHYDRATION_PACK/RUNS/RUN_20260214_0300Z/B/prod_runtime_flags_postdeploy.json |
| CI gate | python scripts/run_ci_checks.py --ci | pending | output snippet in B/RUN_REPORT.md |

## Notes
Deploy-prod workflow URL: https://github.com/KevinSGarrett/RichPanel/actions/runs/22010351142

