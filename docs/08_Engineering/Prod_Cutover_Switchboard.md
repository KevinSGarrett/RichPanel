# PROD Cutover Switchboard

Last updated: 2026-02-10  
Status: Canonical

## Purpose

Single operator runbook for production cutover with:
- repeatable commands,
- safe-by-default operation,
- and rollback in under 60 seconds.

This runbook does not enable PROD outbound by default.

## Guardrails (must follow)

- Account separation:
  - DEV account: `151124909266`
  - PROD account: `878145708918`
- Region: `us-east-2`
- Do not run write/outbound steps unless explicitly approved for cutover.
- `safe_mode` is authoritative: when `safe_mode=true`, automation must stop regardless of Lambda env vars.

## 0) Identity Gate (run before any AWS operation)

```powershell
aws sso login --profile rp-admin-kevin
aws sts get-caller-identity --profile rp-admin-kevin --output json
```

Expected for PROD operations:
- `Account` must be `878145708918`

If the account is not PROD, stop and fix profile/account access before proceeding.

## 1) Read Current State (no writes)

### 1A) CloudFormation stack outputs + nested stacks

```powershell
$PROFILE="rp-admin-prod"
$REGION="us-east-2"
$STACK="RichpanelMiddleware-prod"

aws cloudformation describe-stacks `
  --stack-name $STACK `
  --region $REGION `
  --profile $PROFILE `
  --output json

aws cloudformation list-stack-resources `
  --stack-name $STACK `
  --region $REGION `
  --profile $PROFILE `
  --output table

# Nested stacks
$NESTED = aws cloudformation list-stack-resources `
  --stack-name $STACK `
  --region $REGION `
  --profile $PROFILE `
  --query "StackResourceSummaries[?ResourceType=='AWS::CloudFormation::Stack'].PhysicalResourceId" `
  --output text

foreach ($NS in $NESTED -split "\s+") {
  if ($NS) {
    aws cloudformation describe-stacks --stack-name $NS --region $REGION --profile $PROFILE --output json
  }
}
```

### 1B) Lambda function name(s) for middleware handler

```powershell
$PROFILE="rp-admin-prod"
$REGION="us-east-2"
$STACK="RichpanelMiddleware-prod"

aws cloudformation list-stack-resources `
  --stack-name $STACK `
  --region $REGION `
  --profile $PROFILE `
  --query "StackResourceSummaries[?ResourceType=='AWS::Lambda::Function'].[LogicalResourceId,PhysicalResourceId]" `
  --output table
```

### 1C) Read Lambda safety env vars

```powershell
$PROFILE="rp-admin-prod"
$REGION="us-east-2"
$FUNCTION_NAME="rp-mw-prod-worker"

aws lambda get-function-configuration `
  --function-name $FUNCTION_NAME `
  --region $REGION `
  --profile $PROFILE `
  --query "Environment.Variables.{MW_ENV:MW_ENV,RICHPANEL_OUTBOUND_ENABLED:RICHPANEL_OUTBOUND_ENABLED,RICHPANEL_WRITE_DISABLED:RICHPANEL_WRITE_DISABLED,RICHPANEL_READ_ONLY:RICHPANEL_READ_ONLY,MW_PROD_WRITES_ACK:MW_PROD_WRITES_ACK,MW_PROD_OUTBOUND_ALLOWLIST_EMAILS:MW_PROD_OUTBOUND_ALLOWLIST_EMAILS}" `
  --output json
```

### 1D) Resolve kill-switch parameter namespace

Use requested namespace first; if not found, fall back to deployed namespace from stack outputs.

```powershell
$PROFILE="rp-admin-prod"
$REGION="us-east-2"

aws ssm get-parameters `
  --names /richpanel-middleware/prod/safe_mode /richpanel-middleware/prod/automation_enabled `
  --region $REGION `
  --profile $PROFILE `
  --output table

# Fallback currently used in deployed stack/runbooks (if above shows NotFound):
aws ssm get-parameters `
  --names /rp-mw/prod/safe_mode /rp-mw/prod/automation_enabled `
  --region $REGION `
  --profile $PROFILE `
  --output table
