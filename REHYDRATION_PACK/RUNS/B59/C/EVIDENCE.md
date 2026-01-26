# Evidence - B59/C

## Command (exact; ticket IDs redacted)
```powershell
$env:AWS_PROFILE = "rp-admin-prod"
$env:AWS_DEFAULT_REGION = "us-east-2"
$env:AWS_REGION = "us-east-2"
$env:AWS_SDK_LOAD_CONFIG = "1"
$env:RICHPANEL_ENV = "prod"
$env:MW_ALLOW_NETWORK_READS = "true"
$env:RICHPANEL_READ_ONLY = "true"
$env:RICHPANEL_WRITE_DISABLED = "true"
$env:RICHPANEL_OUTBOUND_ENABLED = "false"
$env:SHOPIFY_OUTBOUND_ENABLED = "true"
$env:SHOPIFY_WRITE_DISABLED = "true"
$env:SHOPIFY_SHOP_DOMAIN = "scentimen-t.myshopify.com"
$env:SHOPIFY_ACCESS_TOKEN_OVERRIDE = ""
$env:RICHPANEL_API_KEY_OVERRIDE = ""
$env:SHOPIFY_ACCESS_TOKEN_SECRET_ID = ""
$env:RICHPANEL_API_KEY_SECRET_ID = "rp-mw/prod/richpanel/api_key"

python scripts\live_readonly_shadow_eval.py `
  --ticket-id redacted:788b726ba2a1 `
  --ticket-id redacted:87022f956b30 `
  --ticket-id redacted:1dcfec81d9b0 `
  --ticket-id redacted:85417ff765d1 `
  --ticket-id redacted:6962c808b085 `
  --ticket-id redacted:9c8e254ed441 `
  --ticket-id redacted:d1c30e537502 `
  --ticket-id redacted:b645a23fd354 `
  --ticket-id redacted:871707348a53 `
  --ticket-id redacted:e7cf89bcb59f `
  --ticket-id redacted:2a7ecc5e705d `
  --ticket-id redacted:2a88c7506c07 `
  --ticket-id redacted:72e09b2d31f5 `
  --ticket-id redacted:90064405d18e `
  --ticket-id redacted:4966ad2d08e3 `
  --ticket-id redacted:34de44a65a2f `
  --ticket-id redacted:f9ead722d06e `
  --shopify-probe `
  --shop-domain scentimen-t.myshopify.com
```

Ticket IDs are redacted; hashes correspond to `ticket_id_redacted` in
`artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260126_2030Z.json`.

## Read-only flags used
- `RICHPANEL_ENV=prod`
- `MW_ALLOW_NETWORK_READS=true`
- `RICHPANEL_READ_ONLY=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `RICHPANEL_OUTBOUND_ENABLED=false`
- `SHOPIFY_OUTBOUND_ENABLED=true`
- `SHOPIFY_WRITE_DISABLED=true`
- `SHOPIFY_SHOP_DOMAIN=scentimen-t.myshopify.com`

## PII-safe summary excerpt
```json
"counts": {
  "tickets_requested": 17,
  "tickets_selected": 17,
  "tickets_scanned": 17,
  "order_status_candidates": 1,
  "orders_matched": 17,
  "tracking_found": 11,
  "eta_available": 17,
  "errors": 0
},
"shopify_probe": {
  "enabled": true,
  "status_code": 200,
  "dry_run": false,
  "ok": true
},
"http_trace_summary": {
  "total_requests": 220,
  "methods": {"GET": 198, "POST": 22},
  "services": {"aws_portal": 1, "aws_secretsmanager": 22, "shopify": 21, "richpanel": 170, "shipstation": 6},
  "aws_operations": {"GetSecretValue": 22},
  "aws_sdk_trace_enabled": true,
  "allowed_methods_only": true
}
```

Derived unmatched count: `orders_unmatched = tickets_scanned - orders_matched = 0`.

## Shopify access scopes (prod, read-only GET)
Command (local, token not logged; uses AWS profile + Secrets Manager):
```powershell
python _tmp\verify_shopify_scopes.py
```

Response (scopes only):
```json
{
  "status": 200,
  "scope_count": 5,
  "scopes": [
    "read_all_orders",
    "read_customers",
    "read_fulfillments",
    "read_orders",
    "read_shipping"
  ]
}
```

## Shopify token diagnosis (prod)
### Metadata check (no secret values)
```powershell
aws secretsmanager describe-secret `
  --secret-id rp-mw/prod/shopify/admin_api_token `
  --region us-east-2 `
  --profile rp-admin-prod
```

Description (from Secrets Manager):
```
Shopify Admin API token (prod) - placeholder; replace with real token from Shopify custom app
```

### Secret metadata (proof of update)
```json
{
  "LastChangedDate": "2026-01-26T14:27:16.713000-06:00",
  "VersionIdsToStages": {
    "967016f8-5763-48aa-9611-d2936e2a1fd3": ["AWSPREVIOUS"],
    "d27a6f1f-d9a3-4390-b488-78946100c140": ["AWSCURRENT"]
  }
}
```

### Fix applied
- Secret updated to align with the active Shopify token (single-store setup).
