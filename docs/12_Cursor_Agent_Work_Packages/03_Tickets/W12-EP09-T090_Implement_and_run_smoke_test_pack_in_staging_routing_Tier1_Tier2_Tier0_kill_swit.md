# W12-EP09-T090 — Implement and run smoke test pack in staging (routing + Tier1 + Tier2 + Tier0 + kill switch)

Last updated: 2025-12-23

## Owner / Agent (suggested)
QA/Backend

## Objective
Verify core correctness before any production enablement.

## Context / References
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

## Dependencies
- W12-EP07-T073
- W12-EP08-T080

## Implementation steps
1. Create scripts or manual run process to execute smoke tests against staging.
1. Record results and any defects; fix before proceeding.
1. Verify kill switch toggles work.

## Acceptance criteria
- [ ] Smoke tests pass in staging with documented evidence.

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
