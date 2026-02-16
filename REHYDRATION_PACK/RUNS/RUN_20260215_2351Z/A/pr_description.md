<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-15 -->

**Run ID:** `RUN_20260215_2351Z`  
**Agents:** A  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_01PDPjEBRFf5bFkDenjtSoEJ`

### 1) Summary
- Added a preorder-only fallback window for "Pre-order Delivery" so replies include delivery window and days.
- Kept non-preorder ETA logic unchanged with a regression test.
- Fixed shadow-eval routing intent classification for current order-status intents.

### 2) Why
- **Problem / risk:** Preorder orders using "Pre-order Delivery" lacked delivery window/arrives-in-days in the reply.
- **Pre-change failure mode:** Preorder ETA computation returned ship date only when normalization failed.
- **Why this approach:** Narrow fallback only in preorder path preserves non-preorder behavior and fail-closed logic.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Non-preorder orders use the exact same ETA behavior as before.
- Preorder ship date = order_created_date + 45 calendar days.
- Delivery window uses business-day addition from ship date when shipping method window is known.
- Unknown preorder shipping methods still return ship date only.
- No outbound messaging paths are introduced.

**Non-goals (explicitly not changed):**
- Tracking-present reply flow.
- Default shipping method transit map for non-preorders.

### 4) What changed
**Core changes:**
- Added preorder-only fallback window for "Pre-order Delivery" variants in `compute_preorder_delivery_estimate`.
- Updated shadow-eval route decision classification to recognize current order-status intents.
- Added unit tests for preorder fallback and route decision classification.

**Design decisions (why this way):**
- Match only explicit "Pre-order Delivery" variants to avoid widening non-preorder logic.
- Keep normalization logic unchanged outside preorder path.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/delivery_estimate.py`
- `scripts/live_readonly_shadow_eval.py`

**Tests:**
- `backend/tests/test_delivery_estimate_fallback.py`
- `scripts/test_live_readonly_shadow_eval.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/00_Project_Admin/Progress_Log.md`
- `docs/_generated/*`
- `REHYDRATION_PACK/RUNS/RUN_20260215_2351Z/A/RUN_REPORT.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/run_ci_checks.py --ci`
- `pytest -q` (with `AWS_REGION=us-east-2`)

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- None

### 7) Results & evidence
**CI:** pending — PR not opened  
**Codecov:** pending — PR not opened  
**Bugbot:** pending — PR not opened

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/RUN_20260215_2351Z/A/RUN_REPORT.md`

**Proof snippet(s) (PII-safe):**
```text
1528 passed, 14 subtests passed in 226.65s (0:03:46)
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — Preorder ETA messaging changes can affect customer-facing delivery expectations.

**Failure impact:** Incorrect preorder delivery window or days in draft replies.

**Rollback plan:**
- Revert PR.
- Re-run `python scripts/run_ci_checks.py --ci`.
- Verify preorder fallback test case output.

### 9) Reviewer + tool focus
**Please double-check:**
- Preorder-only fallback matching in `compute_preorder_delivery_estimate`.
- Non-preorder regression test ensuring no behavior change.
- Route decision classification updates for shadow-eval.

**Please ignore:**
- Generated registries / line number shifts unless CI fails.
- Rehydration pack artifacts except referenced proof files.
