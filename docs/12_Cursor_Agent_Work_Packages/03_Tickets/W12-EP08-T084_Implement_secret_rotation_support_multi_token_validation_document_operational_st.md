# W12-EP08-T084 — Implement secret rotation support (multi-token validation) + document operational steps

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra/SecOps

## Objective
Enable safe periodic rotation without service interruption.

## Context / References
- `docs/06_Security_Privacy_Compliance/Webhook_Secret_Rotation_Runbook.md`
- `docs/06_Security_Privacy_Compliance/Secrets_and_Key_Management.md`

## Dependencies
- W12-EP08-T080

## Implementation steps
1. Support two active webhook tokens simultaneously (current + next).
1. Support OpenAI key rotation and Richpanel key rotation (redeploy not required if secrets fetched at runtime).
1. Document rotation cadence and evidence logging.

## Acceptance criteria
- [ ] Rotation steps validated in staging.

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
