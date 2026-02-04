# B69 — Agent B Evidence

All evidence is PII-safe. Tokens and secret values are never logged.

## Commands Run

### 2026-02-04 — Shopify health check (prod PASS, live store)
Command:
```
python scripts\shopify_health_check.py --env prod --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --out-json REHYDRATION_PACK\RUNS\B69\B\PROOF\shopify_health_check_prod.json --json --verbose
```
Result summary:
- status: `PASS`
- status_code: `200`
- output: `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_prod.json`

### 2026-02-04 — Shopify health check (invalid token, live store)
Command:
```
python scripts\shopify_health_check.py --env prod --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --out-json REHYDRATION_PACK\RUNS\B69\B\PROOF\shopify_health_check_invalid.json --json --verbose
```
Result summary:
- status: `FAIL_INVALID_TOKEN`
- status_code: `401`
- output: `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_invalid.json`

### 2026-02-04 — Shopify health check (dry-run, local)
Command:
```
python scripts\shopify_health_check.py --refresh-dry-run --json --out-json REHYDRATION_PACK\RUNS\B69\B\PROOF\shopify_health_check_dry_run.json --verbose
```
Result summary:
- status: `DRY_RUN`
- output: `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_dry_run.json`

### 2026-02-04 — Shopify health check unit tests
Command:
```
python -m pytest scripts\test_shopify_health_check.py
```
Result:
```
8 passed in 0.34s
```

### 2026-02-04 — Shopify refresh behavior unit tests (targeted)
Command:
```
python -m pytest scripts\test_shopify_client.py -k "refresh_access_token_returns_false_without_refresh_token or refresh_access_token_client_credentials or refresh_error_includes_error_code"
```
Result:
```
3 passed, 64 deselected in 0.27s
```

### 2026-02-04 — Shopify forbidden-status coverage test
Command:
```
python -m pytest scripts\test_shopify_client.py -k "request_logs_forbidden_status"
```
Result:
```
1 passed, 67 deselected in 0.22s
```

## Proof Artifacts
- `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_prod.json`
- `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_invalid.json`
- `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_dry_run.json`

## Sample Outputs (PII-safe)

### Dry-run output (B69)
```
{
  "status": "DRY_RUN",
  "health_check": {
    "dry_run": true,
    "reason": "secret_lookup_failed",
    "status_code": 0,
    "url": "https://example.myshopify.com/admin/api/2024-01/shop.json"
  },
  "refresh_mode": "none",
  "can_refresh": false
}
```

### PASS sample (B69)
Source: `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_prod.json`
```
{
  "status": "PASS",
  "health_check": {
    "status_code": 200,
    "url": "https://scentimen-t.myshopify.com/admin/api/2024-01/shop.json"
  },
  "token_type": "offline"
}
```

### FAIL sample (B69 invalid token)
Source: `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_invalid.json`
```
{
  "status": "FAIL_INVALID_TOKEN",
  "health_check": {
    "status_code": 401,
    "body_excerpt": "{\"errors\":\"[API] Invalid API key or access token (unrecognized login or wrong password)\"}"
  },
  "token_type": "unknown"
}
```