```

## 2) CANARY ON (safe + allowlisted)

Goal:
- automation enabled,
- writes enabled,
- outbound enabled,
- allowlist restricted to internal emails only.

### 2A) Set Lambda env vars for canary

```powershell
$PROFILE="rp-admin-prod"
$REGION="us-east-2"
$FUNCTION_NAME="rp-mw-prod-worker"
$ALLOWLIST="owner1@company.com,owner2@company.com"

aws lambda get-function-configuration `
  --function-name $FUNCTION_NAME `
  --region $REGION `
  --profile $PROFILE `
  --query "Environment.Variables" `
  --output json > .tmp.lambda_env.json

python -c "import json; p='.tmp.lambda_env.json'; d=json.load(open(p)); d.update({'MW_ENV':'prod','RICHPANEL_OUTBOUND_ENABLED':'true','RICHPANEL_WRITE_DISABLED':'false','RICHPANEL_READ_ONLY':'false','MW_PROD_WRITES_ACK':'I_UNDERSTAND_PROD_WRITES','MW_PROD_OUTBOUND_ALLOWLIST_EMAILS':'owner1@company.com,owner2@company.com'}); json.dump({'Variables':d}, open('.tmp.lambda_env_patch.json','w'))"

aws lambda update-function-configuration `
  --function-name $FUNCTION_NAME `
  --region $REGION `
  --profile $PROFILE `
  --environment file://.tmp.lambda_env_patch.json

aws lambda wait function-updated `
  --function-name $FUNCTION_NAME `
  --region $REGION `
  --profile $PROFILE
```

### 2B) Flip SSM kill switches for canary

Use the namespace that exists in your account (resolved in section 1D):

```powershell
$PROFILE="rp-admin-prod"
$REGION="us-east-2"

# Preferred namespace from request:
aws ssm put-parameter --name /richpanel-middleware/prod/safe_mode --type String --value false --overwrite --region $REGION --profile $PROFILE
aws ssm put-parameter --name /richpanel-middleware/prod/automation_enabled --type String --value true --overwrite --region $REGION --profile $PROFILE

# If your deployed namespace is /rp-mw/prod, use instead:
# aws ssm put-parameter --name /rp-mw/prod/safe_mode --type String --value false --overwrite --region $REGION --profile $PROFILE
# aws ssm put-parameter --name /rp-mw/prod/automation_enabled --type String --value true --overwrite --region $REGION --profile $PROFILE
```

### 2C) Post-change verification

```powershell
aws ssm get-parameters --names /richpanel-middleware/prod/safe_mode /richpanel-middleware/prod/automation_enabled --region us-east-2 --profile rp-admin-prod --output table

aws lambda get-function-configuration `
  --function-name rp-mw-prod-worker `
  --region us-east-2 `
  --profile rp-admin-prod `
  --query "Environment.Variables.{MW_ENV:MW_ENV,RICHPANEL_OUTBOUND_ENABLED:RICHPANEL_OUTBOUND_ENABLED,RICHPANEL_WRITE_DISABLED:RICHPANEL_WRITE_DISABLED,RICHPANEL_READ_ONLY:RICHPANEL_READ_ONLY,MW_PROD_WRITES_ACK:MW_PROD_WRITES_ACK,MW_PROD_OUTBOUND_ALLOWLIST_EMAILS:MW_PROD_OUTBOUND_ALLOWLIST_EMAILS}" `
  --output json
```

## 3) FULL ON (after canary success only)

Action: remove/empty allowlist while keeping explicit prod-write ack.

```powershell
$PROFILE="rp-admin-prod"
$REGION="us-east-2"
$FUNCTION_NAME="rp-mw-prod-worker"

aws lambda get-function-configuration `
  --function-name $FUNCTION_NAME `
  --region $REGION `
  --profile $PROFILE `
  --query "Environment.Variables" `
  --output json > .tmp.lambda_env.json

