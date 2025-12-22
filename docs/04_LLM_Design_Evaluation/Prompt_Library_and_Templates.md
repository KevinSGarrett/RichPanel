# Prompt Library and Templates

Last updated: 2025-12-22  
Last verified: 2025-12-22 — created initial `prompts/` + `schemas/` artifacts for Wave 04.

## Purpose
Centralize prompt artifacts and ensure:
- consistent tone and policy
- reproducible model behavior (versioned prompts)
- safe template-driven replies (avoid hallucinations)

**Template IDs:** The allowlisted `template_id` values are defined in:
- `Template_ID_Catalog.md` (IDs + variable requirements)
- `schemas/mw_decision_v1.schema.json` (machine-enforced enum)

Wave 05 owns the final customer-facing copy and macro alignment.

---
## Folder locations (documentation repo)
- Prompts: `docs/04_LLM_Design_Evaluation/prompts/`
- Schemas: `docs/04_LLM_Design_Evaluation/schemas/`

---

## Prompt inventory (v1)

### 1) Primary classifier (routing + tier + template plan)
- **File:** `prompts/classification_routing_v1.md`
- **Schema:** `schemas/mw_decision_v1.schema.json`
- **Use when:** every inbound customer message (email/livechat/social)
- **Outputs:** destination team, intent(s), tier recommendation, template ID allowlist, risk flags

### 2) Tier 2 verifier (shipping/status only)
- **File:** `prompts/tier2_verifier_v1.md`
- **Schema:** `schemas/mw_tier2_verifier_v1.schema.json`
- **Use when:** classifier recommends Tier 2 verified automation
- **Goal:** reduce false positives before any sensitive auto-reply

---

## Prompt versioning rules
- Any change to:
  - intent list
  - destination team list
  - tier policy language
  - output schema fields
…requires:
1) bump prompt version string (filename or header)
2) update the schema version if structure changed
3) re-run offline evaluation + regression checks

---

## Template policy (v1)
- Templates are **the only** customer-facing auto-replies in early rollout.
- Never promise refunds/replacements/exchanges automatically.
- Never disclose sensitive order details unless deterministic match is true.
- Keep messages short, friendly, action-oriented.
- Avoid internal jargon (no “intent”, no “confidence score” in customer-facing text).

---

## Where final customer-facing copy lives
Final copy should align to your existing tone:
- Richpanel macros/templates (source of truth for copy; see `RichPanel_Docs_Phase0/04_SETUP_CONFIGURATION`)
- Middleware templates should **match** macros (Wave 05)

---

## Next documents
- Output schema rules: `Prompting_and_Output_Schemas.md`
- Confidence thresholds: `Confidence_Scoring_and_Thresholds.md`
- Safety controls: `Safety_and_Prompt_Injection_Defenses.md`
