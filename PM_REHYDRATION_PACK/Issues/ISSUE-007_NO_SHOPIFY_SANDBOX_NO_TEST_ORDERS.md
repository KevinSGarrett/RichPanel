# ISSUE-007 — No Shopify sandbox / no test orders

## Summary
Shopify does not provide a sandbox in this environment, and creating test orders is not permitted.
Validation must rely on:

- Prod shadow validation (read-only) to prove matching, tracking, and ETA extraction.
- Dev sandbox E2E to prove inbound webhook handling, outbound send-message behavior,
  and ticket state transitions using sandbox Richpanel only.

## Constraints
- No Shopify test orders.
- No prod outbound messages to customers.
- All proof artifacts must be PII-safe.

## Implications
- All Shopify validation in prod is read-only.
- Dev E2E focuses on workflow + side effects in Richpanel sandbox only.
