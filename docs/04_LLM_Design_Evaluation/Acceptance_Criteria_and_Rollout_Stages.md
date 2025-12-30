# Acceptance criteria and rollout stages (Wave 04)

Last updated: 2025-12-22

## Why this matters
Wave 04 defines how the LLM makes routing + automation recommendations.
To prevent “prompt tweaking in production,” we need:
- clear **acceptance criteria** (what “good enough” means)
- a **rollout plan** that starts safe and expands as quality proves out

This document is designed so engineering can implement gates in CI and release checklists.

---

## Definitions
- **Routing**: applying tags / team mapping (no automated customer reply)
- **Tier 1 (safe assist)**: generic, non-sensitive messages (e.g., “please provide order #”)
- **Tier 2 (verified automation)**: customer-specific info (order status/tracking) — requires deterministic match + verifier approval
- **Tier 0**: never automate (chargebacks, fraud, legal threats, harassment)

---

## Acceptance criteria (v1)

### A) Tier 0 safety (highest priority)
Goal: reduce catastrophic failures.

**Must hold on the golden set:**
- **Tier 0 false negatives:** 0 for:
  - `chargeback_dispute`
  - `fraud_suspected`
  - `legal_threat`
  - `harassment_threats`
- **Tier 0 false positives:** allowed (conservative escalation is acceptable in early rollout)

**Implementation requirement (defense-in-depth):**
- Tier 0 intents must be protected by:
  1) model classification **and**
  2) a lightweight keyword heuristic safety net (documented in `Safety_and_Prompt_Injection_Defenses.md`)

### B) Tier 2 automation correctness (order status/tracking)
Goal: never disclose wrong customer-specific info.

**Must hold on golden set:**
- **Tier 2 automation false positives:** 0  
  (automation must not trigger when the message is not actually order status/tracking)
- **Tier 2 deterministic-match violations:** 0  
  (automation can only run when deterministic match is true; enforced in code)
- **Tier 2 verifier overrides:** if verifier says “not verified,” automation must not run

**Expected early limitation:**
- We accept lower Tier 2 coverage at first (more “ask for order #”), as long as it is safe.

### C) Routing quality (route-only)
Routing mistakes are less catastrophic but still costly.

Target metrics on the golden set:
- **Macro F1** (all intents): ≥ **0.75** (v1 target)
- **Weighted F1** (frequency-weighted): ≥ **0.90**
- Top 5 high-volume intents should each have **F1 ≥ 0.85**:
  - `order_status_tracking`
  - `cancel_order`
  - `technical_support`
  - `cancel_subscription`
  - `missing_items_in_shipment`

If the dataset is imbalanced, also track:
- per-intent precision/recall
- confusion matrices by department destination

---

## Rollout stages (recommended)

### Stage 0 — Offline-only (no Richpanel side effects)
- run offline eval harness on labeled data
- iterate prompts + schema until acceptance criteria are met

### Stage 1 — Shadow mode (observe-only)
- middleware runs on real inbound messages
- produces a decision object and logs it
- **does not** apply tags, assign teams, or reply
- collect “would-have-done” analytics

Exit criteria:
- stable decision output rate (no schema failures)
- no Tier 0 misses found in sampled audits

### Stage 2 — Apply tags only (no assignment, no replies)
- middleware applies routing tags in Richpanel
- agents still triage normally (tags assist)

Exit criteria:
- tag accuracy meets routing targets
- no automation loops or conflicts

### Stage 3 — Assignment enabled (route-only)
- middleware assigns to the chosen team/queue (or triggers assignment automation)
- still **no automated customer replies**

Exit criteria:
- handle-time improvements without unacceptable misroutes

### Stage 4 — Tier 1 safe-assist messages (limited)
- enable only for “ask for info” flows (no sensitive info)
- start with a limited channel set (e.g., email only)

Exit criteria:
- no spike in negative feedback
- no “wrong tone” escalations

### Stage 5 — Tier 2 verified automation (order status/tracking)
- enable only when deterministic match + verifier approval
- start with a limited channel set and/or percent rollout

Exit criteria:
- 0 disclosed-wrong-order incidents
- acceptable customer satisfaction impact

---

## Operational kill switches (required)
Before any stage beyond Stage 1:
- “Disable all automation replies” flag
- “Disable all assignments” flag
- “Force route-only fallback” flag

These must be available as configuration (no redeploy required).
---

## Regression gates in CI
Before expanding rollout stages, enforce the CI gates defined in:
- `docs/08_Testing_Quality/LLM_Evals_in_CI.md`
- `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`

These gates ensure:
- schema validity (structured outputs)
- Tier 0 safety (no missed escalations)
- Tier 2/Tier 3 policy invariants
- no unacceptable metric regression once a baseline exists
