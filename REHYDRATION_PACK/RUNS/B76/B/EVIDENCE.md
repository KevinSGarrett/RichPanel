# B76/B Evidence (Hard Evidence, PII-safe)

Date: 2026-02-10  
Operator: Cursor (Agent B)

## 1) Required identity commands (executed first)

Command:
```powershell
aws sso login --profile rp-admin-kevin
```
Result: success (SSO login completed).

Command:
```powershell
aws sts get-caller-identity --profile rp-admin-kevin
```
Output:
```json
{
  "UserId": "AROASGL57DTJKBCKXKECG:rp-admin-kevin",
  "Account": "151124909266",
  "Arn": "arn:aws:sts::151124909266:assumed-role/AWSReservedSSO_RP-Admin_65ba0b62bcc9f8ed/rp-admin-kevin"
}
```
Artifact:
- `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/sts_identity_prod.txt`

Observation:
- Command returned DEV account `151124909266`, not expected PROD `878145708918`.

## 2) PROD profile verification (successful)

Command:
```powershell
aws sso login --profile rp-admin-prod
aws sts get-caller-identity --profile rp-admin-prod
```
Output:
```json
{
  "UserId": "AROA4Y5MQEN3E5KRSFG44:rp-deployer-prod",
  "Account": "878145708918",
  "Arn": "arn:aws:sts::878145708918:assumed-role/AWSReservedSSO_RP-Deployer_19cf80c2655853f2/rp-deployer-prod"
}
```

Artifact:
- `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/sts_identity_prod_verified.txt`

Result:
- PROD account access verified in-region context (`us-east-2`) for account `878145708918`.

## 3) Secrets/SSM preflight in verified PROD account

Command:
```powershell
python scripts/secrets_preflight.py --env prod --profile rp-admin-prod --region us-east-2
```
Artifact:
- `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/secrets_preflight_prod.txt`

Key output facts:
- `overall_status=PASS`
- `account_preflight.ok=true` with expected account `878145708918`
- Required secrets exist/readable:
  - `rp-mw/prod/richpanel/api_key`
  - `rp-mw/prod/openai/api_key`
  - `rp-mw/prod/richpanel/webhook_token`
  - `rp-mw/prod/shopify/admin_api_token`
  - `rp-mw/prod/richpanel/bot_agent_id`
- Required SSM kill switches exist/readable:
  - `/rp-mw/prod/safe_mode`
  - `/rp-mw/prod/automation_enabled`

## 4) Bot agent preflight outputs in verified PROD account (JSON + MD)

Command:
```powershell
python scripts/order_status_preflight_check.py --env prod --aws-profile rp-admin-prod --shop-domain scentimen-t.myshopify.com --out-json REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.json --out-md REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.md
```
Artifacts:
- `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.json`
- `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.md`

Key output facts:
- `overall_status=FAIL`
- `bot_agent_id_secret=PASS` (`present (rp-mw/prod/richpanel/bot_agent_id)`)
- `richpanel_api=PASS (200)`
- `shopify_token=PASS (200)`
- `shopify_graphql=PASS (200)`
- `shopify_token_refresh_last_success=PASS`
- Remaining failure is `required_env` (local preflight runtime env vars not set for this invocation), not a missing bot-agent secret and not an account mismatch.
