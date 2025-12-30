# W12-EP04-T040 — Create Richpanel team + tags (Chargebacks/Disputes, mw-routing-applied, feedback tags) and document mapping

Last updated: 2025-12-23

## Owner / Agent (suggested)
Ops (Richpanel Admin)

## Objective
Ensure the required teams and tags exist before automation/routing is enabled.

## Context / References
- `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`
- `docs/03_Richpanel_Integration/Team_Tag_Mapping_and_Drift.md`
- `docs/08_Observability_Analytics/Feedback_Signals_and_Agent_Override_Macros.md`

## Dependencies
- W12-EP00-T001

## Implementation steps
1. Create Team: Chargebacks / Disputes.
1. Create or confirm tags: mw-routing-applied, chargeback_dispute, fulfillment_exception_*, mw_feedback_* etc.
1. Export team/tag IDs (if needed) and store mapping in docs (no secrets).

## Acceptance criteria
- [ ] Chargebacks team exists.
- [ ] Required tags exist and are visible in Richpanel.
- [ ] Mapping doc updated with any new IDs/names.

## Test plan
- (TBD)

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Do not store customer data in mapping docs.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
