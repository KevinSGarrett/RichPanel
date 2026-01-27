# B60/C Changes

## Metrics + Drift
- Added summary aggregation for match success rate, channel counts, timing, and failure reasons.
- Added schema fingerprinting + drift warnings for ticket snapshots and Shopify summaries.
- Added `--allow-empty-sample` to keep CI runs green when listing endpoints are forbidden.

## CI / Workflow
- Scheduled `shadow_live_readonly_eval.yml` daily (03:00 UTC) alongside manual dispatch.
- Added summary artifact upload (included in existing readonly shadow artifacts).
- Added fallbacks for `PROD_SHOPIFY_SHOP_DOMAIN` and optional `PROD_RICHPANEL_TICKET_IDS`.

## Docs
- Updated the prod read-only shadow runbook with daily artifacts, drift thresholds,
  and response guidance for listing 403s or match failures.
