# Continuous Improvement Loop

Last updated: 2025-12-22

This is the operational loop that turns:
- agent feedback
- customer behavior changes
- incidents
into **measurable improvements**.

---

## Inputs (signals)

### A) Automated signals (Wave 08)
- intent distribution drift
- confidence distribution drift
- automation rate drift
- misroute spikes
- vendor rate limiting / latency spikes

### B) Human signals (Support team)
- override tags/macros
- “wrong template” feedback
- “should have automated” feedback
- escalation tags (chargeback, fraud, VIP)

### C) Incident signals (Wave 10)
- wrong reply incidents
- PII risk incidents
- automation loops
- regressions after releases

---

## The loop (v1)

1) **Collect**
- sample cases weekly
- store sanitized examples for labeling (per PII policy)

2) **Label**
- dual-label + adjudication for golden set updates
- prioritize high-impact categories: Tier 0, returns, chargebacks, DNR

3) **Diagnose**
- confusion matrix + examples
- determine smallest safe fix

4) **Fix**
- thresholds first
- template gating second
- prompt changes third
- taxonomy changes last

5) **Validate**
- golden set regression
- adversarial suite
- staging smoke pack

6) **Release**
- progressive enablement
- monitor for 24–72 hours

7) **Document**
- decision log + change log updates

---

## “Smallest safe fix” guidance
Prefer:
- disabling a template_id temporarily
- raising a threshold
- tightening deterministic match gates
over:
- rewriting prompts
- renaming intents
- broad “behavior changes”

---

## Success metrics for the loop
- average time from “detected drift” → “fix shipped” under 2 weeks
- fewer repeat incidents from the same root cause
- decreasing manual overrides over time

