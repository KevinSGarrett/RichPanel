# Shopify Seeding Execution Evidence

## GitHub Secrets Configured
- `DEV_SHOPIFY_ADMIN_API_TOKEN` (masked in run logs)
- `STAGING_SHOPIFY_ADMIN_API_TOKEN` (masked in run logs)
- `PROD_SHOPIFY_ADMIN_API_TOKEN` (masked in run logs)

## Seeding Runs (workflow_dispatch on PR branch)
- Dev: https://github.com/KevinSGarrett/RichPanel/actions/runs/21128649036 — **Success**
- Staging: https://github.com/KevinSGarrett/RichPanel/actions/runs/21128661179 — **Success**
- Prod: https://github.com/KevinSGarrett/RichPanel/actions/runs/21128671471 — **Success**

## Evidence from logs
Commands used:
```
gh workflow run seed-secrets.yml --ref run/RUN_20260119_0643Z_claude_gate_real -f environment=dev
gh workflow run seed-secrets.yml --ref run/RUN_20260119_0643Z_claude_gate_real -f environment=staging
gh workflow run seed-secrets.yml --ref run/RUN_20260119_0643Z_claude_gate_real -f environment=prod
gh run view <run-id> --log
```

Log excerpts showing Shopify secret upserts:
- Dev run (21128649036):
  - `[OK] Updated rp-mw/dev/shopify/admin_api_token`
- Staging run (21128661179):
  - `[OK] Updated rp-mw/staging/shopify/admin_api_token`
- Prod run (21128671471):
  - `[OK] Updated rp-mw/prod/shopify/admin_api_token`

Notes:
- Richpanel/OpenAI secrets were skipped in staging/prod when missing, as expected.
