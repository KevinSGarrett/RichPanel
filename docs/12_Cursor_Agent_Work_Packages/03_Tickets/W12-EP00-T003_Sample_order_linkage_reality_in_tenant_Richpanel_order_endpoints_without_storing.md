# W12-EP00-T003 — Sample order linkage reality in tenant (Richpanel order endpoints) without storing PII

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Determine how often tickets have linked orders (and tracking fields) so Tier 2 automation expectations match reality.

## Context / References
- `docs/05_FAQ_Automation/Order_Status_Automation.md`
- `docs/03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md`
- `docs/07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`

## Dependencies
- W12-EP00-T001

## Implementation steps
1. Select 10–30 recent tickets expected to be order-related (from Richpanel).
1. Call `GET /v1/order/{conversationId}` and record whether an order is linked (yes/no) and whether key fields are present (tracking url/number).
1. Store only aggregate counts (e.g., 18/30 linked) and field presence rates; store no PII.
1. Update Order Status automation assumptions if linkage is rare.

## Acceptance criteria
- [ ] Aggregate linkage rates documented in a short report.
- [ ] Any needed adjustments to Tier 2 gating assumptions documented.

## Test plan
- N/A (analysis task).

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Do not store order IDs, tracking numbers, emails, or ticket text.
- Aggregate only.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
