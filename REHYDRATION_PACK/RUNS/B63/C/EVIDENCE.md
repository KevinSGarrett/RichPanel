# Evidence — B63/C

## Commands run (unit tests)
```powershell
cd C:\RichPanel_GIT
python scripts\test_live_readonly_shadow_eval.py
```

## Commands run (shadow validator)
```powershell
cd C:\RichPanel_GIT
gh workflow run shadow_live_readonly_eval.yml --ref main `
  -f sample-size=10 `
  -f shopify-probe=true `
  -f shopify-token-source=api `
  -f shop-domain=<redacted>.myshopify.com

gh run download 21462034933 -n live-readonly-shadow-eval -D C:\RichPanel_GIT\_tmp_shadow_eval_b63_baseline

gh workflow run shadow_live_readonly_eval.yml --ref b63/shadow-validator-drift-triage `
  -f sample-size=10 `
  -f shopify-probe=true `
  -f shopify-token-source=api `
  -f shop-domain=<redacted>.myshopify.com

gh run download 21462527530 -n live-readonly-shadow-eval -D C:\RichPanel_GIT\_tmp_shadow_eval_b63_final
```

## Drift-watch summary (before vs after)
- **Before (B62/C RUN_20260128_1811Z):** schema_new_ratio_pct=52.94; api_error_rate_pct=0.0; has_alerts=true (schema_drift)
- **Before (main RUN_20260129_0126Z):** schema_new_ratio_pct=23.16; api_error_rate_pct=12.84; has_alerts=true (api_error_rate, schema_drift)
- **After (B63/C RUN_20260129_0150Z):** schema_new_ratio_pct=13.54; api_error_rate_pct=0.0; has_alerts=false

## Read-only confirmation
- `env_flags` in `REHYDRATION_PACK/RUNS/B63/C/PROOF/live_shadow_report.json`:
  `MW_ALLOW_NETWORK_READS=true`, `RICHPANEL_READ_ONLY=true`,
  `RICHPANEL_WRITE_DISABLED=true`, `RICHPANEL_OUTBOUND_ENABLED=false`
- `http_trace_summary.allowed_methods_only=true` in `live_shadow_report.json`
- Trace file: `REHYDRATION_PACK/RUNS/B63/C/PROOF/live_shadow_http_trace.json`

## Notes
- `run_warnings` includes `ticket_fetch_failed` due to stale explicit ticket IDs; drift-watch API error rate now excludes these and the warnings remain visible.
