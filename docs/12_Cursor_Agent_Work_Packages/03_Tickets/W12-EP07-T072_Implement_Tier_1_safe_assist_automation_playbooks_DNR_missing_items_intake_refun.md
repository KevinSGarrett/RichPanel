# W12-EP07-T072 — Implement Tier 1 safe-assist automation playbooks (DNR, missing items intake, refunds intake) + routing tags

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Send low-risk structured intake replies and route to the right team.

## Context / References
- `docs/05_FAQ_Automation/Top_FAQs_Playbooks.md`
- `docs/05_FAQ_Automation/Templates_Library_v1.md`

## Dependencies
- W12-EP06-T061
- W12-EP04-T043

## Implementation steps
1. Implement Tier 1 allowed templates and their routing/tagging side effects.
1. Apply rate limiting/dedup per ticket (avoid spamming customer).
1. Ensure safe_mode disables these sends.

## Acceptance criteria
- [ ] Tier 1 templates send only when allowed and dedup prevents repeated sends.
- [ ] Tags applied correctly for Returns Admin workflows.

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
