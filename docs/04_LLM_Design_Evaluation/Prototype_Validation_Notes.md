# Prototype validation notes (Wave 04)

Last updated: 2025-12-22

## What this is
A Cursor agent produced an **optional offline-eval scaffold** during Wave 04.  
This is **not required** for the documentation plan, but it provides evidence that the Wave 04 design choices (schemas, gating, eval harness) are implementable.

The primary deliverable remains the documentation plan.

---

## Artifact location
The prototype artifacts are stored here (non-production reference):
- `reference_artifacts/cursor_wave04_offline_eval_scaffold/`

Key files:
- `Wave04_LLMEval_Report.md` (implementation report)
- `src/mw_llm/` (prototype package)
- `scripts/run_eval.py` (offline eval runner)
- `tests/` (policy + schema validation tests)
- `artifacts/` (sample output; safe/mock)

---

## Summary of what the prototype implemented
(Condensed from the Cursor run summary and `Wave04_LLMEval_Report.md`.)

- Bootstrapped a python package with:
  - prompt loading
  - strict JSON schema validation for `mw_decision_v1` and `mw_tier2_verifier_v1`
  - redaction helpers (email/phone/order#/tracking-like tokens)
- Implemented:
  - classifier wrapper (structured outputs; fail-closed)
  - Tier 2 verifier wrapper
  - application-layer policy engine:
    - Tier 0 override
    - Tier 2 deterministic-match + verifier approval
    - Tier 3 disabled
- Built an offline eval harness that can:
  - ingest the SC_Data package
  - compute accuracy, macro F1, per-intent precision/recall
  - output confusion matrix CSV
  - report Tier 0 FN/FP and Tier 2 eligibility / violations

---

## What we learn / how this improves the plan
### 1) “Fail closed” is realistic and should be required
The prototype confirms we can enforce:
- strict schema validation
- deterministic fallback behavior when the model output is invalid/unsafe

**Plan update:** Wave 04 docs now treat schema validation + fail-closed fallback as **required**, not optional.

### 2) Policy gates belong in code, not prompts
Prompts can help, but the prototype reinforces:
- the model is advisory
- the middleware must enforce Tier rules in application logic

**Plan update:** We emphasize “policy engine gates everything” in `Decision_Pipeline_and_Gating.md`.

### 3) Offline eval harness is feasible with your dataset
The SC_Data format works well for building an internal eval harness.  
This reduces risk of shipping prompt changes without measurement.

**Plan update:** We link Wave 04 eval design directly to the SC_Data package profile and define acceptance criteria + rollout stages.

---

## Important caveats
- Sample metrics in the prototype report used a **mock model + tiny mock label set**, so they are **not performance indicators**.
- Real evaluation requires:
  - a human-labeled dataset (golden set)
  - stable intent definitions + adjudication rules
  - calibration work (confidence is not inherently calibrated)

---

## Next steps (documentation plan)
1) Finalize v1 threshold defaults + acceptance bands (Wave 04)
2) Define the adversarial/edge-case test suite (Wave 04)
3) Define labeling + adjudication SOP and sampling plan (Wave 04)
