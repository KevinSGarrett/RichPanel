# Prompt, Template, and Schema Versioning

Last updated: 2025-12-22

This document defines how we version and release the *non-code artifacts* that control system behavior:
- prompts
- template library
- output schemas
- thresholds and policy config

---

## Why this matters
These artifacts behave like code:
- they change customer-visible behavior
- they can introduce regressions
- they must be reversible

---

## Source of truth
- Prompts: `docs/04_LLM_Design_Evaluation/prompts/`
- Schemas: `docs/04_LLM_Design_Evaluation/schemas/` and related schema folders
- Templates: `docs/05_FAQ_Automation/templates/templates_v1.yaml`
- Defaults/config knobs: `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`

Richpanel macros must mirror templates, but **the repo is canonical**.

---

## Versioning scheme (v1 recommended)
Use semantic versioning for each artifact family:

- `mw_decision_schema`: v1, v2, v3+
- `template_library`: v1.0, v1.1, v1.2+
- `routing_prompt`: v1.0, v1.1, v1.2+
- `threshold_config`: v1.0, v1.1, v1.2+

Version bump guidelines:
- **Patch:** copy tweaks, non-functional clarifications
- **Minor:** new templates/intents, new optional fields
- **Major:** breaking field rename/removal, intent renames, incompatible prompt outputs

---

## Release requirements
Any version change must:
- include a changelog entry
- pass Wave 09 gates (smoke pack + eval gates)
- have a rollback plan

---

## Rollback strategy
Always keep last-known-good versions available:
- revert commit
- disable template_id
- safe_mode route-only

---

## “No hidden changes” rule
Do not:
- edit prompts directly in production runtime
- change templates only in Richpanel macros
- modify thresholds without logging a decision

