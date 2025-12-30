# W12-EP02-T022 — Implement deployment promotion flow (dev → staging → prod) and rollback automation

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra

## Objective
Make deployments repeatable with safe rollback path.

## Context / References
- `docs/09_Deployment_Operations/Release_and_Rollback.md`
- `docs/09_Deployment_Operations/First_Production_Deploy_Runbook.md`

## Dependencies
- W12-EP02-T021

## Implementation steps
1. Implement deployment job to dev, then staging, then prod (manual approval between).
1. Ensure feature flags default to route-only in prod deploy.
1. Automate rollback to last-known-good artifact.
1. Document runbook steps.

## Acceptance criteria
- [ ] Staging deployment requires manual approval after tests pass.
- [ ] Rollback path documented and tested in staging.

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
