# W12-EP07-T073 — Implement Tier 2 verified order status auto-reply (tracking link/number) with deterministic match + verifier approval

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend/AI

## Objective
Provide automated order status replies only when safe to disclose.

## Context / References
- `docs/05_FAQ_Automation/Order_Status_Automation.md`
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`

## Dependencies
- W12-EP06-T062
- W12-EP05-T050
- W12-EP07-T070

## Implementation steps
1. If intent is order_status and confidence >= threshold → attempt deterministic order link.
1. Run Tier 2 verifier; only proceed if approved.
1. Render template with tracking variables and send message via Richpanel.
1. Record action idempotency and observability events.

## Acceptance criteria
- [ ] No deterministic match → no tracking disclosed.
- [ ] Verifier must approve before sending.
- [ ] Duplicate events do not duplicate replies.

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
