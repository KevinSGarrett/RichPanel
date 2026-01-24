# B54 C Changes

## Code
- Hardened `scripts/live_readonly_shadow_eval.py` for prod-only runs, sample-size selection, and PII-safe summary outputs with HTTP trace verification.
- Added latest-ticket sampling and sanitized outputs to `scripts/shadow_order_status.py`.
- Redacted error type fields to safe categories in shadow eval outputs.
- Updated shadow eval tests for new CLI flags and redaction behavior.
- Suppressed Claude gate structured parse failures from showing as action required in shadow mode.
- Extracted shared ticket sampling helpers into `scripts/readonly_shadow_utils.py`.
- Centralized `_safe_error` in `scripts/readonly_shadow_utils.py` for reuse.
- Added workflow dispatch for live read-only shadow validation: `.github/workflows/shadow_live_readonly_eval.yml`.
- Hardened workflow inputs (env-bound values + validation) and installed `boto3`.
- Added OIDC-based AWS secret resolution when GH secrets point to secret IDs.
- Added fallback to list recent tickets via `/api/v1/conversations` and `/v1/conversations` when `/v1/tickets` returns 401/403/404.
- Added `use-aws-secrets` workflow input to force AWS Secrets Manager resolution.
- Added `shopify-probe` workflow input and CLI flag for read-only Shopify verification (orders count, best-effort).
- Added GH secret fallback to accept `PROD_SHOPIFY_API_TOKEN` when the admin token secret is unset.
- Shadow eval now extracts the latest customer message from conversation messages for routing.
- Added Shopify order-number fallback using `orders.json?name=` when `GET /orders/{id}` returns 404.
- Enforced Shopify name search with `#` prefix + single encoding; added email/name and email-only identity fallbacks with explicit `order_resolution` telemetry.
- Expanded order-number extraction to scan all comments with prioritized patterns and wrapper awareness.
- Added local env fallbacks for `RP_KEY` and `SHOPIFY_TOKEN` during read-only runs.
- Removed payload-only short-circuit that blocked Shopify lookups when only status was present.
- Persisted `order_resolution` for explicit ticket runs in `scripts/live_readonly_shadow_eval.py`.

## Artifacts
- `REHYDRATION_PACK/RUNS/B54/C/PROOF/live_readonly_shadow_eval_report.md`

## Docs
- Updated `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md` for new report paths and workflow guidance.
