# W12-EP01-T013 — Create Secrets Manager + SSM parameter namespaces for env config (including kill switch flags)

Last updated: 2025-12-23

## Owner / Agent (suggested)
Infra

## Objective
Standardize config storage and enable runtime control flags.

## Context / References
- `docs/06_Security_Privacy_Compliance/Secrets_and_Key_Management.md`
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`

## Dependencies
- W12-EP01-T010
- W12-EP00-T001

## Implementation steps
1. Create SSM parameter path convention: `/mw/{env}/...`.
1. Create initial flags: `safe_mode`, `automation_enabled`, `template_enabled.*`.
1. Create Secrets Manager secrets: Richpanel API key, OpenAI key, (optional Shopify).
1. Document how to update flags quickly during incidents.

## Acceptance criteria
- [ ] Parameter namespaces exist in each environment.
- [ ] Lambda roles can read only their environment parameters/secrets.
- [ ] Kill switch flags are readable and changeable by authorized operators.

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
