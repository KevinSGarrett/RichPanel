# B68 — Agent B Changes

- Added Shopify health check script with JSON proof output: `scripts/shopify_health_check.py`.
- Updated Richpanel Retry-After unit test to assert `Retry-After: 7`: `scripts/test_richpanel_client.py`.
- CDK updates for Shopify refresh in dev and secret access grants: `infra/cdk/lib/richpanel-middleware-stack.ts`.
- Added Shopify refresh token secret support (optional) for rotating tokens: `backend/src/integrations/shopify/client.py`.
- Added JSON parsing for Shopify client id/secret and redacted refresh error logging.
- Fixed Shopify client tests for refresh-token lookup behavior.
- Added Shopify client tests for refresh error parsing and secret field extraction.
- Docs clarified for single live Shopify store (read-only): `docs/08_Engineering/Secrets_and_Environments.md`.
