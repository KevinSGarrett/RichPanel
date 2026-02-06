# Shopify Token Health Summary (B72)

Generated from:
- REHYDRATION_PACK/RUNS/B72/B/PROOF/secrets_preflight_dev.json
- REHYDRATION_PACK/RUNS/B72/B/PROOF/secrets_preflight_prod.json
- REHYDRATION_PACK/RUNS/B72/B/PROOF/shopify_health_dev.json
- REHYDRATION_PACK/RUNS/B72/B/PROOF/shopify_health_prod.json

## DEV
- Secrets preflight: PASS (aws_account_id=151124909266).
- Token prefix classification: offline => shpat_ (from token_type=offline).
- Token format: raw (plain token string).
- can_refresh: false (has_refresh_token=false).
- refresh_enabled: false.
- health.ok: true (status=PASS; status_code=200).

## PROD
- Secrets preflight: PASS (aws_account_id=878145708918).
- Token prefix classification: offline => shpat_ (from token_type=offline).
- Token format: json.
- can_refresh: false (has_refresh_token=false).
- refresh_enabled: false.
- health.ok: true (status=PASS; status_code=200).

## Evidence notes
- DEV + PROD tokens are offline (non-expiring by design) and both return HTTP 200 for the configured shop domain.
- PROD token is stored as JSON without a refresh token; DEV token is stored as a raw string.
