# W12-EP09-T092 — Execute first production deploy runbook (routing-only) and verify observability + rollback

Last updated: 2025-12-23

## Owner / Agent (suggested)
Release Manager/Infra

## Objective
Deploy to production safely with routing-only mode enabled.

## Context / References
- `docs/09_Deployment_Operations/First_Production_Deploy_Runbook.md`
- `docs/09_Deployment_Operations/Go_No_Go_Checklist.md`

## Dependencies
- W12-EP09-T090

## Implementation steps
1. Deploy prod stack with `automation_enabled=false`.
1. Verify ingress/worker health, logs, dashboards, alarms.
1. Verify rollback procedure in prod (dry run).

## Acceptance criteria
- [ ] Prod running in route-only mode with clean monitoring.
- [ ] Rollback path validated.

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
