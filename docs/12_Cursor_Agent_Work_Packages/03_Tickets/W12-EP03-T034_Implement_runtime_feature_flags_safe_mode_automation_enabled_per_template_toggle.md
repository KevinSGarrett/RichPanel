# W12-EP03-T034 — Implement runtime feature flags (safe_mode, automation_enabled, per-template toggles) with caching

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Enable operators to disable automation quickly without redeploying.

## Context / References
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- `docs/07_Reliability_Scaling/Parameter_Defaults_Appendix.md`
- `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`

## Dependencies
- W12-EP01-T013
- W12-EP03-T033

## Implementation steps
1. Read flags from SSM Parameter Store with 30–60s cache TTL.
1. Enforce flags in decision pipeline (automation disabled, safe mode route-only).
1. Implement per-template toggles.
1. Add logs/metrics for flag changes observed by runtime.

## Acceptance criteria
- [ ] Flags can be toggled and take effect within cache TTL.
- [ ] Safe mode prevents all customer auto-replies.

## Test plan
- Unit: flag enforcement tests.
- Manual: toggle safe_mode and verify auto replies suppressed.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
