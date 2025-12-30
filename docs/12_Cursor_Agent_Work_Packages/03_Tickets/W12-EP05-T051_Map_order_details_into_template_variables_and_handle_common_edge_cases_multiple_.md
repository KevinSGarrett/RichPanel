# W12-EP05-T051 — Map order details into template variables and handle common edge cases (multiple fulfillments)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Provide consistent customer replies even when orders are partially fulfilled or multi-shipment.

## Context / References
- `docs/05_FAQ_Automation/Order_Status_Automation.md`
- `docs/05_FAQ_Automation/templates/templates_v1.yaml`

## Dependencies
- W12-EP05-T050

## Implementation steps
1. Implement selection logic: if multiple fulfillments, choose most recent with tracking or summarize.
1. Handle missing tracking URL/number gracefully (status-only reply).
1. Handle delivered-but-not-received case by routing + safe assist (Tier 1).

## Acceptance criteria
- [ ] Customer reply never includes empty placeholders.
- [ ] DNR triggers route + safe-assist template rather than Tier 2 status reply.

## Test plan
- (TBD)

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
