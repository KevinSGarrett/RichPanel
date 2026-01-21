# Shadow Mode Order Status Runbook

## Purpose
Validate Order Status automation against real Richpanel + Shopify data in **read-only** shadow mode, with PII-safe JSON artifacts.

## DO NOT RUN WITHOUT READ-ONLY GUARDS
This script **must** run with explicit read-only flags. It will refuse to start otherwise.

## Required Environment Variables
Set these **before** running the script:

- `RICHPANEL_READ_ONLY=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `RICHANEL_ENV=staging` or `RICHANEL_ENV=prod` (required; script will set `RICHPANEL_ENV` to match)
- `MW_ALLOW_NETWORK_READS=true` (enables read-only Shopify + Richpanel reads)

## Optional Environment Variables
Use these only if you need LLM evidence or non-default secrets:

- `RICHPANEL_OUTBOUND_ENABLED=true` (only if you need OpenAI routing/rewrites)
- `OPENAI_REPLY_REWRITE_ENABLED=true`
- `OPENAI_ALLOW_NETWORK=true`
- `OPENAI_API_KEY_SECRET_ID=rp-mw/<env>/openai/api_key` (if non-default)
- `SHOPIFY_SHOP_DOMAIN=<your-shop>.myshopify.com`
- `SHOPIFY_ACCESS_TOKEN_SECRET_ID=rp-mw/<env>/shopify/admin_api_token`

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
