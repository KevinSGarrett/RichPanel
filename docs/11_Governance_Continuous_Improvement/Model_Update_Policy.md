# Model Update Policy

Last updated: 2025-12-22

This policy defines how we change **OpenAI models** (or model settings) used for routing and FAQ automation.

The core principle:
- **Models are advisory; policy gates are authoritative.**
- Any model change can shift behavior. We treat it like a production change.

---

## What counts as a “model change”
Any of the following:
- changing model name/version for the classifier or verifier
- changing temperature / reasoning settings / max output
- changing prompt format that affects structured outputs
- changing tool settings that affect data handling (e.g., logging/store)

---

## When we should change models
Valid triggers:
- accuracy or stability improvements (validated by evals)
- cost reductions without quality loss
- latency improvements
- vendor deprecations / availability issues
- safety improvements (lower jailbreak susceptibility)

Invalid triggers:
- “new model is out, let’s switch” without evaluation

---

## Required artifacts for a model change PR
- the proposed model identifier + settings
- expected impact (quality/cost/latency)
- evaluation summary on the **current golden set**
- summary of adversarial suite results
- rollback plan (previous model pin)

---

## Required gates (v1)

### Hard gates (must pass)
- **Structured output schema validity:** 100% valid
- **Tier 0 FN = 0** on golden set (or explicitly waived with leadership signoff — not recommended)
- **Tier 2 violations = 0** (policy engine should enforce this regardless)
- **No increase in PII risk indicators** (no new logging of message bodies, etc.)

### Soft gates (can be waived with justification)
- macro F1 not worse than baseline by > 2–3 points (choose a fixed band in CI)
- latency p95 not worse than baseline by > 20%
- cost per ticket not worse than baseline by > 15%

---

## Rollout strategy (best-suggested)
Default is progressive:

1. **Staging bake** (24–72 hours)
   - run eval harness daily
   - monitor vendor error rates and latency

2. **Prod canary**
   - apply model to a limited segment (e.g., LiveChat only) or to a low-risk template set
   - monitor for regressions

3. **Full rollout**
   - only after canary stability

If canary regressions occur:
- revert model pin
- keep routing active (route-only safe mode if needed)

---

## Model version pinning and inventory
We treat model selection as a versioned artifact:
- record the active model in:
  - config file (or Parameter Store)
  - observability event metadata
  - change log entry

We do **not** change models by editing a production console value without a repo trace.

---

## Deprecation and emergency migration
If a provider deprecates a model:
- move to the closest supported model
- keep automation disabled (route-only) until eval gates pass
- document the event and mitigation in the change log

---

## Ownership
- Accountable: Engineering Owner
- Consulted: Support Ops Owner (for customer-visible impact), Security (data-handling changes)
- Informed: Leadership

