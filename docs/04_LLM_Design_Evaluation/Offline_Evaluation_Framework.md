# Offline evaluation framework

Last updated: 2025-12-22  
Last verified: 2025-12-22 — Updated to match v1 taxonomy + schemas in Wave 04.

## Objective
Build an **offline evaluation harness** so we can:
- measure routing accuracy and misroutes
- calibrate confidence thresholds
- validate Tier 0 / Tier 2 safety gates
- compare model/prompt versions before rollout

This avoids shipping “prompt tweaks” straight to production.

---

## Inputs

### A) Conversation dataset
Primary dataset:
- `SC_Data_ai_ready_package.zip`
  - conversations: 3613
  - messages: 28585
  - date range: 2025-10-14 10:26:00 → 2025-12-20 19:44:00
  - conversation types include: email, email_from_widget, tiktok messages, comments, etc.

**Important:** Do not paste raw conversation content into planning docs.  
Use aggregate stats + anonymized patterns only.

### B) Golden label set (human-labeled)
We need a curated, human-labeled **golden set** that maps each *example message* to:

- `primary_intent` (from the v1 taxonomy)
- `secondary_intents` (0–2)
- `destination_team`
- `automation_tier_max` (Tier 0/1/2/3 policy cap)
- `template_id` (nullable; IDs only)

**How we create/QA/version the golden set** is defined in:
- `Golden_Set_Labeling_SOP.md`
- `schemas/golden_example_v1.schema.json`

**Important:** Treat the golden set as a **controlled artifact**:
- store it securely (not in the documentation repo)
- reference immutable versions in CI (example: `gold_v1.0_YYYY-MM-DD`)
- re-baseline metrics only with an explicit Decision Log entry
### C) Schemas and prompts
- schemas live in `docs/04_LLM_Design_Evaluation/schemas/`
- prompts live in `docs/04_LLM_Design_Evaluation/prompts/`

---

## Dataset profile notes (planning-relevant)
From the SC_Data package, deterministic identifiers are often missing in the first message:
- order number in first customer message: ~12.4%
- order number anywhere in conversation: ~22.2%

This supports:
- Tier 1 “ask for order #” as a core pattern
- Tier 2 gating that requires deterministic match

---

## Evaluation metrics (required)
At minimum, compute:
- overall accuracy
- macro F1 (intent)
- weighted F1 (intent)
- per-intent precision/recall/F1
- confusion matrix (intent)
- confusion matrix (destination team)
- Tier 0 FN/FP counts and examples (anonymized)
- Tier 2 eligibility:
  - % eligible
  - % blocked by missing deterministic match
  - % blocked by verifier
  - violations (must be 0)

---

## Acceptance bands (v1 targets)
See `Acceptance_Criteria_and_Rollout_Stages.md` for the formal targets.
High-level:
- Tier 0: 0 false negatives on golden set (plus keyword heuristic safety net)
- Tier 2: 0 false positives + 0 deterministic-match violations
- Routing: macro F1 ≥ 0.75; weighted F1 ≥ 0.90

---

## Regression gates (required before production)
Any model/prompt/schema change must satisfy:
- Tier 0 misses do not increase beyond the acceptance band
- routing macro F1 does not regress beyond the acceptance band
- Tier 2 deterministic match rule not violated
- latency + cost sanity checks

---

## Optional reference implementation
A non-production prototype harness exists (for validation only):
- `reference_artifacts/cursor_wave04_offline_eval_scaffold/`

Docs remain the source of truth; prototypes exist only to validate feasibility and reduce ambiguity.

---

## Open questions (can be answered later)
- Final golden-set sampling strategy and adjudication workflow
- Whether we need language-specific or channel-specific models
- Whether we want per-channel threshold overrides (LiveChat vs email)