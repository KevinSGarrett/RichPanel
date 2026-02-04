# B69 — Agent B Changes

- Prevent Shopify refresh from overwriting stable admin API tokens by requiring a refresh token.
- Add structured health check status classification and compact `--json` output mode.
- Default prod workflows to AWS Secrets Manager (OIDC) for Shopify tokens.
- Document refresh-token requirement and CI token sourcing strategy.
- Update Shopify unit tests for refresh behavior and status mapping.