python -c "import json; p='.tmp.lambda_env.json'; d=json.load(open(p)); d.update({'MW_ENV':'prod','RICHPANEL_OUTBOUND_ENABLED':'true','RICHPANEL_WRITE_DISABLED':'false','RICHPANEL_READ_ONLY':'false','MW_PROD_WRITES_ACK':'I_UNDERSTAND_PROD_WRITES','MW_PROD_OUTBOUND_ALLOWLIST_EMAILS':''}); json.dump({'Variables':d}, open('.tmp.lambda_env_patch.json','w'))"

aws lambda update-function-configuration `
  --function-name $FUNCTION_NAME `
  --region $REGION `
  --profile $PROFILE `
  --environment file://.tmp.lambda_env_patch.json

aws lambda wait function-updated `
  --function-name $FUNCTION_NAME `
  --region $REGION `
  --profile $PROFILE
```

## 4) Rollback in <60 seconds

### Preferred single-command rollback (authoritative kill switch)

```powershell
aws ssm put-parameter --name /richpanel-middleware/prod/safe_mode --type String --value true --overwrite --region us-east-2 --profile rp-admin-prod
```

If your deployed namespace is `/rp-mw/prod`, use:

```powershell
aws ssm put-parameter --name /rp-mw/prod/safe_mode --type String --value true --overwrite --region us-east-2 --profile rp-admin-prod
```

### Secondary rollback command (Lambda outbound hard stop)

If SSM API is unavailable, also force env outbound off:

```powershell
aws lambda get-function-configuration --function-name rp-mw-prod-worker --region us-east-2 --profile rp-admin-prod --query "Environment.Variables" --output json > .tmp.lambda_env.json
python -c "import json; d=json.load(open('.tmp.lambda_env.json')); d['RICHPANEL_OUTBOUND_ENABLED']='false'; json.dump({'Variables':d}, open('.tmp.lambda_env_patch.json','w'))"
aws lambda update-function-configuration --function-name rp-mw-prod-worker --region us-east-2 --profile rp-admin-prod --environment file://.tmp.lambda_env_patch.json
```

## 5) Evidence to Capture (mandatory)

For each state transition (read-state, canary-on, full-on, rollback), capture:

- SSM truth:
  ```powershell
  aws ssm get-parameters --names /richpanel-middleware/prod/safe_mode /richpanel-middleware/prod/automation_enabled --region us-east-2 --profile rp-admin-prod --output table
  ```
- Lambda env truth:
  ```powershell
  aws lambda get-function-configuration --function-name rp-mw-prod-worker --region us-east-2 --profile rp-admin-prod --query "Environment.Variables.{MW_ENV:MW_ENV,RICHPANEL_OUTBOUND_ENABLED:RICHPANEL_OUTBOUND_ENABLED,RICHPANEL_WRITE_DISABLED:RICHPANEL_WRITE_DISABLED,RICHPANEL_READ_ONLY:RICHPANEL_READ_ONLY,MW_PROD_WRITES_ACK:MW_PROD_WRITES_ACK,MW_PROD_OUTBOUND_ALLOWLIST_EMAILS:MW_PROD_OUTBOUND_ALLOWLIST_EMAILS}" --output json
  ```
- CloudWatch proof that `safe_mode` was evaluated:
  ```powershell
  aws logs tail /aws/lambda/rp-mw-prod-worker --since 15m --profile rp-admin-prod --region us-east-2
  ```
- Account proof:
  ```powershell
  aws sts get-caller-identity --profile rp-admin-prod --output json
  ```

## 6) Preflight Commands (required before cutover)

```powershell
# Secrets + SSM existence preflight
python scripts/secrets_preflight.py --env prod --profile rp-admin-prod --region us-east-2

# Bot agent preflight
python scripts/order_status_preflight_check.py `
  --env prod `
  --aws-profile rp-admin-prod `
  --shop-domain scentimen-t.myshopify.com `
  --out-json REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.json `
  --out-md REHYDRATION_PACK/RUNS/B76/B/ARTIFACTS/preflight_prod/preflight_prod.md
```

## 7) Safety Notes

- Keep `safe_mode=true` until a human cutover approval is recorded.
- Never remove the `MW_PROD_WRITES_ACK` requirement for PROD.
- Do not run canary/full-on commands from DEV account.
