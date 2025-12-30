# W12-EP06-T064 — Integrate offline eval harness into CI (golden set run + regression gates)

Last updated: 2025-12-23

## Owner / Agent (suggested)
AI/QA

## Objective
Prevent silent quality regressions when prompts/models/templates change.

## Context / References
- `docs/04_LLM_Design_Evaluation/Offline_Evaluation_Framework.md`
- `docs/04_LLM_Design_Evaluation/Golden_Set_Labeling_SOP.md`
- `docs/08_Testing_Quality/LLM_Evals_in_CI.md`

## Dependencies
- W12-EP02-T021

## Implementation steps
1. Add CI job to run golden set evaluation (sanitized).
1. Enforce hard gates: Tier0 FN=0, Tier2 violations=0, schema validity=100%.
1. Publish confusion matrix artifact for review.

## Acceptance criteria
- [ ] CI fails when gates violated.
- [ ] Artifacts available for review.

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
