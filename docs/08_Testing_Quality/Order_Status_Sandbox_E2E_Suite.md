# Order Status Sandbox E2E Suite (B67)

This doc describes the sandbox-only E2E suite used to extend proof coverage beyond the golden path. It is PII-safe by design and should never be run against production.

## Preconditions
- Sandbox env only.
- `RICHPANEL_OUTBOUND_ENABLED=true`
- `RICHPANEL_BOT_AGENT_ID` configured for outbound replies.
- `MW_OPENAI_INTENT_ENABLED=true`
- `MW_OPENAI_ROUTING_ENABLED=true`

## Harness
Use `scripts/b67_sandbox_e2e_suite.py` to run a single scenario or the full suite.

Example (suite):
```powershell
python scripts/b67_sandbox_e2e_suite.py --suite --env dev --region <region> --stack-name <stack> --profile <profile> --allowlist-email <redacted>
```

## Scenarios
- `order_status_golden` (keep as baseline)
- `order_status_fallback_email_match` (order-status request without an order number)
- `not_order_status_negative_case` (refund/cancel type request, no auto-reply)
- `followup_after_autoclose` (no second auto-reply)

## Artifacts
Artifacts are written to `REHYDRATION_PACK/RUNS/B67/A/PROOF/`:
- `sandbox_e2e_suite_results.json`
- `sandbox_e2e_suite_summary.md`
- `sandbox_negative_case_proof.json`
- `sandbox_fallback_email_match_proof.json`
- `sandbox_followup_suppression_proof.json`

All artifacts must remain PII-safe (redacted/hashes only).

## Split Evidence (Shopify is live read-only)
There is **no Shopify sandbox/dev store**, so use a split-evidence approach:
- Prod read-only report to prove match method + Shopify fetch.
- Sandbox run to prove `/send-message` + operator reply + close.

Prod read-only example:
```powershell
$env:AWS_PROFILE='rp-admin-kevin'
$env:MW_ALLOW_NETWORK_READS='true'
$env:RICHPANEL_READ_ONLY='true'
$env:RICHPANEL_WRITE_DISABLED='true'
$env:RICHPANEL_OUTBOUND_ENABLED='false'
$env:MW_OPENAI_ROUTING_ENABLED='true'
$env:MW_OPENAI_INTENT_ENABLED='true'
$env:MW_OPENAI_SHADOW_ENABLED='true'
$env:SHOPIFY_OUTBOUND_ENABLED='true'
$env:SHOPIFY_WRITE_DISABLED='true'
python scripts/prod_shadow_order_status_report.py --env prod --richpanel-secret-id rp-mw/prod/richpanel/api_key --shopify-secret-id rp-mw/prod/shopify/admin_api_token --shop-domain scentimen-t.myshopify.com --ticket-number <redacted> --out-json REHYDRATION_PACK/RUNS/B67/A/PROOF/prod_readonly_fallback_match_report.json --out-md REHYDRATION_PACK/RUNS/B67/A/PROOF/prod_readonly_fallback_match_report.md
```
