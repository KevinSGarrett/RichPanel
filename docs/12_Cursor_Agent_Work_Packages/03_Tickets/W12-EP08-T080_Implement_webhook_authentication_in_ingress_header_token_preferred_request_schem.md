# W12-EP08-T080 — Implement webhook authentication in ingress (header token preferred) + request schema validation

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend/Infra

## Objective
Prevent unauthorized calls and reduce attack surface.

## Context / References
- `docs/06_Security_Privacy_Compliance/Webhook_Auth_and_Request_Validation.md`
- `docs/06_Security_Privacy_Compliance/Webhook_Secret_Rotation_Runbook.md`

## Dependencies
- W12-EP00-T004
- W12-EP03-T030

## Implementation steps
1. Validate token according to chosen method; support dual-token window.
1. Reject invalid requests quickly; return 401/403.
1. Validate request JSON schema; reject oversized payloads.
1. Emit security metrics and logs.

## Acceptance criteria
- [ ] Invalid token requests are rejected and counted.
- [ ] Token rotation works without downtime.

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
