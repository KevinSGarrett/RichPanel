# Evidence — B58/C

## Command (exact)
```powershell
$env:AWS_PROFILE = "rp-admin-prod"
$env:AWS_DEFAULT_REGION = "us-east-2"
$env:AWS_REGION = "us-east-2"
$env:AWS_SDK_LOAD_CONFIG = "1"
$env:RICHPANEL_ENV = "prod"
$env:MW_ALLOW_NETWORK_READS = "true"
$env:RICHPANEL_WRITE_DISABLED = "true"
$env:RICHPANEL_OUTBOUND_ENABLED = "false"
$env:SHOPIFY_OUTBOUND_ENABLED = "true"
$env:SHOPIFY_WRITE_DISABLED = "true"
$env:SHOPIFY_SHOP_DOMAIN = "scentimen-t.myshopify.com"
$env:SHOPIFY_ACCESS_TOKEN_PROFILE = "rp-admin-dev"
$env:SHOPIFY_ACCESS_TOKEN_SECRET_ID = "rp-mw/dev/shopify/admin_api_token"
$env:RICHPANEL_API_KEY_SECRET_ID = "rp-mw/prod/richpanel/api_key"
$env:SHOPIFY_ACCESS_TOKEN_OVERRIDE = ""
$env:RICHPANEL_API_KEY_OVERRIDE = ""

python scripts\live_readonly_shadow_eval.py --ticket-id 94875 --ticket-id 98378 --ticket-id 94874 --ticket-id 95608 --ticket-id 98245 --ticket-id 94872 --ticket-id 84723 --ticket-id 95614 --ticket-id 97493 --ticket-id 97034 --ticket-id 95618 --ticket-id 95693 --ticket-id 95620 --ticket-id 95515 --ticket-id 98371 --ticket-id 95622 --ticket-id 95624 --shopify-probe
```

## Read-only flags used
- `RICHPANEL_ENV=prod`
- `MW_ALLOW_NETWORK_READS=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `RICHPANEL_OUTBOUND_ENABLED=false`
- `SHOPIFY_OUTBOUND_ENABLED=true`
- `SHOPIFY_WRITE_DISABLED=true`
- `SHOPIFY_SHOP_DOMAIN=scentimen-t.myshopify.com`

Secret sourcing (profiles):
- `AWS_PROFILE=rp-admin-prod`
- `SHOPIFY_ACCESS_TOKEN_PROFILE=rp-admin-dev`
- `RICHPANEL_API_KEY_SECRET_ID=rp-mw/prod/richpanel/api_key`
- `SHOPIFY_ACCESS_TOKEN_SECRET_ID=rp-mw/dev/shopify/admin_api_token`

Overrides (secrets, not logged): none (overrides explicitly cleared)

## PII-safe success snippet
```json
"counts": {
  "tickets_evaluated": 17,
  "order_status_like": 0,
  "orders_matched": 16,
  "tracking_present": 11,
  "eta_computed": 16
},
"http_trace_summary": {
  "total_requests": 218,
  "methods": {"GET": 198, "POST": 20},
  "services": {"aws_portal": 2, "aws_secretsmanager": 20, "shopify": 21, "richpanel": 170, "shipstation": 5},
  "aws_operations": {"GetSecretValue": 20},
  "aws_sdk_trace_enabled": true,
  "allowed_methods_only": true
}
```

## Safety proof

### Richpanel client read-only enforcement
```python
READ_ONLY_ENVIRONMENTS = {"prod", "production", "staging"}
```

```python
if (self.read_only or self._writes_disabled()) and method_upper not in {
    "GET",
    "HEAD",
}:
    self._logger.warning("richpanel.write_blocked", ...)
    raise RichpanelWriteDisabledError(
        "Richpanel writes are disabled; request blocked"
    )
```

### Script guardrails (outbound not required)
```python
REQUIRED_FLAGS = {
    "MW_ALLOW_NETWORK_READS": "true",
    "RICHPANEL_WRITE_DISABLED": "true",
}
```

### AWS SDK trace coverage (full network)
- `http_trace_summary.aws_sdk_trace_enabled` is `true`, and `aws_operations` lists only `GetSecretValue` (see snippet above).

### No non-GET methods attempted
- `http_trace_summary.allowed_methods_only` is `true`; Richpanel/Shopify/ShipStation are GET-only, AWS POSTs are limited to SecretsManager `GetSecretValue` and SSO portal auth.

## PR Gate Evidence
- PR: https://github.com/KevinSGarrett/RichPanel/pull/185
- CI (validate): https://github.com/KevinSGarrett/RichPanel/actions/runs/21346012477
- Codecov: https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/185
- Claude gate: https://github.com/KevinSGarrett/RichPanel/actions/runs/21346016249 (response id `msg_01YHrDRoKUKYshuqqW7yrxoh`)
