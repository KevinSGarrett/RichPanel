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

## 2) PROD profile access attempt (diagnostic)

Command:
```powershell
aws sso login --profile rp-admin-prod
aws sts get-caller-identity --profile rp-admin-prod
```
Result:
- `aws sso login` completed.
- `aws sts get-caller-identity` failed with:
  - `ForbiddenException: No access`

Artifact:
- `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/sts_identity_prod_profile_attempt.txt`

Diagnosis:
- Blocker is IAM/profile access for PROD credentials from this machine context.

## 3) Secrets/SSM preflight command output

Command:
```powershell
python scripts/secrets_preflight.py --env prod --profile rp-admin-kevin --region us-east-2
```
Artifact:
- `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/secrets_preflight_prod.txt`

Key output facts:
- `account_preflight.ok=false` with `error=account_mismatch`.
- Expected account in output: `878145708918`.
- Actual account in output: `151124909266`.
- Required secret missing in this account context:
  - `rp-mw/prod/richpanel/webhook_token`
  - `rp-mw/prod/richpanel/bot_agent_id`
- Required SSM params not found in this account context:
  - `/rp-mw/prod/safe_mode`
  - `/rp-mw/prod/automation_enabled`

## 4) Bot agent preflight outputs (JSON + MD)

Command:
```powershell
python scripts/order_status_preflight_check.py --env prod --aws-profile rp-admin-kevin --shop-domain scentimen-t.myshopify.com --out-json REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.json --out-md REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.md
```
Artifacts:
- `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.json`
- `REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.md`

Key output facts:
- `overall_status=FAIL`
- `bot_agent_id_secret=FAIL` (`missing_or_unreadable (ResourceNotFoundException)`)
- `richpanel_api=PASS (200)`
- `shopify_token=PASS (200)`
- `shopify_graphql=PASS (200)`

Important scope note:
- These outputs are from account `151124909266` due the identity mismatch and cannot be claimed as final PROD (`878145708918`) proof.

## 5) Smallest fix to unblock true PROD preflight

1. Grant `rp-admin-kevin` access to account `878145708918` in AWS SSO permission set **or** provide a working profile mapped to that account.
2. Re-run exactly:
   - `aws sts get-caller-identity --profile <prod-capable-profile>`
   - `python scripts/secrets_preflight.py --env prod --profile <prod-capable-profile> --region us-east-2`
   - `python scripts/order_status_preflight_check.py --env prod --aws-profile <prod-capable-profile> --shop-domain scentimen-t.myshopify.com --out-json ... --out-md ...`
3. Confirm `Account=878145708918` in evidence before accepting any cutover decision.
