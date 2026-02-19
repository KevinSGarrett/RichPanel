# Test Matrix

**Run ID:** `RUN_20260218_1954Z`  
**Agent:** C  
**Date:** 2026-02-18

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI checks | `python scripts/run_ci_checks.py --ci` | pass | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/run_ci_checks.log` |
| Rehydration pack | `python scripts/verify_rehydration_pack.py` | pass | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/verify_rehydration_pack.log` |
| CDK diff (staging) | `AWS_PROFILE=rp-admin-staging npx cdk diff RichpanelMiddleware-staging` | pass (diff includes unrelated changes; blocker) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/cdk_diff_staging.txt` |
| Deploy Prod Stack | GitHub Actions workflow run 22161726807 | pass | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/deploy_prod_main_run_22161726807.log` |
| Read-only shadow eval | `python scripts/live_readonly_shadow_eval.py --env prod --max-tickets 1` | fail (Richpanel 504 timeout) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/prod_readonly_shadow_eval.log` |
| Shadow Live Read-Only Eval (workflow) | run 22162429932 | fail (OpenAI routing disabled in workflow env) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/shadow_eval_run_22162429932.log` |
| Read-only shadow eval (ticket IDs) | `python scripts/live_readonly_shadow_eval.py --ticket-id ...` | partial (ticket ok; conversation 403; order_status candidate; OpenAI calls observed) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/prod_shadow_summary.json` |
| Rewrite inference note | N/A | partial (OpenAI calls + rewrite model env) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/prod_shadow_rewrite_inference.md` |
| CDK diff (prod) | `AWS_PROFILE=rp-admin-prod npx cdk diff RichpanelMiddleware-prod` | pass | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/cdk_diff_prod.txt` |
| Prod kill-switch check | `aws ssm get-parameters --names <safe_mode> <automation_enabled>` | pass (safe_mode=true, automation_enabled=false) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/prod_safe_mode_automation_status.txt` |
| Deploy Staging Stack (main) | `gh workflow run "Deploy Staging Stack" --ref main` | fail (LogGroup exists) | `REHYDRATION_PACK/RUNS/RUN_20260218_1954Z/C/evidence/deploy_staging_main_run_22157069157.log` |

## Notes
AWS SSO credentials are required before CDK diffs and deployment verification can proceed.
