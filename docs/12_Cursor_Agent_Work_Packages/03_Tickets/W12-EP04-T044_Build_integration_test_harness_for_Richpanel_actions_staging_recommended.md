# W12-EP04-T044 — Build integration test harness for Richpanel actions (staging recommended)

Last updated: 2025-12-23

## Owner / Agent (suggested)
QA/Backend

## Objective
Validate end-to-end behavior against real Richpanel APIs without affecting production.

## Context / References
- `docs/08_Testing_Quality/Integration_Test_Plan.md`
- `docs/08_Testing_Quality/Manual_QA_Checklists.md`

## Dependencies
- W12-EP04-T043

## Implementation steps
1. Create a staging test ticket flow (or safe sandbox process).
1. Run tests: add tags, remove tags, send message, assign team, ensure no close action occurs.
1. Capture results and update docs if any API differences appear.

## Acceptance criteria
- [ ] Integration test runbook exists and passes in staging.

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
