# W12-EP08-T082 — Deploy dashboards + alarms (Wave 06/07/08 alignment) and validate alert runbooks

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra/SecOps

## Objective
Ensure operators can detect issues quickly and follow runbooks.

## Context / References
- `docs/06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md`
- `docs/08_Observability_Analytics/Dashboards_Alerts_and_Reports.md`
- `docs/10_Operations_Runbooks_Training/Runbook_Index.md`

## Dependencies
- W12-EP02-T020
- W12-EP03-T031
- W12-EP03-T033

## Implementation steps
1. Deploy CloudWatch dashboards and alarms for ingress errors, queue age, DLQ, vendor 429s.
1. Link each alarm to a runbook ID (R001–R010).
1. Test at least one alarm path in staging.

## Acceptance criteria
- [ ] Dashboards exist and show expected metrics.
- [ ] Alarm-to-runbook mapping documented.

## Test plan
- Manual: simulate DLQ message and confirm alarm triggers.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
