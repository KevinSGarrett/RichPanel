# W12-EP06-T060 — Implement classifier model call with strict schema validation (mw_decision_v1) and fail-closed fallback

Last updated: 2025-12-23

## Owner / Agent (suggested)
AI/Backend

## Objective
Produce structured routing decisions with confidence scoring and safe fallback on parse/validation failure.

## Context / References
- `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`
- `docs/04_LLM_Design_Evaluation/schemas/mw_decision_v1.schema.json`
- `docs/04_LLM_Design_Evaluation/prompts/classification_routing_v1.md`

## Dependencies
- W12-EP03-T033
- W12-EP00-T001

## Implementation steps
1. Load prompt artifact and call model with structured output support.
1. Validate response against schema; if invalid → route-only fallback to Technical Support (or default) and tag for review.
1. Log only metadata (model name, token counts, decision id) not raw text.
1. Emit observability events for decision_made and decision_failed.

## Acceptance criteria
- [ ] Invalid schema output never triggers automation.
- [ ] Valid decisions include intent, confidence, and suggested department.

## Test plan
- Unit: schema validation failure path.
- Unit: prompt injection examples do not bypass Tier 0 gates.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
