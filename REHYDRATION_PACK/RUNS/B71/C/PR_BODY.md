<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-05 -->

**Run ID:** `RUN_20260205_1637Z`  
**Agents:** C  
**Risk:** `risk:R2`  
**Claude gate:** Opus 4.5  

### 1) Summary
- Fail-loud OpenAI routing banners and deterministic-only guardrails added to shadow eval entrypoints.
- Added `--openai-shadow-eval` wrapper to enforce correct read-only OpenAI routing defaults.
- Ran prod OpenAI shadow eval in 25-ticket batches (200 total) and generated PII-safe summary + metrics.
- Self-score: 8/10 (rate slightly above expected band; needs follow-up on distribution drivers).

### 2) Why
- **Problem / risk:** Shadow evals can silently run with OpenAI routing off, producing invalidly low order-status rates.
- **Pre-change failure mode:** Runs with OpenAI gated would proceed without explicit warning/override.
- **Why this approach:** Fail-closed at startup and provide a single flag to enforce correct routing gates.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Read-only prod shadow remains GET-only; no Richpanel writes.
- OpenAI routing status is printed with gating blockers and fails without explicit override.
- `--openai-shadow-eval` sets OpenAI routing + shadow flags while keeping outbound disabled.

**Non-goals (explicitly not changed):**
- Deterministic router behavior (no rule changes).
- Shopify/Richpanel client behavior outside shadow evaluation.

### 4) What changed
**Core changes:**
- Added startup banner + hard guard in shadow eval scripts when OpenAI routing is disabled.
- Added `--openai-shadow-eval` / `--allow-deterministic-only` CLI flags in shadow eval entrypoints.
- Updated tests to include OpenAI routing defaults where needed.

**Design decisions (why this way):**
- Prevent invalid measurements by requiring an explicit override when routing is gated.
- Keep changes localized to eval entrypoints and guard logic.

### 5) Scope / files touched
**Runtime code:**
- `scripts/live_readonly_shadow_eval.py`
- `scripts/shadow_order_status.py`
- `scripts/prod_shadow_order_status_report.py`

**Tests:**
- `scripts/test_live_readonly_shadow_eval.py`
- `scripts/test_shadow_order_status.py`

**CI / workflows:**
- (None)

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_order_status_report_batch01.json`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_order_status_report_batch02.json`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_order_status_report_batch03.json`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_order_status_report_batch04.json`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_order_status_report_batch05.json`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_order_status_report_batch06.json`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_order_status_report_batch07.json`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_order_status_report_batch08.json`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_order_status_report_batch09.json`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_openai_200_summary.md`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_openai_200_metrics.json`

### 6) Test plan
**Local / CI-equivalent:**
- Not run (not requested).

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/prod_shadow_order_status_report.py --env prod --openai-shadow-eval --ticket-number <redacted x25> --out-json ..._batch01.json --out-md ..._batch01.md` (repeated for 9 batches; batch04 had 24 tickets due to one invalid ticket)

### 7) Results & evidence
**CI:** `validate` ✅  
**Codecov:** `codecov/patch` ✅ (97.20% >= 93.79%)  
**Bugbot:** ✅  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_openai_200_summary.md`
- `REHYDRATION_PACK/RUNS/B71/C/PROOF/prod_shadow_openai_200_metrics.json`

**Proof snippet(s) (PII-safe):**
```text
ticket_count=200
order_status_rate=0.435
match_rate.order_number=0.724, match_rate.email=0.276
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — eval guardrails and CLI flags; no production routing behavior change.

**Failure impact:** Eval runs could be blocked if OpenAI routing is off without override.

**Rollback plan:**
- Revert PR
- Re-run one small shadow eval to confirm behavior

### 9) Reviewer + tool focus
**Please double-check:**
- Startup guardrails and banner coverage for OpenAI routing.
- `--openai-shadow-eval` flag behavior and env defaults.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
