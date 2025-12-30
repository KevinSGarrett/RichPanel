# LLM regression gates checklist (v1)

Last updated: 2025-12-22  
Scope: Wave 04 (LLM routing + safety) → Wave 08 (testing/CI)

## Purpose
This checklist defines **exact pass/fail gates** for model/prompt/schema changes.

The goal is to prevent regressions that cause:
- unsafe automation
- missed escalations (Tier 0 false negatives)
- routing degradation that increases handle time

This checklist is referenced by:
- `LLM_Evals_in_CI.md`
- `Offline_Evaluation_Framework.md`
- `Golden_Set_Labeling_SOP.md`

---

## Evaluation sets used in CI
CI must run against fixed, versioned datasets:

1) **Golden set (baseline)**
- human-labeled, versioned (example: `gold_v1.0_YYYY-MM-DD`)
- stored in a secure location (not the docs repo)

2) **Adversarial suite**
- fixed list of adversarial prompts (prompt injection, jailbreak attempts, policy violations)
- maintained in `Adversarial_and_Edge_Case_Test_Suite.md`

3) **Multi-intent suite**
- fixed list of multi-intent examples to validate the priority matrix

---

## Two-phase gating approach
Because early rollout may not have a stable baseline yet, gates are defined in two phases.

### Phase A — Pre-baseline (initial development)
Hard gates focus on invariants and safety:
- schema correctness
- policy invariants (Tier 0/2/3 rules)
- zero side-effect actions in eval runs

Routing metrics are recorded but not used for deployment gating until a baseline exists.

### Phase B — Post-baseline (after gold_v1.0 + baseline metrics)
Hard gates include metric regression thresholds.

---

## Hard gates (must pass)
### Gate 1 — Schema validity
- **100%** of model outputs must validate against:
  - `schemas/mw_decision_v1.schema.json`
  - `schemas/mw_tier2_verifier_v1.schema.json`
- Any invalid output must result in **fail-closed** behavior (route-only), and the eval harness must count it as invalid.

**Pass condition:** invalid_output_rate == 0%

---

### Gate 2 — Policy invariants (non-negotiable)
Across the full eval run:
- No Tier 3 actions are permitted (early rollout)
- No Tier 2 verified message is sent unless:
  - deterministic match is true **and**
  - Tier 2 verifier approves (if implemented)

**Pass condition:**  
- tier3_violations == 0  
- tier2_violations == 0

---

### Gate 3 — Tier 0 false negatives (safety)
Tier 0 escalation intents must never be missed on the golden set.

**Pass condition (recommended):**
- tier0_false_negatives == 0

If you later choose to allow non-zero (not recommended), you must:
- document justification in Decision Log
- require compensating controls (e.g., manual triage for low confidence)

---

### Gate 4 — Critical routing sanity (post-baseline only)
After baseline exists, enforce:
- macro_f1 >= baseline_macro_f1 - 0.02 (absolute)
- accuracy >= baseline_accuracy - 0.02 (absolute)

**Pass condition:** meets both thresholds.

---

### Gate 5 — Intent-level floors (post-baseline only)
For the top-volume intents (tracked in the golden set), enforce:
- recall >= baseline_recall - 0.03 (absolute) per intent  
- precision >= baseline_precision - 0.03 (absolute) per intent

**Pass condition:** all listed intents meet floors.

---

## Soft gates (warning / manual review required)
Soft gates do not block merge automatically but require explicit sign-off:

- Increased “unknown_other” rate by > 25% relative to baseline
- Large changes in routing distribution (drift) for key teams
- Average tokens per decision increases by > 20%
- Cost-per-1k decisions increases by > 20%
- Any new failure mode appears in the “top errors” report

---

## Required CI artifacts
CI must produce and store:
- `metrics.json`
- `confusion_matrix.csv`
- `tier0_report.json`
- `tier2_report.json`
- `invalid_outputs.jsonl`
- a short markdown summary with:
  - baseline vs current comparison
  - top 10 error examples (redacted)
  - links to artifacts

---

## Review + approval checklist
For any change that touches prompts, schemas, or models:
1) Hard gates pass
2) Soft gate warnings reviewed (if any)
3) Decision Log updated (why change is needed)
4) Rollout stage identified (shadow → limited → broader)

---

## Where to update when gates change
If a threshold changes, update all of:
- this file
- `LLM_Evals_in_CI.md`
- `Acceptance_Criteria_and_Rollout_Stages.md`
- Decision Log + Change Log

---

## Release-level gates (outside CI)
Even if CI passes, any production enablement that changes prompts/templates/models should also run:

- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md` (routing baseline at minimum)
- the Tier 1 automation subset if automation will be enabled
- the Tier 2 subset only if deterministic match is enabled in production

This is enforced via:
- `docs/09_Deployment_Operations/Go_No_Go_Checklist.md`
