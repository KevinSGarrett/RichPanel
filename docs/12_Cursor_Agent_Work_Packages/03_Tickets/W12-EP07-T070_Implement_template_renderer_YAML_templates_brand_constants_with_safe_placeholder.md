# W12-EP07-T070 — Implement template renderer (YAML templates + brand constants) with safe placeholder handling

Last updated: 2025-12-23

## Owner / Agent (suggested)
Backend

## Objective
Render customer replies from approved templates without allowing the model to write text.

## Context / References
- `docs/05_FAQ_Automation/templates/templates_v1.yaml`
- `docs/05_FAQ_Automation/templates/brand_constants_v1.yaml`
- `docs/05_FAQ_Automation/Template_Rendering_and_Variables.md`

## Dependencies
- W12-EP05-T051
- W12-EP06-T061

## Implementation steps
1. Load templates and constants at startup (cache).
1. Validate that required variables are present; if missing → route-only fallback.
1. Support channel variants (default/livechat).
1. Implement escaping/sanitization to prevent template injection.

## Acceptance criteria
- [ ] No template renders with unresolved placeholders.
- [ ] Renderer supports both default and livechat variants.

## Test plan
- Unit: rendering with missing variables fails closed.

## Rollout / Release notes
- Feature flags: `safe_mode`, `automation_enabled`, per-template toggles (see Wave 06/07).

## Security / Privacy notes
- Follow PII handling rules; no secrets in repo.

## Deliverables
- Implementation (code/IaC/config) per ticket scope
- Tests passing (as specified)
- Cursor summary (what changed + how to run)
