# W12-EP06-T062 — Implement Tier 2 verifier call (mw_tier2_verifier_v1) and integrate into policy gating

Last updated: 2025-12-23

## Owner / Agent (suggested)
AI/Backend

## Objective
Add a second check before sending account/order-specific info.

## Context / References
- `docs/04_LLM_Design_Evaluation/schemas/mw_tier2_verifier_v1.schema.json`
- `docs/04_LLM_Design_Evaluation/prompts/tier2_verifier_v1.md`

## Dependencies
- W12-EP06-T061
- W12-EP05-T050

## Implementation steps
1. Call verifier with minimal data (redacted context + order linkage evidence).
1. Validate verifier output schema; require explicit approval to proceed.
1. Log verifier metadata only.
1. On verifier failure → route-only + tag for review.

## Acceptance criteria
- [ ] Verifier must approve for Tier 2 auto-reply to send.
- [ ] Verifier cannot be bypassed by classifier output.

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
