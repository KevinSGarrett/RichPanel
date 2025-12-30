# Golden set labeling SOP

Last updated: 2025-12-22  
Scope: Wave 04 (LLM routing design)

## Purpose
We need a **golden (human-labeled) dataset** to:
- calibrate routing confidence thresholds
- validate Tier 0 escalation behavior (safety)
- validate Tier 2 verified automation eligibility (deterministic match gating)
- power CI regression gates (prevent silent regressions)

This SOP describes **how we create, label, QA, version, and maintain** that dataset.

> **Principle:** The LLM is advisory. The **policy engine is authoritative**.  
> Golden labels are used to evaluate the *system decision* (model + gates), not the model alone.

---

## Inputs
### Primary source
- `SC_Data_ai_ready_package.zip` (historical conversations + messages)

### Supplemental sources
- Production sampling (post-launch), redacted and approved
- Synthetic/adversarial cases (prompt-injection attempts, multi-intent, ambiguous language)

---

## What we label (v1)
Each labeled example represents **one customer message** (usually the *first customer message* in a ticket, plus selected follow-ups).

### Required labels (minimum for v1)
1. **primary_intent** (exactly 1)  
2. **secondary_intents** (0–2)  
3. **destination_team** (where the ticket should land)  
4. **automation_tier_max** (highest tier allowed by policy for this message)
   - `TIER_0_ESCALATION` / `TIER_1_SAFE_ASSIST` / `TIER_2_VERIFIED` / `TIER_3_AUTO_ACTION`
5. **template_id** (only if `automation_tier_max` is Tier 1/2 and the response is template-based)

### Optional but recommended labels
- **channel** (LiveChat / Email / Social / TikTok / Unknown)
- **root-cause vs desired-outcome marker**  
  (Example: “missing items” is a root cause; “refund request” is a desired outcome.)
- **deterministic_match_possible** (Yes/No/Unknown)  
  *This is not “we have the order number in the text.” It means the system could deterministically link the customer to the right order given our integrations.*

### What we do **not** label in v1
- exact wording/copy of replies  
  (Wave 05 owns response copy + macro alignment.)
- agent performance quality or CSAT scoring  
  (Useful later, but not required for routing + safe automation correctness.)

---

## Data minimization and redaction
Golden set examples must be **redacted** before use outside the secure dataset store.

### Redaction rules (minimum)
Replace the following with placeholders:
- emails → `<EMAIL>`
- phone numbers → `<PHONE>`
- order numbers → `<ORDER_ID>`
- tracking numbers → `<TRACKING_NUMBER>`
- tracking links → `<TRACKING_URL>`
- addresses → `<ADDRESS>`
- full names (when obvious) → `<NAME>`

**Do not** store raw unredacted text in the documentation repo.  
Store the golden set in a private bucket/repo and only keep:
- schema, SOP, and sample redacted examples in this project plan repo.

---

## Sampling plan (v1)
We want broad coverage with explicit over-sampling for high-risk categories.

### Target size (recommended)
- **1,000 examples** total for initial production gating
  - 600 “common” intents
  - 250 shipping/returns exceptions
  - 150 Tier 0 escalation intents (oversampled)
- **+ 50 adversarial cases** (prompt injection, jailbreak attempts, policy violations)
- **+ 50 multi-intent cases** (to validate priority matrix behavior)

If time is constrained, start with **300–500** and grow over time. The SOP remains the same.

### Stratification
Sample across:
- channels (LiveChat vs Email)
- time of day / day of week (if available)
- intent frequency (oversample rare but high-risk intents)
- languages (if non-English appears)

### How to find candidates (practical)
Use heuristics to bucket candidates before labeling:
- keywords: “chargeback”, “dispute”, “fraud”, “lawyer”, “BBB”
- shipping: “delivered”, “tracking”, “lost”, “missing”, “damaged”
- order modifications: “cancel”, “address change”, “wrong address”
- returns/refunds: “refund”, “return”, “exchange”

Then sample a fixed number per bucket plus a random sample.

---

## Labeling workflow (recommended)
### Roles
- **Labeler A** and **Labeler B**: label independently (blind)
- **Adjudicator**: resolves disagreements and updates guidelines
- **Owner**: approves new dataset version for CI baseline

### Process
1. **Pilot (50 examples)**
   - Labeler A/B label the same 50
   - Adjudicator identifies ambiguous cases
   - Update taxonomy notes + add examples to the edge-case suite

2. **Production labeling**
   - Split remaining examples across labelers
   - 10–20% overlap between labelers for agreement tracking

3. **Adjudication**
   - Disagreements go to adjudicator
   - Update rules in:
     - `Intent_Taxonomy_and_Labeling_Guide.md`
     - `Multi_Intent_Priority_Matrix.md`

4. **QA**
   - Random QA sample (min 5% of the dataset)
   - Focus QA on Tier 0 and Tier 2 eligible intents

### Agreement targets (directional)
- Primary intent agreement: **≥ 85%**
- Destination team agreement: **≥ 90%**
- Tier max agreement: **≥ 90%**
Lower agreement usually means the taxonomy or priority rules need refinement.

---

## Golden set format (recommended)
We recommend a **row-based dataset** (CSV or JSONL) with a stable schema.

### Required columns (CSV)
- `example_id`
- `conversation_id` (optional but useful)
- `message_index` (optional)
- `channel`
- `text_redacted`
- `primary_intent`
- `secondary_intents` (comma-separated)
- `destination_team`
- `automation_tier_max`
- `template_id` (nullable)
- `notes` (nullable)

A JSON Schema for this format is provided in:
- `schemas/golden_example_v1.schema.json`

---

## Versioning and change control
### Version naming
- `gold_v1.0_YYYY-MM-DD` (first baseline)
- `gold_v1.1_YYYY-MM-DD` (add examples; no taxonomy changes)
- `gold_v2.0_YYYY-MM-DD` (taxonomy/schema breaking changes)

### Rules
- CI gates reference an immutable dataset version
- Any change requires:
  - Decision Log entry (why)
  - Changelog entry (what changed)
  - Updated baseline metrics artifact

---

## Where this SOP is used
- `Offline_Evaluation_Framework.md` (eval design)
- `LLM_Evals_in_CI.md` + `LLM_Regression_Gates_Checklist.md` (gates)
- `Adversarial_and_Edge_Case_Test_Suite.md` (test inputs)
