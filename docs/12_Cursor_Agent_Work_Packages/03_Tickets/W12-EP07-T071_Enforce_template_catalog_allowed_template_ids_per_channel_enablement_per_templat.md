# W12-EP07-T071 — Enforce template catalog: allowed template_ids, per-channel enablement, per-template feature flags

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Prevent accidental use of unapproved templates and support controlled rollout.

## Context / References
- `docs/04_LLM_Design_Evaluation/Template_ID_Catalog.md`
- `docs/05_FAQ_Automation/FAQ_Automation_Dedup_Rate_Limits.md`

## Dependencies
- W12-EP03-T034
- W12-EP07-T070

## Implementation steps
1. Create allowlist of template_ids from Template_ID_Catalog.
1. Check per-template enablement flags via SSM.
1. Apply per-channel constraints (LiveChat vs Email).
1. Emit observability events when templates are blocked.

## Acceptance criteria
- [ ] Unknown template_id is rejected and results in route-only.
- [ ] Per-template toggle disables that template immediately.

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
