# Evidence — B62/C

## Commands run (sample artifact generation; no network)
```powershell
cd C:\RichPanel_GIT
python REHYDRATION_PACK\RUNS\B62\C\PROOF\generate_sample_report.py
```

## Commands run (unit tests)
```powershell
cd C:\RichPanel_GIT
python scripts\test_live_readonly_shadow_eval.py
```

## Intended live run (not executed here; requires prod read-only creds)
```powershell
$env:RICHPANEL_ENV = "prod"
$env:MW_ALLOW_NETWORK_READS = "true"
$env:RICHPANEL_READ_ONLY = "true"
$env:RICHPANEL_WRITE_DISABLED = "true"
$env:RICHPANEL_OUTBOUND_ENABLED = "false"
$env:SHOPIFY_OUTBOUND_ENABLED = "true"
$env:SHOPIFY_SHOP_DOMAIN = "<redacted>.myshopify.com"

python scripts\live_readonly_shadow_eval.py `
  --env prod `
  --region us-east-2 `
  --max-tickets 10 `
  --shopify-probe `
  --out REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_report.json `
  --summary-md-out REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_summary.md `
  --allow-empty-sample
```

## Key metrics (from sample report)
- ticket_count: 17
- match_success_rate: 94.12%
- tracking_or_eta_available_rate: 94.12%
- would_reply_send: false
- match_failure_buckets: no_email=0, no_order_number=0, ambiguous_customer=0, no_order_candidates=0,
  order_match_failed=0, parse_error=0, api_error=0, other_failure=0, unknown=1

## Read-only confirmation
- `env_flags` in `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_report.json`:
  `MW_ALLOW_NETWORK_READS=true`, `RICHPANEL_READ_ONLY=true`,
  `RICHPANEL_WRITE_DISABLED=true`, `RICHPANEL_OUTBOUND_ENABLED=false`
- `http_trace_summary.allowed_methods_only=true` in `live_shadow_report.json`
- Trace file: `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_http_trace.json`

## B61/C merge status
- B61/C diagnostics are already present in `scripts/live_readonly_shadow_eval.py` and the prod runbook.

## Notes
- No prod credentials available in this environment; sample artifacts are derived from
  `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260126_0319Z.json`.
