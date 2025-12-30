# W12-EP00-T004 — Finalize webhook authentication approach and rotation strategy (based on tenant verification)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Security/Infra

## Objective
Lock the webhook auth design (header token preferred; fallback supported) and prepare token rotation without downtime.

## Context / References
- `docs/06_Security_Privacy_Compliance/Webhook_Auth_and_Request_Validation.md`
- `docs/06_Security_Privacy_Compliance/Webhook_Secret_Rotation_Runbook.md`
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`

## Dependencies
- W12-EP00-T002

## Implementation steps
1. Choose auth method: custom header token (preferred) if supported; else body token; URL token as last resort.
1. Implement multi-token validation window design (current + next).
1. Define rotation cadence and emergency rotation steps.
1. Record final decision in Decision Log.

## Acceptance criteria
- [ ] Decision Log entry exists for webhook auth method.
- [ ] Rotation runbook updated (if needed) to match chosen method.

## Test plan
- Manual: verify invalid token is rejected and logged (without PII).
- Manual: verify dual-token window accepts both tokens.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Tokens stored in Secrets Manager, not in code.
- Reject unsigned/invalid requests quickly (<200ms).

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
