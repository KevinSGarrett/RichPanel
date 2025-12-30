# LLM Evals in CI

Last updated: 2025-12-22  
Last verified: 2025-12-22 — updated to align with Wave 04 closeout (golden set SOP + multi-intent + regression gates).

## Objective
Prevent prompt/model/schema changes from silently degrading:
- routing quality
- Tier 0 safety (missed escalations)
- Tier 2 verified automation correctness

CI must act as a **gate**, not a dashboard.

---

## Source of truth documents
- Offline eval design: `docs/04_LLM_Design_Evaluation/Offline_Evaluation_Framework.md`
- Golden set creation + QA: `docs/04_LLM_Design_Evaluation/Golden_Set_Labeling_SOP.md`
- Hard/soft thresholds: `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`

---

## What runs in CI (minimum)
### 1) Deterministic unit tests (no model calls)
Must run on every PR:
- routing tag formatting and allowlists
- policy engine invariants (Tier 0 overrides, Tier 2 gating, Tier 3 disabled)
- multi-intent canonicalization (priority matrix)
- redaction utilities (PII removal)
- JSON schema validation for:
  - `mw_decision_v1`
  - `mw_tier2_verifier_v1`

### 2) Golden-set LLM eval (small, fast)
Run on a small golden subset (example: 100–300 examples):
- fixed dataset version + hash
- labels included
- cost/time bounded (fast enough for PR CI)

This run is what enforces the **hard gates**.

### 3) Full offline eval (nightly / on-demand)
Run a larger evaluation (full golden set + extra suites):
- produces confusion matrices, detailed reports, drift indicators
- used for calibration and monitoring
- not required to run on every PR

---

## When CI runs
Run evaluation gates on PRs that modify:
- prompts (`docs/04_LLM_Design_Evaluation/prompts/`)
- schemas (`docs/04_LLM_Design_Evaluation/schemas/`)
- policy logic / thresholds (implementation repo)
- model selection config (implementation repo)

Nightly run:
- scheduled job (optional early, recommended after launch)

---

## Pass/fail criteria
All hard/soft gates are defined in:
- `LLM_Regression_Gates_Checklist.md`

CI should:
- fail the check when **any hard gate** fails
- raise warnings when **soft gates** trigger and require sign-off

---

## Required CI outputs
CI must produce:
- PR markdown summary:
  - dataset version used
  - pass/fail of each hard gate
  - baseline vs current metric deltas (post-baseline)
- saved artifacts:
  - `metrics.json`
  - `confusion_matrix.csv`
  - `tier0_report.json`
  - `tier2_report.json`
  - `invalid_outputs.jsonl` (if any invalid outputs appear)

---

## Notes
- The goal is to prevent *accidental regressions*, not to optimize in CI.
- Never include raw PII in CI logs or artifacts; keep outputs redacted.
