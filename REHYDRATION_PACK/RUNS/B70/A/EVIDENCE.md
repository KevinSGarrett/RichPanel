# B70 Agent A Evidence

## Commands Run (PII-safe)

```powershell
cd C:\RichPanel_GIT
aws sso login --profile rp-admin-dev
$env:AWS_PROFILE = "rp-admin-dev"
python scripts\secrets_preflight.py --env dev --region us-east-2 --out REHYDRATION_PACK\RUNS\B70\A\PROOF\secrets_preflight_dev.json
aws sso login --profile rp-admin-prod
$env:AWS_PROFILE = "rp-admin-prod"
python scripts\secrets_preflight.py --env prod --region us-east-2 --out REHYDRATION_PACK\RUNS\B70\A\PROOF\secrets_preflight_prod.json
python scripts\sync_bot_agent_secret.py --env prod --region us-east-2
aws secretsmanager list-secrets --region us-east-2 --filters Key=name,Values=rp-mw/prod/richpanel/ --query "SecretList[].Name" --output json
```

## Outputs

- Dev preflight JSON: `REHYDRATION_PACK/RUNS/B70/A/PROOF/secrets_preflight_dev.json` (PASS)
- Prod preflight JSON: `REHYDRATION_PACK/RUNS/B70/A/PROOF/secrets_preflight_prod.json` (FAIL: missing `rp-mw/prod/richpanel/bot_agent_id`)

## Notes
- No secret values were printed; output contains only existence/readability flags and error class names.
- Preflight checks **do not** validate external API tokens (no HTTP 200 probe); they only verify Secrets Manager/SSM existence + read access.
- `sync_bot_agent_secret.py` failed because `RICHPANEL_BOT_AGENT_ID` is not set on the prod worker Lambda.
- Prod secrets list shows only `rp-mw/prod/richpanel/api_key` and `rp-mw/prod/richpanel/webhook_token` (bot agent id secret missing).