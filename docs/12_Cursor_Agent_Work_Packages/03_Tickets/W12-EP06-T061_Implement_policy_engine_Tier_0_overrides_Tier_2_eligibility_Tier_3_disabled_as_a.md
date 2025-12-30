# W12-EP06-T061 — Implement policy engine (Tier 0 overrides, Tier 2 eligibility, Tier 3 disabled) as authoritative layer

Last updated: 2025-12-23

## Owner / Agent (suggested)
AI/Backend

## Objective
Ensure model recommendations cannot cause unsafe actions.

## Context / References
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- `docs/04_LLM_Design_Evaluation/Multi_Intent_Priority_Matrix.md`

## Dependencies
- W12-EP06-T060

## Implementation steps
1. Implement Tier 0 intent list and hard override behavior (route-only).
1. Enforce Tier 2 requires deterministic match and verifier approval.
1. Disable Tier 3 actions entirely in v1.
1. Apply multi-intent priority matrix to select primary intent.

## Acceptance criteria
- [ ] Tier 0 never auto-sends customer replies.
- [ ] Tier 2 never runs without deterministic match.
- [ ] Tier 3 remains disabled regardless of model output.

## Test plan
- Unit tests covering Tier 0 override and Tier 2 eligibility.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
