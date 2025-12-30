# W12-EP05-T050 — Implement deterministic order linkage lookup using Richpanel order endpoints

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Determine whether an inbound ticket is linked to an order; enforce deterministic match gating.

## Context / References
- `docs/05_FAQ_Automation/Order_Status_Automation.md`
- `docs/03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md`

## Dependencies
- W12-EP04-T042

## Implementation steps
1. Call `GET /v1/order/{conversationId}` and treat `{}` as no link.
1. If linked, fetch full order details via `GET /v1/order/{appclient_id}/{order_id}`.
1. Normalize fields required for templates (status, tracking URL/number).
1. Return a deterministic_match boolean + extracted variables.

## Acceptance criteria
- [ ] No order link → deterministic_match=false and Tier 2 automation blocked.
- [ ] Linked order → variables extracted safely.

## Test plan
- Unit: order endpoint responses with and without link.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Never log tracking numbers/links in raw logs; only in customer reply rendering.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
