# W12-EP08-T083 — Harden public endpoint (API Gateway throttling, optional WAF, SSRF/egress controls)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra

## Objective
Reduce abuse risk and protect availability.

## Context / References
- `docs/06_Security_Privacy_Compliance/Network_Security_and_Egress_Controls.md`
- `docs/07_Reliability_Scaling/Service_Quotas_and_Operational_Limits.md`

## Dependencies
- W12-EP03-T030

## Implementation steps
1. Set API Gateway throttling limits consistent with expected traffic.
1. If WAF is used, configure baseline rules (rate-based, common threats).
1. Ensure Lambda has no unnecessary egress (avoid fetching arbitrary URLs).

## Acceptance criteria
- [ ] Throttling in place and documented.
- [ ] Egress policy documented.

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
