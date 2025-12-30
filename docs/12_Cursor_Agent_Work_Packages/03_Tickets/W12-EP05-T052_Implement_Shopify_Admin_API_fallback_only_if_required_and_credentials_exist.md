# W12-EP05-T052 — Implement Shopify Admin API fallback (only if required and credentials exist)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Use Shopify as fallback source of truth if Richpanel order payload lacks tracking fields.

## Context / References
- `docs/05_FAQ_Automation/Order_Status_Automation.md`
- `docs/06_Security_Privacy_Compliance/Vendor_Data_Handling_OpenAI_Richpanel_Shopify.md`

## Dependencies
- W12-EP00-T001

## Implementation steps
1. Confirm credentials and required scopes (read orders/fulfillments).
1. Implement minimal Shopify lookup by order_id/email/phone as allowed.
1. Use only for deterministic-match path; never guess.
1. Add rate limiting and caching.

## Acceptance criteria
- [ ] Fallback works only when deterministic match is established.
- [ ] If fallback unavailable, system asks for order# and routes.

## Test plan
- (TBD)

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Do not send Shopify raw payloads to OpenAI.
- Redact order/customer identifiers from logs.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
