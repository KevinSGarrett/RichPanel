# AWS Account Split

## Accounts
- **DEV**: `151124909266`
  - Owns DEV Secrets Manager + SSM parameters
  - API Gateway: `rp-mw-dev-ingress` (`pj41mkbj38`)
- **PROD**: `878145708918`
  - Owns PROD secrets and token refresh infrastructure

## Key rules
- Secrets are **not shared** across accounts.
- Always verify the active AWS account before running DEV/PROD scripts.
- Use the preflight helper to fail fast on wrong account or missing secrets:
```
python scripts/secrets_preflight.py --env dev --expect-account-id 151124909266
python scripts/secrets_preflight.py --env prod --expect-account-id 878145708918
```
