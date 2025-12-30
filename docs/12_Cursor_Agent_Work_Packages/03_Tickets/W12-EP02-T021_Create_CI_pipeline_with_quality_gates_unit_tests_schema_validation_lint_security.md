# W12-EP02-T021 — Create CI pipeline with quality gates (unit tests, schema validation, lint, security checks)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra/Backend

## Objective
Ensure changes to code/prompts/templates are gated before merge/deploy.

## Context / References
- `docs/09_Deployment_Operations/CICD_Plan.md`
- `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`
- `docs/08_Testing_Quality/Contract_Tests_and_Schema_Validation.md`

## Dependencies
- W12-EP02-T020

## Implementation steps
1. Set up CI pipeline steps: install, lint, unit tests, schema validation for LLM and observability events.
1. Add diff checks for `templates_v1.yaml` and prompt artifacts as release artifacts.
1. Add security scanning (dependency check) if available in your policy set.
1. Publish artifacts (smoke test CSV, eval metrics) for review.

## Acceptance criteria
- [ ] CI fails on schema invalid outputs or failing tests.
- [ ] Templates/prompts changes require approval (CODEOWNERS or manual gate).

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
