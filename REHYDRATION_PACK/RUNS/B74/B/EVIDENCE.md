# B74 — Evidence

## AWS caller identity (DEV)
- Command: `aws sts get-caller-identity --profile rp-admin-kevin`
- Account id: `151124909266`

## AWS caller identity (PROD)
- Command: `aws sts get-caller-identity --profile rp-admin-prod`
- Account id: `878145708918`

## Secrets checked (names only)
- DEV:
  - `rp-mw/dev/shopify/admin_api_token`
  - `rp-mw/dev/shopify/client_id`
  - `rp-mw/dev/shopify/client_secret`
  - `rp-mw/dev/shopify/refresh_token` (**access denied** in preflight)
- PROD:
  - `rp-mw/prod/shopify/admin_api_token`
  - `rp-mw/prod/shopify/client_id`
  - `rp-mw/prod/shopify/client_secret`
  - `rp-mw/prod/shopify/refresh_token` (**missing** in preflight)

## Secrets preflight proof (PII-safe)
- DEV: `REHYDRATION_PACK/RUNS/B74/B/PROOF/secrets_preflight_dev.json`
- PROD: `REHYDRATION_PACK/RUNS/B74/B/PROOF/secrets_preflight_prod.json`

Preflight excerpt (DEV):
```text
overall_status=FAIL
error=ForbiddenException (GetRoleCredentials: No access)
```

Preflight excerpt (PROD):
```text
overall_status=FAIL
missing_secret=rp-mw/prod/shopify/refresh_token
```

## Shopify token health check proof (PII-safe)
- DEV (run 1): `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_dev_run1.json`
- DEV (run 2): `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_dev_run2.json`
- DEV (run 3): `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_dev_run3.json`
- DEV (latest): `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_dev.json`
- PROD (run 1): `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_prod_run1.json`
- PROD (run 2): `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_prod_run2.json`
- PROD (run 3): `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_prod_run3.json`
- PROD (latest): `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_prod.json`

Proof excerpt (DEV run 3):
```text
status=PASS
health_check.status_code=200
aws_account_id=151124909266
```

Proof excerpt (PROD run 3):
```text
status=PASS
health_check.status_code=200
aws_account_id=878145708918
```
