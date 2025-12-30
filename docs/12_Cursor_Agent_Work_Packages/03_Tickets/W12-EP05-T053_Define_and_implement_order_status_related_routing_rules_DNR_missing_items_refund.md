# W12-EP05-T053 — Define and implement order-status-related routing rules (DNR, missing items, refund requests)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Ensure order topics that are not safe to auto-resolve are routed consistently.

## Context / References
- `docs/05_FAQ_Automation/Top_FAQs_Playbooks.md`
- `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`

## Dependencies
- W12-EP06-T061
- W12-EP07-T072

## Implementation steps
1. Implement detection for DNR/missing items; route to Returns Admin.
1. Ensure chargeback/dispute routes to Chargebacks team (Tier 0).
1. Add tags for workflow triage (shipping exception tags).

## Acceptance criteria
- [ ] DNR and missing items do not get Tier 2 status automation.
- [ ] Chargebacks always routed to Chargebacks team.

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
