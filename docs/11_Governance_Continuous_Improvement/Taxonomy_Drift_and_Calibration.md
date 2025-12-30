# Taxonomy Drift and Calibration

Last updated: 2025-12-22

This document defines how we detect and manage “drift” in routing and FAQ classification over time.

Drift happens when:
- customer language changes (“new product name”, new slang, new issue types)
- business processes change (new teams, new routing rules)
- model behavior shifts (vendor updates, prompt edits)
- data distribution shifts (new channel mix, marketing campaigns)

---

## The drift loop (v1)

1. **Detect**: automated signals indicate something changed
2. **Diagnose**: analyze confusion matrix, overrides, and misroutes
3. **Decide**: choose the smallest safe fix (threshold, prompt, taxonomy, template)
4. **Validate**: run golden set + adversarial tests
5. **Release**: progressive enablement
6. **Monitor**: confirm the drift is resolved

---

## Drift signals (what to watch)

### A) Quality drift
- routing accuracy or macro F1 down week-over-week
- rising human override rate (agent changes team/tag)
- rising “escalate_to_human” or Tier 0 triggers

### B) Distribution drift
- large shifts in intent distribution (e.g., order status spikes)
- new unknown/other intent rate rising

### C) Operations drift
- retry rates increase (vendor instability)
- queue backlog grows due to latency changes
- cost per ticket increases unexpectedly

---

## Calibration cadence (best-suggested defaults)

### Weekly: “Quality triage” (30–45 min)
Inputs:
- top 10 misroutes (by impact)
- override signals
- Tier 0 triggers
Outputs:
- issue list + owners (fix or label for dataset)

### Monthly: “Calibration run”
Inputs:
- sample of production tickets (PII redacted)
- fresh labeled set (dual-label + adjudication)
Actions:
- update thresholds (if needed)
- minor prompt edits (if needed)
- add/retire intents/templates (if needed)

### Quarterly: “Taxonomy review”
- consider structural changes (split/merge intents)
- review team mapping and coverage
- update training materials for agents

---

## What “good” looks like
- drift is detected within 1 week
- fixes are small, tested, and reversible
- no one is forced to “guess” what changed (everything is logged)

---

## Tooling hooks (where signals come from)
- Wave 08 dashboards and drift detection rules
- Wave 04 evaluation harness (golden set + adversarial suite)
- Wave 10 operational runbooks (misrouting spike, wrong reply incidents)

---

## Common calibrations (preferred order)
When a metric regresses, start with the smallest change:

1) **Adjust threshold(s)** (lowest blast radius)
2) **Improve deterministic match gate** (reduce unsafe automation)
3) **Prompt tweak** (carefully; requires full eval)
4) **Add a new intent** (if new behavior is real and recurring)
5) **Split/merge intents** (largest change; requires training update)

---

## Documentation requirements
Every calibration cycle should produce:
- a short summary (what drift was observed)
- what was changed (and why)
- what tests passed
- what to monitor after release

