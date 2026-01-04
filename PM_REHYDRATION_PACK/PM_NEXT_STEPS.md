# PM Next Steps

Date: 2026-01-03

## Immediate (post baseline — dev/staging green; prod gated)
1. Keep using the standard PR path:
   - `gh pr merge --auto --merge --delete-branch`
2. Use `REHYDRATION_PACK/05_TASK_BOARD.md` as the source of truth for “what next”.
3. Keep evidence links current when claiming “green” (dev/staging deploy + smoke).

## Human inputs that will be needed soon
- AWS account/credentials (or confirm how AWS auth is being handled locally).
- Richpanel API access / auth method.
- Any email provider credentials for sending (if applicable).
- Shopify credentials + mapping confirmations (if Shopify is used).
- ShipStation credentials + mapping confirmations (if ShipStation is used).
- Final confirmation of order status mapping + SLA language used for the “delivery estimate only” messaging.

## Next work focus
- Shopify / ShipStation integration work
- Richpanel UI configuration + operator workflow validation
- Maintain prod gating until explicit go/no-go + evidence capture
