# Order Status — Prod Cutover Runbook

## Scope
Single-source runbook for enabling Order Status automation in **PROD** with a safe canary and rollback.
No Shopify test orders and no customer contact from prod.

## Accounts and region
- **DEV**: 151124909266 (`rp-admin-dev`) — `us-east-2`
- **PROD**: 878145708918 (`rp-admin-prod`) — `us-east-2`

## Prereqs (must be true before cutover)
- AWS access to PROD with `rp-admin-prod` in `us-east-2`.
- Secrets present in PROD:
  - `rp-mw/prod/richpanel/api_key`
  - `rp-mw/prod/richpanel/webhook_token`
  - `rp-mw/prod/richpanel/bot_agent_id`
  - `rp-mw/prod/openai/api_key`
  - `rp-mw/prod/shopify/admin_api_token`
- Richpanel bot agent created; bot id stored in Secrets Manager.
- Prod HTTP target endpoint URL + auth header are configured in Richpanel.
- Order Status automation rule is **paused** before starting.

## Cutover steps (in order)
1) **Verify preflight is green**
   - Run:
     - `python scripts/order_status_preflight_check.py --env prod --aws-profile rp-admin-prod --out-json REHYDRATION_PACK/RUNS/B72/A/PROOF/order_status_preflight_prod.json --out-md REHYDRATION_PACK/RUNS/B72/A/PROOF/order_status_preflight_prod.md`
   - Confirm `overall_status=PASS` and `bot_agent_id_secret_present=true`.
2) **Verify Richpanel HTTP target**
   - Confirm endpoint URL and auth header match the approved prod target.
   - Capture a PII-safe screenshot or redacted config snippet.
3) **Enable automation rule**
   - Unpause the Order Status automation rule in Richpanel.
4) **Canary (outbound still disabled)**
   - Keep outbound flag **disabled** (no customer contact).
   - Send a single internal test email to trigger the workflow.
   - Verify Lambda logs show the ticket was processed.
   - Confirm no customer email was sent.
5) **Enable outbound flag (only after canary success)**
   - Enable outbound only if canary passed and logs show clean processing.

## Canary procedure (safe)
- Use an internal email address only.
- Confirm:
  - Processing shows up in Lambda logs (PII-safe excerpts only).
  - No customer outbound email was sent.
- If any unexpected outbound behavior occurs, **stop** and proceed to rollback.

## Rollback steps
1) Pause the Order Status automation rule in Richpanel.
2) Set outbound disabled (safety flag back to `false`).
3) Confirm no further Lambda invocations for Order Status.

## Evidence checklist (PII-safe)
- Preflight JSON/MD showing prod green and bot agent id present.
- Screenshot or redacted snippet of prod HTTP target config.
- Log snippet showing canary processing (redact any identifiers).
- Proof of automation rule pause/enable toggles.
- Rollback confirmation (if executed): rule paused + outbound disabled + no new invocations.
