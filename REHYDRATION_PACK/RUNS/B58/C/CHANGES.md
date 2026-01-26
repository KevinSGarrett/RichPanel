# B58/C Changes

## Code
- Updated `scripts/live_readonly_shadow_eval.py` guardrails to require `MW_ALLOW_NETWORK_READS=true` and `RICHPANEL_WRITE_DISABLED=true` without requiring `RICHPANEL_OUTBOUND_ENABLED`.
- Updated `scripts/test_live_readonly_shadow_eval.py` to match the new guardrail set.
- Updated `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md` to reflect outbound-disabled read-only runs.

## Artifacts
- `REHYDRATION_PACK/RUNS/B58/C/PROOF/live_readonly_shadow_report.json`
- `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260126_0154Z.json`
- `artifacts/readonly_shadow/live_readonly_shadow_eval_http_trace_RUN_20260126_0154Z.json`
