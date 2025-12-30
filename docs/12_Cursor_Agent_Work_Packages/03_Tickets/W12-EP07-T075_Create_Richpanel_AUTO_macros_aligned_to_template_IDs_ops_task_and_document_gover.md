# W12-EP07-T075 — Create Richpanel 'AUTO:' macros aligned to template IDs (ops task) and document governance

Last updated: 2025-12-23

## Owner / Agent (suggested)
Ops (Richpanel Admin)

## Objective
Enable agents to use the same approved copy manually and keep macros aligned over time.

## Context / References
- `docs/05_FAQ_Automation/Richpanel_AUTO_Macro_Pack_v1.md`
- `docs/05_FAQ_Automation/Richpanel_AUTO_Macro_Setup_Checklist.md`
- `docs/11_Governance_Continuous_Improvement/Procedures_Adding_Intents_Teams_Templates.md`

## Dependencies
- W12-EP04-T040

## Implementation steps
1. Create macros in Richpanel corresponding to each enabled template.
1. Use mapping CSV; avoid inserting sensitive variables into macros if Richpanel cannot render them safely.
1. Document macro IDs/names and store mapping.

## Acceptance criteria
- [ ] Macro pack created in Richpanel.
- [ ] Mapping doc updated and governance process defined.

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
