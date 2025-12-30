# Wave 04 — LLM routing + confidence scoring + safety

Last updated: 2025-12-22  
Status: **Complete** ✅

## Wave goal
Design the **LLM decision system** that powers:
- accurate routing to the correct department/team
- safe FAQ automation (especially order status / tracking)
- conservative fallback behavior when uncertain
- production-grade safety controls (prompt injection, data minimization, policy gates)

Wave 04 produces **build-ready specifications** (schemas, prompts, gates, eval design). It does not deploy production code.

---

## Key outputs (Wave 04 deliverables)

### 1) Taxonomy + labeling guidance
- `docs/04_LLM_Design_Evaluation/Intent_Taxonomy_and_Labeling_Guide.md`

### 2) Multi-intent precedence rules
- `docs/04_LLM_Design_Evaluation/Multi_Intent_Priority_Matrix.md`

### 3) Structured output schemas (contract)
- `docs/04_LLM_Design_Evaluation/schemas/mw_decision_v1.schema.json`
- `docs/04_LLM_Design_Evaluation/schemas/mw_tier2_verifier_v1.schema.json`

### 4) Prompt library (IDs only; no customer-facing copy)
- `docs/04_LLM_Design_Evaluation/prompts/classification_routing_v1.md`
- `docs/04_LLM_Design_Evaluation/prompts/tier2_verifier_v1.md`
- `docs/04_LLM_Design_Evaluation/Prompt_Library_and_Templates.md`

### 5) Policy gating logic (authoritative)
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`

### 6) Confidence thresholds + calibration approach
- `docs/04_LLM_Design_Evaluation/Confidence_Scoring_and_Thresholds.md`

### 7) Offline evaluation framework + golden set SOP
- `docs/04_LLM_Design_Evaluation/Offline_Evaluation_Framework.md`
- `docs/04_LLM_Design_Evaluation/Golden_Set_Labeling_SOP.md`
- `docs/04_LLM_Design_Evaluation/schemas/golden_example_v1.schema.json`

### 8) Safety + adversarial coverage
- `docs/04_LLM_Design_Evaluation/Safety_and_Prompt_Injection_Defenses.md`
- `docs/04_LLM_Design_Evaluation/Adversarial_and_Edge_Case_Test_Suite.md`

### 9) Rollout stages + acceptance criteria
- `docs/04_LLM_Design_Evaluation/Acceptance_Criteria_and_Rollout_Stages.md`

### 10) CI regression gates
- `docs/08_Testing_Quality/LLM_Evals_in_CI.md`
- `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`

### 11) Template ID interface (no copy)
- `docs/04_LLM_Design_Evaluation/Template_ID_Catalog.md`

---

## Decisions locked in Wave 04
- The LLM is **advisory**; application policy gates are authoritative.
- Customer-facing replies are **templates only** (no free-form generated replies).
- Tier 3 auto-actions are **disabled** for early rollout.
- Tier 2 verified replies require **deterministic match** and (optionally) verifier approval.
- Multi-intent messages follow a deterministic **priority matrix**.

---

## Notes
- Cursor “prototype” artifacts (if any) are treated as optional reference only; **docs remain the source of truth**.
- Richpanel tenant capability verification remains deferred and is tracked in Admin Open Questions.

---

## Next wave
Wave 05 — FAQ automation design (copy, macros, order status flows, templates, and handoff rules).
