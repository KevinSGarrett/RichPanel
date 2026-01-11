# Cost + Latency Estimates (2,000–3,000 msgs/day)

This repo already contains a formula-based cost model:
- `docs/07_Reliability_Scaling/Cost_Model.md`

Two key inputs:
- **Your stated volume**: ~2,000–3,000 messages/day
- **Repo observed volume** (Agent Activity Heatmap): ~5,066 messages/day average

---

## 1) Pricing inputs (GPT‑5 family)

From `https://platform.openai.com/docs/models/gpt-5` (captured via accessibility snapshot):
- GPT‑5 input: **$1.25 / 1M tokens** (cached input: $0.125 / 1M, output: $10.00 / 1M)
- GPT‑5 mini input: **$0.25 / 1M tokens**
- GPT‑5 nano input: **$0.05 / 1M tokens**

Treat these as directional until validated against `https://openai.com/api/pricing/` in your environment.

---

## 2) Token assumptions (classification-style)

These are *planning assumptions*; replace after you run evals on real-ish traffic:
- **Classifier input tokens (`Tin`)**: 300–800
  - driven by: taxonomy, team list, tier policy, truncated customer text
- **Classifier output tokens (`Tout`)**: 30–120
  - strict JSON only

---

## 3) Daily cost estimate (single-call classifier only)

Let:
- `M = 3,000` messages/day
- `Tin = 600`, `Tout = 80`
- prices per **1M tokens**:
  - GPT‑5 mini input: $0.25
  - GPT‑5 mini output: (not shown in quick comparison; use GPT‑5 output ratio as placeholder until confirmed)

### 3.1 What we can estimate confidently right now
**Input cost for GPT‑5 mini**

- daily input tokens = `M * Tin` = 3,000 * 600 = 1,800,000 tokens
- cost ≈ 1.8M * ($0.25 / 1M) = **$0.45/day** (input only)

Even if `Tin` is 1,000, input-only is still ≈ $0.75/day at 3k msgs/day.

### 3.2 Output cost (needs confirmation)
Output token pricing for mini/nano wasn’t visible in the quick comparison snapshot.
Action item:
- confirm full GPT‑5 mini pricing on `openai.com/api/pricing`
- plug into the formula from `docs/07_Reliability_Scaling/Cost_Model.md`

---

## 4) Cascade cost (nano → mini → 5.2)

A cascade is only cost-saving if:
- the nano stage confidently handles a large fraction of traffic, and
- you *don’t* run multiple models for every message.

Example (illustrative):
- 70% handled by nano (1 call)
- 29% escalated to mini (2 total calls for those)
- 1% escalated to 5.2 (3 total calls for those)

Even then, the biggest cost driver is usually:
- output tokens (if you generate long text)
- and repeated calls (if cascade is too eager)

---

## 5) Latency considerations

At 3,000 msgs/day average:
- ~2.1 msgs/minute average

Even with spikes, you’re unlikely to hit rate limits if:
- you keep model calls to 0–1 per message in steady state
- you use short outputs

From the GPT‑5 docs snapshot, rate limits are tiered by your OpenAI usage tier.
Do not rely on “average rate”; plan for burst traffic and retries.

---

## 6) Key conclusion

For **2k–3k msgs/day**, you can safely standardize on:
- `gpt-5-mini` for classifier/verifier (primary)
- `gpt-5.2` only for rare ambiguity or customer-visible high-stakes tasks

The larger cost risk is not “using GPT‑5 models” — it’s:
- unbounded prompts/outputs
- logging explosions
- repeated cascade calls
- accidental “free-form generation everywhere”


