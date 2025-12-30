# W12-EP01-T012 — Enable baseline logging + audit (CloudTrail, CloudWatch log retention, budgets, alarms)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra/SecOps

## Objective
Ensure we can audit and detect abnormal activity before production rollout.

## Context / References
- `docs/06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md`
- `docs/06_Security_Privacy_Compliance/AWS_Security_Baseline_Checklist.md`

## Dependencies
- W12-EP01-T010

## Implementation steps
1. Enable CloudTrail in each account (or org-level if used).
1. Set CloudWatch log retention defaults.
1. Create budget alarms for AWS cost anomalies.
1. Create security alarms (invalid webhook token spikes, break-glass role usage).

## Acceptance criteria
- [ ] CloudTrail enabled and logs retained for configured period.
- [ ] Budget alarm triggers defined.
- [ ] Security alarms exist and are documented.

## Test plan
- Manual: generate a test event and confirm it appears in CloudTrail/CloudWatch.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
