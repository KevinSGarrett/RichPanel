# Shadow Mode Order Status Runbook

## Purpose
Validate Order Status automation against real Richpanel + Shopify data in **read-only** shadow mode, with PII-safe JSON artifacts.

## DO NOT RUN WITHOUT READ-ONLY GUARDS
This script **must** run with explicit read-only flags. It will refuse to start otherwise.

## Required Environment Variables
Set these **before** running the script:

- `RICHPANEL_READ_ONLY=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `RICHPANEL_ENV=staging` or `RICHPANEL_ENV=prod` (required)
- `MW_ALLOW_NETWORK_READS=true` (enables read-only Shopify + Richpanel reads)

## Optional Environment Variables
Use these only if you need LLM evidence or non-default secrets:

- `MW_OPENAI_ROUTING_ENABLED=true`
- `MW_OPENAI_INTENT_ENABLED=true`
- `MW_OPENAI_REWRITE_ENABLED=true`
- `MW_OPENAI_SHADOW_ENABLED=true` (allows OpenAI in read-only shadow)
- `OPENAI_ALLOW_NETWORK=true`
- `OPENAI_API_KEY_SECRET_ID=rp-mw/<env>/openai/api_key` (if non-default)
- `SHOPIFY_SHOP_DOMAIN=<your-shop>.myshopify.com`
- `SHOPIFY_ACCESS_TOKEN_SECRET_ID=rp-mw/<env>/shopify/admin_api_token`

## Shopify Token Health Check (Order Status)
Run these before shadow-mode validation to confirm Shopify auth health and AWS account alignment.

### AWS Account Preflight
Verify you are in the intended AWS account before running any health checks:
- **DEV / sandbox** account: `151124909266`
- **PROD / live** account: `878145708918`

Command:
```
aws sts get-caller-identity
```

If Cursor cannot load AWS credentials, set a profile explicitly and retry:
```
AWS_SDK_LOAD_CONFIG=1 AWS_PROFILE=<your-dev-or-prod-profile> aws sts get-caller-identity
```

### Health Check Commands
Use the read-only health check script (outputs JSON diagnostics):

DEV (run in account `151124909266`):
```
python scripts/shopify_token_health_check.py --env dev --include-aws-account-id
```

PROD (run in account `878145708918`):
```
python scripts/shopify_token_health_check.py --env prod --include-aws-account-id
```

Healthy output cues:
- `"status": "PASS"` with a 2xx `health_check.status_code`
- `"can_refresh": true` only when refresh metadata exists (client id/secret + refresh token)

If token is invalid:
- Expect `"status": "FAIL_INVALID_TOKEN"` and `health_check.status_code=401`
- Action: confirm Secrets Manager values for `rp-mw/<env>/shopify/admin_api_token`, plus `client_id`/`client_secret` if refresh is expected.

## Run For One Ticket
Example:

```
python scripts/shadow_order_status.py \
  --ticket-id 123456 \
  --out artifacts/shadow_order_status_123456.json \
  --max-tickets 1 \
  --confirm-live-readonly
```

## Output Handling (PII-Safe Proof)
- Output JSON is redacted:
  - Email is hashed.
  - Name, address, and phone are redacted.
  - Tracking number is last-4 only.
- A read-only HTTP trace is also written under `artifacts/shadow_order_status/` and included in the JSON output (`http_trace_path`).
- Store artifacts under `artifacts/` or a secure internal storage bucket.
- Do **not** paste artifacts into public channels or commit them to git.
- If sharing, provide only the redacted JSON and keep the file permissions restricted.

## Warnings
- **DO NOT RUN WITHOUT READ-ONLY GUARDS.**
- **Do not run in CI** (live keys are prohibited in CI).
- Never add or expose raw ticket payloads in logs or output.
- OpenAI calls only occur when `MW_OPENAI_*_ENABLED=true`, `OPENAI_ALLOW_NETWORK=true`,
  and read-only guards are set. Enable `MW_OPENAI_SHADOW_ENABLED=true` to explicitly
  allow OpenAI in read-only shadow runs when outbound is disabled.