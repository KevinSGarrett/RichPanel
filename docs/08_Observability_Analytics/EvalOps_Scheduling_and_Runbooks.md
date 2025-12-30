# EvalOps Scheduling and Runbooks (Wave 08)

Last updated: 2025-12-22

EvalOps = “evaluation operations”: the repeatable process to keep routing/automation quality stable in production.

This is the operational counterpart to:
- Wave 04 eval design: `docs/04_LLM_Design_Evaluation/Offline_Evaluation_Framework.md`
- Golden set SOP: `docs/04_LLM_Design_Evaluation/Golden_Set_Labeling_SOP.md`
- Regression gates: `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`

---

## 1) Evaluation cadences (v1)

### Daily: lightweight QA sampling
Goal: catch obvious failures quickly.

Recommended:
- Sample **N = 20–50** tickets/day (or per business day)
- Stratify by:
  - channel (livechat vs email)
  - tier (0/1/2)
  - top intents/templates
- Review outcomes:
  - correct team?
  - correct template?
  - any safety violations?

Output:
- daily QA notes + any incidents flagged
- candidate examples for golden set expansion

### Weekly: golden set regression run
Goal: detect drift and regressions tied to prompt/model/template changes.

Run:
- full golden set eval (same as CI, but with current prod config)
- compare to last baseline

Output:
- weekly metrics summary (macro F1, per-intent PR, Tier 0 FN/FP)
- any threshold recalibration recommendation

### Monthly (or as-needed): calibration + release readiness
Goal: adjust thresholds/prompts/templates based on production behavior.

Run:
- recalibration analysis:
  - confidence threshold tuning
  - template enable/disable decisions
  - new intents (if drift indicates new categories)

Output:
- change proposal:
  - prompt/version update
  - threshold change
  - template update
- release plan (staging → prod) and monitoring checklist

---

## 2) Runbook: “How to run an evaluation”

### Step 1 — Select dataset
- Golden set (versioned)
- Fresh sample set (last 7–14 days)

### Step 2 — Run the harness
The harness should output:
- accuracy + macro F1
- per-intent precision/recall
- confusion matrix (CSV)
- Tier 0 FN/FP report
- Tier 2 eligibility violations report (must be 0 due to code gates)

### Step 3 — Interpret results
- Any Tier 0 FN? → **stop** (do not ship changes)
- Any Tier 2 violation? → investigate policy enforcement
- Large confusion shifts? → review misroute examples and adjust

### Step 4 — Decide actions
- threshold adjust (confidence)
- prompt update
- template update
- safe mode if production harm suspected

### Step 5 — Store artifacts
- **If the sanitized S3 analytics/export pipeline is enabled** (recommended once comfortable):
  - store sanitized eval artifacts in: `s3://<org>-mw-analytics-<env>/eval_runs/`
- **If S3 export is not enabled yet** (CloudWatch-only v1 rollout):
  - store the eval output as CI artifacts (or in a controlled internal bucket) and link it from the Change Log / Decision Log
- Always link the run in Change Log / Decision Log if a change is made


---

## 3) Runbook: “Quality regression in production”

Trigger:
- alarms from `Quality_Monitoring_and_Drift_Detection.md`

Actions:
1) Enable safe mode (route-only) if customer harm possible
2) Pull a sample of recent problem tickets (10–30)
3) Label quickly using SOP
4) Run harness on those samples + golden set
5) Decide mitigation:
   - disable specific templates
   - adjust thresholds
   - roll back prompt/model version
6) Exit safe mode only when:
   - metrics stabilize AND
   - manual QA is clean for a sample window

---

## 4) Ownership + roles
- Engineering:
  - runs the harness, maintains dashboards/exports, manages releases
- Support Ops:
  - provides labelers, uses override macros, participates in weekly review
- Leadership:
  - approves material policy/copy changes when needed (chargebacks, refunds, etc.)

---

## 5) Related docs
- Drift rules: `Quality_Monitoring_and_Drift_Detection.md`
- Feedback macros: `Feedback_Signals_and_Agent_Override_Macros.md`
- Release process: `docs/09_Deployment_Operations/Release_and_Rollback.md`