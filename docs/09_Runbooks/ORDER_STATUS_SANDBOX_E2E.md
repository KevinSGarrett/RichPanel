# Order Status Sandbox E2E (DEV)

## Purpose
Run the DEV sandbox end-to-end proof for order-status automation, including:
- operator reply via `/send-message`
- email-channel verification
- follow-up routing safety (no repeat auto-reply)

## Preconditions
- AWS SSO authenticated for DEV.
- Confirm DEV account: `151124909266`.
- Do not run any PROD webhooks.

## Commands (DEV)
```powershell
# Auth (DEV account)
aws sso login --profile rp-admin-dev-admin
aws sts get-caller-identity --profile rp-admin-dev-admin

# Preflight (read-only)
$env:MW_ALLOW_NETWORK_READS="true"
$env:RICHPANEL_READ_ONLY="true"
$env:RICHPANEL_WRITE_DISABLED="true"
$env:RICHPANEL_OUTBOUND_ENABLED="false"
$env:SHOPIFY_OUTBOUND_ENABLED="true"
$env:SHOPIFY_WRITE_DISABLED="true"
$env:SHOPIFY_SHOP_DOMAIN="scentimen-t.myshopify.com"
python scripts\order_status_preflight_check.py --env dev --aws-profile rp-admin-dev-admin `
  --out-json REHYDRATION_PACK\RUNS\B73\A\PROOF\preflight_dev.json

# E2E proof (operator reply + email channel + /send-message)
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --profile rp-admin-dev-admin `
  --ticket-number 1260 --scenario order_status `
  --require-operator-reply --require-email-channel `
  --require-send-message-path --require-send-message-used `
  --proof-path REHYDRATION_PACK\RUNS\B73\A\PROOF\dev_e2e_smoke.json

# Follow-up routing safety (same harness, second DEV ticket)
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --profile rp-admin-dev-admin `
  --ticket-number 1260 --scenario order_status `
  --require-operator-reply --require-email-channel `
  --require-send-message-path --require-send-message-used `
  --simulate-followup `
  --proof-path REHYDRATION_PACK\RUNS\B73\A\PROOF\followup_smoke.json
```

## Artifacts
- `REHYDRATION_PACK/RUNS/B73/A/PROOF/preflight_dev.json`
- `REHYDRATION_PACK/RUNS/B73/A/PROOF/dev_e2e_smoke.json`
- `REHYDRATION_PACK/RUNS/B73/A/PROOF/dev_e2e_smoke.md`
- `REHYDRATION_PACK/RUNS/B73/A/PROOF/followup_smoke.json`
- `REHYDRATION_PACK/RUNS/B73/A/PROOF/followup_check.md`

## Pass Criteria
- Preflight `overall_status=PASS`.
- `dev_e2e_smoke.json` shows:
  - `proof_fields.ticket_channel=email`
  - `proof_fields.latest_comment_is_operator=true`
  - `proof_fields.outbound_endpoint_used=/send-message`
  - `result.status=PASS`
- Follow-up safety:
  - `followup_reply_sent=false`
  - `followup_routed_support=true`
  - `followup_skip_tags_added` includes `mw-skip-followup-after-auto-reply`
