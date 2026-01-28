# Evidence — B62/C

## Commands run (unit tests)
```powershell
cd C:\RichPanel_GIT
python scripts\test_live_readonly_shadow_eval.py
```

## Commands run (CI workflow, prod read-only)
```powershell
cd C:\RichPanel_GIT
gh workflow run shadow_live_readonly_eval.yml --ref b62-channel-aware-outbound `
  -f sample-size=10 `
  -f shopify-probe=true `
  -f shop-domain=<redacted>.myshopify.com

gh run download 21446879808 -n live-readonly-shadow-eval -D C:\RichPanel_GIT\_tmp_shadow_eval
```

## Attempted run (AWS Secrets Manager; failed)
```powershell
cd C:\RichPanel_GIT
gh workflow run shadow_live_readonly_eval.yml --ref b62-channel-aware-outbound `
  -f sample-size=10 `
  -f shopify-probe=true `
  -f use-aws-secrets=true `
  -f shop-domain=<redacted>.myshopify.com
```
- Failure: `ResourceNotFoundException` for `rp-mw/prod/*` secrets (run `21447011102`).

## Key metrics (live report `RUN_20260128_1637Z`)
- ticket_count: 17 (sample_mode: explicit)
- match_success_rate: 0.0%
- tracking_or_eta_available_rate: 0.0%
- would_reply_send: false
- match_failure_buckets: no_order_number=3, no_order_candidates=6, other_failure=8
- top_failure_reasons: no_order_candidates=9, ticket_fetch_failed=8
- run_warnings: ticket_fetch_failed
- drift_watch.has_alerts: true (api_error_rate + schema_drift)
- shopify_probe.status_code: 401

## Read-only confirmation
- `env_flags` in `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_report.json`:
  `MW_ALLOW_NETWORK_READS=true`, `RICHPANEL_READ_ONLY=true`,
  `RICHPANEL_WRITE_DISABLED=true`, `RICHPANEL_OUTBOUND_ENABLED=false`
- `http_trace_summary.allowed_methods_only=true` in `live_shadow_report.json`
- Trace file: `REHYDRATION_PACK/RUNS/B62/C/PROOF/live_shadow_http_trace.json`

## Claude gate (real run)
- Workflow run: https://github.com/KevinSGarrett/RichPanel/actions/runs/21447344671
- Audit artifact: `REHYDRATION_PACK/RUNS/B62/C/PROOF/claude_gate_audit.json`
- model_used: `claude-opus-4-5-20251101`
- response_id: `msg_018M4ZC5A1bjxaLrHvWZMANz`
- request_id: `req_011CXa7zv77tRw7JSX2D79Fk`
- usage: input_tokens=25917; output_tokens=600; cache_creation_input_tokens=0; cache_read_input_tokens=0; service_tier=standard

## B61/C merge status
- PR #197 (B61/C) merged: https://github.com/KevinSGarrett/RichPanel/pull/197

## Notes
- CI run: https://github.com/KevinSGarrett/RichPanel/actions/runs/21446879808
- Claude gate initial runs failed due to PR metadata fetch; fixed via GraphQL fallback in `scripts/claude_gate_review.py`.
