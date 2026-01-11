# Roadmap LLM Workloads (What needs models, where, and why)

This repo has a clear separation:
- **Shipped v1**: deterministic routing + deterministic order-status reply (no live LLM classifier in worker)
- **Roadmap**: LLM classifier + verifier + authoritative policy engine (Tier 0/1/2/3)

Primary sources:
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`
- `docs/12_Cursor_Agent_Work_Packages/02_Epics/EP06_LLM_routing_policy_engine.md`

---

## 1) Planned LLM call graph (target)

### Call #1 — Primary classifier (`mw_decision_v1`)
**Purpose**
- determine `primary_intent`, `destination_team`
- recommend automation tier (0/1/2/3)
- choose an allowlisted `template_id` (templates-only design)
- emit risk flags + clarifying questions

**Contract**
- strict JSON Schema: `docs/04_LLM_Design_Evaluation/schemas/mw_decision_v1.schema.json`

**API requirement (repo design)**
- Responses API + Structured Outputs (JSON Schema)
- see `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`

### Call #2 — Tier 2 verifier (`mw_tier2_verifier_v1`) (conditional)

**Purpose**
- second-pass safety check before **Tier 2** disclosure (shipping/status)
- confirm no conflicting intent (cancel/refund/chargeback/etc.)
- require deterministic order linkage boolean

**Contract**
- strict JSON Schema: `docs/04_LLM_Design_Evaluation/schemas/mw_tier2_verifier_v1.schema.json`

**Trigger**
- only when classifier recommends Tier 2 (`TIER_2_VERIFIED`)

### “Optional” LLM workloads (future, but likely)
Based on Wave docs and ticket backlogs, the following LLM workloads are expected to be added over time:

- **Confidence calibration / threshold tuning** (offline)
  - ticket: `W12-EP06-T063`
- **Offline eval harness + regression gates in CI**
  - ticket: `W12-EP06-T064`
- **Clarifying question generation** (still templates-only in early rollout)
  - included in `mw_decision_v1` schema

---

## 2) A note about outbound “rewrite” vs templates-only policy

Many repo docs explicitly require:
- **templates only** for customer-facing replies
- “no free-form LLM-generated replies”

Examples:
- `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- `docs/05_FAQ_Automation/templates/templates_v1.yaml`

If you still want “unique/personalized” copy, you have two safe options:

1) **Template library expansion** (preferred, aligns with policy)
   - produce N approved variants per template_id (tone-safe)
   - pick variant deterministically or via a *classifier-style* LLM that outputs only `variant_id` (not text)

2) **Rewrite layer** (policy exception)
   - deterministic body is generated first
   - model only rewrites style, with hard gates + strict output bounds
   - must fix OpenAI logging first (no response excerpts)

This research directory includes recommendations for both approaches; see `03_Model_Recommendations.md`.


