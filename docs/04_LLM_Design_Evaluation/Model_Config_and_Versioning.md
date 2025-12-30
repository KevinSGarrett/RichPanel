# Model Configuration and Versioning

Last updated: 2025-12-22  
Last verified: 2025-12-22 — Updated recommended defaults for GPT-5 model family + cascade strategy.

## Objective
Define how we select, configure, and upgrade OpenAI models in a way that is:
- safe (fail closed)
- reproducible (versioned prompts + schema)
- measurable (offline eval + shadow mode)
- cost-aware (cascades, caching, token discipline)

---

## Guiding principles
1) **Model choice is config, not code**
   - use env/config files
   - never hardcode model names in multiple places

2) **Prompts + schema are versioned artifacts**
   - prompt version changes require offline eval
   - schema changes require code updates + eval

3) **Prefer a model cascade**
   - cheap model first
   - expensive model only on low confidence or high-risk

---

## Recommended default model set (v1)

### Primary classifier (routing + tier + template plan)
**Default (best balance):**
- Model: `gpt-5-mini`
- Reasoning effort: `none` (classification-style)
- Temperature: 0 (if supported for the chosen model/effort)
- Structured outputs enabled (JSON Schema)

Why:
- well-defined classification-style task
- low latency / good instruction following
- structured outputs supported

### Tier 2 verifier (shipping/status only)
**Default:**
- Model: `gpt-5-mini` (same family, short prompt)
- Reasoning effort: `none`
- Temperature: 0
- Structured outputs enabled

### Optional optimization (later): nano/mini cascade
If volume or cost becomes material:
- Stage A: `gpt-5-nano` for high-throughput classification
- Stage B: `gpt-5-mini` only when:
  - confidence < threshold, or
  - Tier 2 is being considered, or
  - message is multi-intent/ambiguous

This preserves quality while reducing spend.

### “Heavy” fallback (rare)
For extremely ambiguous messages where correct routing matters:
- `gpt-5.2` with reasoning effort `none` (or higher if needed)
Use sparingly; keep prompts short.

---

## Parameter compatibility notes
Some models/effort settings only support certain parameters (temperature/logprobs/top_p).
Treat this as **implementation detail**:
- for routing/classification, our prompts should not rely on logprobs
- confidence comes from engineered signals + offline calibration

---

## Versioning (must-have)
Track these version strings on every decision record:
- `model_name`
- `model_snapshot` (if applicable)
- `prompt_version`
- `schema_version`
- `routing_mapping_version`
- `tier_policy_version`

Store versions in:
- config file (source of truth)
- logs/metrics (observability)
- evaluation reports

---

## Rollout strategy (required)

### Step 1 — Offline evaluation (golden set)
- run the classifier on labeled data
- compute per-intent precision/recall + confusion matrices
- validate Tier 0 and Tier 2 gates

### Step 2 — Staging (shadow mode)
- run in parallel on live traffic
- do not affect routing/actions
- compare outputs to current manual outcomes

### Step 3 — Staging (assisted mode)
- apply route tags but do not auto-send replies
- agents can see “suggested route” in tags/notes

### Step 4 — Production (limited auto-send)
- enable only Tier 1 safe-assist and Tier 2 verified order-status
- keep Tier 0 strict
- auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception) tickets

---

## Monitoring for drift
Track:
- intent distribution over time
- abstain rate
- Tier 0 flags volume
- mismatch between model route and final human assignment (proxy quality)
- Tier 2 send rate + customer complaint rate

---

## Decisions to document
- who can change model/prompt config
- what metrics must pass for promotion
- how often we review thresholds
