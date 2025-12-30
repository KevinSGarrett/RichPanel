# Quality Monitoring and Drift Detection (Wave 08)

Last updated: 2025-12-22

This document defines how we detect when routing/automation quality is degrading **in production**.

Key concept: production monitoring combines:
- **explicit signals** (agent overrides, “wrong route” tags)
- **implicit signals** (template usage anomalies, confidence drift, escalation spikes)
- **periodic evaluation** (golden set + fresh samples)

---

## 1) Quality signals (what we measure)

### A) Explicit feedback signals (highest value)
These signals require small Support Ops behaviors/macros:
- “misrouted” tag applied by agent
- “auto reply wrong” tag applied by agent
- “needs human / escalation” tag applied by agent (when automation was attempted)

Spec is defined in:
- `Feedback_Signals_and_Agent_Override_Macros.md`

### B) Implicit quality proxies (useful but weaker)
- high rate of ticket reassignment shortly after routing
- high rate of follow-up messages immediately after an auto reply (customer confusion)
- high “automation blocked” rate (model outputs risky/ambiguous)
- increase in “other/unknown” intent rate (if used)

### C) Periodic eval metrics (ground truth)
- Golden set results:
  - macro F1
  - per-intent precision/recall
  - Tier 0 FN/FP = 0 targets
- Fresh sample QA:
  - estimated real-world accuracy with current traffic

---

## 2) Drift types and detection rules

### Drift type 1 — Intent distribution drift
Detection:
- Compare last 7 days vs trailing 28 day baseline
- Alert if:
  - any single intent share changes by > **X% absolute**
  - “unknown/other” share increases by > **Y% absolute**

### Drift type 2 — Confidence drift
Detection:
- Track confidence histograms (bin counts) per channel
- Alert if:
  - mean confidence drops by > **0.08** from baseline
  - low-confidence bin share increases sharply

### Drift type 3 — Template mix drift
Detection:
- Track template_id counts
- Alert if:
  - one template becomes > **2×** its baseline share without a product/policy change
  - Tier 2 template usage drops significantly (possible order-linking break)

### Drift type 4 — Override drift
Detection:
- Track explicit override tags/macros
- Alert if:
  - misroute tag rate > **target threshold**
  - “auto reply wrong” rate increases week-over-week

### Drift type 5 — Safety/Policy drift
Detection:
- automation blocked reason-code mix changes
- Tier 0 detections suddenly drop to near zero (possible prompt regression)
- increase in “schema invalid fail closed” events

---

## 3) Alerting and response playbooks

### A) “Quality regression suspected” response
1) Check the “Quality” dashboard:
   - confidence distribution
   - override signals
   - template mix
2) If customer harm is plausible:
   - enable **safe_mode=true** (route-only)
   - optionally set `automation_enabled=false`
3) Identify the cause:
   - release/prompt/template version change?
   - vendor outages?
   - product/policy change (promotions, shipping delays)?
4) Open a calibration ticket:
   - sample and label fresh cases
   - run eval harness against golden set
   - adjust thresholds or templates as needed

### B) “Order automation degraded” response
- If deterministic match success rate drops:
  - suspect order-linking or API changes
  - disable Tier 2 templates temporarily (template flags)
  - fall back to Tier 1 “ask for order #” template

---

## 4) Where the data comes from

| Signal | Source | Storage |
|---|---|---|
| decision events | middleware logs | CloudWatch + optional S3 export |
| blocked automation reasons | policy events | CloudWatch + optional S3 export |
| override tags | Richpanel actions or agent macros | logs/export |
| eval metrics | eval harness output | S3 (sanitized) |
| queue health | CloudWatch metrics | CloudWatch |

---

## 5) Ownership and cadence (v1)
- Engineering owns dashboards/alarms and kill switch operations
- Support Ops owns override macro usage and QA review process
- Weekly quality review meeting is recommended in early rollout

---

## 6) Related docs
- EvalOps runbooks: `EvalOps_Scheduling_and_Runbooks.md`
- Kill switch: `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- Routing + thresholds: `docs/04_LLM_Design_Evaluation/Confidence_Scoring_and_Thresholds.md`
