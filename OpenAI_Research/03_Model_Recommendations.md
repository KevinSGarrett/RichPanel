# Model Recommendations (Exact model IDs per workload)

You asked for “exact models for every process,” while processing ~2,000–3,000 messages/day.

This repo already defines a GPT‑5 family strategy and names:
- `gpt-5-nano` (cheapest/highest throughput)
- `gpt-5-mini` (default “best balance”)
- `gpt-5` / `gpt-5-2025-08-07` snapshot alias (documented in OpenAI docs)
- `gpt-5.2` (heavy fallback, rare) — from repo design docs

**Repo sources**
- `docs/04_LLM_Design_Evaluation/Model_Config_and_Versioning.md`
- `docs/11_Governance_Continuous_Improvement/Model_Update_Policy.md`

**External evidence (OpenAI docs)**  
From `https://platform.openai.com/docs/models/gpt-5` we captured:
- a link recommending “latest GPT‑5.1”
- pricing quick comparison for GPT‑5 family
- snapshot alias example: `gpt-5-2025-08-07`

---

## 1) Recommended “canonical” model pins (what to set)

### 1.1 Production (default posture)
- **Primary classifier**: `gpt-5-mini`
- **Tier‑2 verifier**: `gpt-5-mini`
- **Cheap pre-pass (optional)**: `gpt-5-nano`
- **Heavy fallback (rare)**: `gpt-5.2`

### 1.2 Stability vs freshness (where GPT‑5.1 fits)
OpenAI’s GPT‑5 docs recommend using the latest GPT‑5.1. Operationally, this implies:
- `gpt-5.1` (or a dated GPT‑5.1 snapshot) is a **stability pin**
- `gpt-5.2` is a **capability pin** for rare/high-risk ambiguity or strict enforcement

**If your account exposes `gpt-5.1` and `gpt-5.2` as distinct model IDs**, use:
- classifier/verifier: `gpt-5.1-mini` (or `gpt-5-mini` if 5.1-mini doesn’t exist)
- heavy fallback: `gpt-5.2`

If your account only exposes `gpt-5-mini` (alias), keep it and record `model_snapshot` in audit logs for drift tracking.

---

## 2) Per-workload mapping (current + planned)

### 2.1 Shipped v1 (today)

| Workload | Where | Should it call OpenAI? | Recommended model |
|---|---|---:|---|
| Deterministic routing (keyword heuristics) | `automation/router.py` | No | N/A |
| LLM routing suggestion (advisory module exists) | `automation/llm_routing.py` | Only in shadow/assisted mode | `gpt-5-mini` (replace `gpt-4o-mini`) |
| Offline prompt harness | `automation/prompts.py` | Offline only | `gpt-5-mini` (for eval parity) |

### 2.2 Roadmap LLM pipeline (target)

| Workload | Contract | Recommended model | Why |
|---|---|---|---|
| Classifier (`mw_decision_v1`) | JSON Schema (Structured Outputs) | `gpt-5-mini` | default “best balance” per repo docs |
| Verifier (`mw_tier2_verifier_v1`) | JSON Schema | `gpt-5-mini` | short, strict decision; low latency |
| Cheap pre-pass (optional) | JSON Schema | `gpt-5-nano` | cost control at higher volumes |
| Heavy fallback | JSON Schema | `gpt-5.2` | rare ambiguity; higher accuracy/capability |

### 2.3 “Unique/personalized” customer copy (two recommended options)

**Option A (preferred, policy-aligned): template variants**  
Model output should be **only** `template_id` + `variant_id`, never text.
- Variant chooser model: `gpt-5-nano` or `gpt-5-mini`
- Why: cheapest, avoids free-form text risk

**Option B (policy exception): rewrite layer**
- Rewrite model: `gpt-5-mini` initially; promote to `gpt-5.2` if quality isn’t sufficient
- Why: rewriting is “customer-visible quality,” so `gpt-5.2` may be worth the cost, but only after hard gates + logging fixes.

---

## 3) Pricing + throughput sanity check (high level)

From the GPT‑5 docs page snapshot, GPT‑5 family “quick comparison” shows input token pricing per 1M tokens:
- GPT‑5: **$1.25**
- GPT‑5 mini: **$0.25**
- GPT‑5 nano: **$0.05**

Also, repo’s own cost model uses formula-based placeholders:
- `docs/07_Reliability_Scaling/Cost_Model.md`

At **2–3k msgs/day**, `gpt-5-mini` for a single classifier call per message is typically affordable if prompts are kept tight and output is short JSON.

---

## 4) Required config surface (what to implement)

To avoid a single global `OPENAI_MODEL` affecting everything, implement per-workload env vars:

- `OPENAI_CLASSIFIER_MODEL` = `gpt-5-mini`
- `OPENAI_VERIFIER_MODEL` = `gpt-5-mini`
- `OPENAI_ROUTING_ADVISORY_MODEL` = `gpt-5-mini`
- `OPENAI_VARIANT_PICKER_MODEL` = `gpt-5-nano`
- `OPENAI_HEAVY_FALLBACK_MODEL` = `gpt-5.2`

If you want an explicit GPT‑5.1 pin (recommended for stability):
- `OPENAI_CLASSIFIER_MODEL` = `gpt-5.1-mini` (if available)
- `OPENAI_VERIFIER_MODEL` = `gpt-5.1-mini` (if available)

See `04_Implementation_Plan.md` for wiring details.


