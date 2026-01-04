# Shopify integration skeleton

- **Token location:** Shopify Admin API access token is stored in AWS Secrets Manager at `rp-mw/<env>/shopify/access_token`. The `<env>` segment follows the same resolution as other middleware secrets: `RICHPANEL_ENV` → `RICH_PANEL_ENV` → `MW_ENV` → `ENVIRONMENT` → `local`.
- **Client defaults:** `ShopifyClient` is offline-first. Network calls are blocked unless `SHOPIFY_OUTBOUND_ENABLED=true` (or `allow_network=True` when constructing the client). When network is blocked, requests short-circuit with `dry_run=True` and `reason="network_disabled"`.
- **Safety gates:** Even when outbound traffic is enabled, callers must pass the runtime gates `safe_mode` and `automation_enabled` into `ShopifyClient.request(...)`. If either gate is closed, the client returns a dry-run response with `reason` set (e.g., `safe_mode` or `automation_disabled`). Missing secrets also short-circuit with `dry_run=True` so we never emit outbound requests without credentials.
- **Logging posture:** Request/response logs exclude secrets; `X-Shopify-Access-Token` (and Authorization headers) are redacted via `ShopifyClient.redact_headers`.
- **Enabling network safely:** Set `SHOPIFY_OUTBOUND_ENABLED=true` only in controlled environments. Keep `safe_mode` true and/or `automation_enabled` false during dry runs to preserve the no-side-effects posture. Outbound remains subject to the global safe_mode + automation gating even when the flag is set.

