# Confidence scoring and threshold defaults

Last updated: 2025-12-22

## Why this matters
LLM “confidence” is not calibrated by default. If we treat a model’s self-reported confidence as truth, we eventually ship:
- wrong auto-replies (highest risk)
- misroutes that increase handle time
- unsafe disclosures (tracking/status for the wrong person)

This document defines:
- what “confidence” means in our system
- how we compute **routing confidence** and **automation confidence**
- **v1 threshold defaults** (conservative; tuned later)
- calibration plan (how we improve over time)

---

## Data-informed context (why we must be conservative)

From `RoughDraft/SC_Data_intent_routing.csv` (3,611 conversations):
Top intents by volume:
- Order status & tracking: 1872 (51.84%)
- Cancel order: 240 (6.65%)
- Product / app troubleshooting: 174 (4.82%)
- Cancel subscription: 141 (3.9%)
- Missing items in shipment: 125 (3.46%)
- Chargeback / dispute: 87 (2.41%)

From `SC_Data_ai_ready_package.zip` (3,613 conversations):
- an order number appears in **~22.2% of conversations** but only **~12.4% of first customer messages**
- phone numbers appear in **~28.4% of conversations** but only **~7.5% of first customer messages**
This supports our design: many customers do **not** provide deterministic identifiers up front, so Tier 2 automation must be gated and Tier 1 “ask for order #” must exist.

---

## Definitions

### Model intent confidence (raw)
A number produced by the model (0–1).  
**We treat it as a score, not a calibrated probability.**

### Margin
`margin = top1_confidence - top2_confidence`  
Low margin means ambiguity / multi-intent risk.

### Routing confidence (post-processed)
A derived score the middleware uses to decide if we should **apply routing tags/assignment**.

Recommended v1 computation (simple and safe):
- start with `top1_confidence`
- apply penalties:
  - **-0.10** if margin < 0.10 (ambiguous)
  - **-0.10** if customer message is very short (< 5 words) or non-text-only
  - **-0.10** if model marks multi-intent (or returns 2+ intents > 0.55)

### Automation confidence (post-gated)
A derived score used only for Tier 2 verified automation.

Recommended v1 computation:
- if `deterministic_match == false`: automation_confidence = 0
- else automation_confidence = `min(routing_confidence, tier2_verifier_confidence)`

---

## Tier rules (summary)
- **Tier 0:** never automate. Route to escalation teams with high recall.
- **Tier 1:** safe-assist allowed only if message is clearly in-scope and response is non-sensitive.
- **Tier 2:** verified automation allowed only for order status/tracking flows with deterministic match + verifier approval.
- **Tier 3:** disabled for v1.

See `Decision_Pipeline_and_Gating.md` and `Acceptance_Criteria_and_Rollout_Stages.md`.

---

## v1 threshold defaults (recommended)

### A) Routing thresholds (route-only)
| Case | Rule | Action |
|---|---|---|
| Tier 0 detected (keywords or model) | always | route to escalation (Chargebacks/Leadership) |
| routing_confidence ≥ 0.60 | yes | apply routing tags + route to destination team |
| 0.50 ≤ routing_confidence < 0.60 | maybe | apply tag `mw-uncertain` + route to Email Support Team (manual triage) |
| routing_confidence < 0.50 | no | route to Email Support Team + tag `mw-needs-manual-triage` |

### B) Tier 1 safe-assist thresholds (generic, non-sensitive)
Tier 1 safe-assist is allowed only for intents whose “assist” message does **not** disclose sensitive data.
Recommended:
- require `routing_confidence ≥ 0.60`
- require **no Tier 0 flags**
- require **not multi-intent ambiguous** (margin ≥ 0.10)

### C) Tier 2 verified automation thresholds (order status/tracking)
Tier 2 automation allowed only when ALL are true:
1) intent in allowed set:
   - `order_status_tracking`
   - `shipping_delay_not_shipped` (treated as order status variant)
2) `routing_confidence ≥ 0.70`
3) `deterministic_match == true`
4) Tier 2 verifier:
   - `verified == true`
   - `tier2_verifier_confidence ≥ 0.80`
5) no Tier 0 flags present

If any condition fails:
- do not send a customer-specific reply
- fall back to Tier 1 ask-for-order# (if applicable) or route-only

---

## Intent-specific overrides (v1)
We bias thresholds by risk.

- **chargeback_dispute / fraud_suspected / legal_threat / harassment_threats**
  - no thresholds: Tier 0 override (escalate even at low confidence)
- **return_request / refund_request / exchange_request**
  - route threshold 0.60, allow Tier 1 intake (ask for photos/order#) at 0.65, never Tier 2
- **technical_support**
  - route threshold 0.60, allow Tier 1 troubleshooting questions at 0.70
- **cancel_order / address_change_order_edit / cancel_subscription**
  - route threshold 0.60, allow Tier 1 “please confirm order #” at 0.65, never Tier 2

---

## Calibration plan (how we make confidence real)

### 1) Build a golden set
- 300–500 human-labeled conversations (stratified by intent and risk tier)
- include multi-intent and adversarial cases from `Adversarial_and_Edge_Case_Test_Suite.md`

### 2) Measure calibration
- reliability diagrams / ECE (Expected Calibration Error)
- confusion matrices by intent and by destination team
- separate evaluation for Tier 2 automation eligibility and safety

### 3) Improve confidence without changing models
- clearer intent definitions + examples
- negative examples (“what this is NOT”)
- separate verifier model for Tier 2
- add lightweight heuristics for Tier 0 detection

### 4) Threshold tuning
Tune thresholds per intent to optimize:
- Tier 0 recall (avoid misses)
- Tier 2 precision (avoid false positives)
- overall routing macro F1

---

## Storage and versioning
Thresholds must be:
- configuration-driven (no redeploy required)
- versioned (linked to model/prompt version)
- auditable (Decision Log + Change Log)

See `Model_Config_and_Versioning.md`.
