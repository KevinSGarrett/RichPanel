# Cursor agent tasks (Wave 04) — Optional

Last updated: 2025-12-22

## Purpose
These are **optional** implementation/validation tasks for builders.  
Wave 04 planning does **not** require running Cursor.

If builders want a head start, these tasks implement a non-production harness that:
- validates schema + policy gates
- runs offline evals on SC_Data
- produces metrics artifacts for acceptance criteria checks

## Optional reference artifact
A non-production scaffold already exists here:
- `reference_artifacts/cursor_wave04_offline_eval_scaffold/`

Builders can either:
- reuse it, or
- implement independently following the docs in `docs/04_LLM_Design_Evaluation/`.

## If implementing from scratch (optional)
- Implement strict JSON schema validation for:
  - `mw_decision_v1`
  - `mw_tier2_verifier_v1`
- Implement policy engine gates:
  - Tier 0 override
  - Tier 2 deterministic match + verifier approval
  - Tier 3 disabled
- Implement offline eval runner producing:
  - accuracy, macro/weighted F1
  - per-intent PR
  - confusion matrices
  - Tier 0 FN/FP report
  - Tier 2 eligibility + violation report

Deliverable: a short markdown report + sample artifacts (no PII).
