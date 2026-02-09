<!-- PR_QUALITY: title_score=98/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-09 -->

**Run ID:** `RUN_B75_A_TRACKING_URL`  
**Agents:** A  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `pending`  

### 1) Summary
- Add deterministic carrier tracking URL generation when Shopify `tracking_url` is missing.
- Preserve existing tracking URLs and keep reply/summary consistent with effective URL.
- Add unit tests covering carrier variants, encoding, and override behavior.

### 2) Why
- **Problem / risk:** Replies showed `Tracking link: (not available)` even when carrier + tracking number existed.
- **Why this approach:** deterministic templates restore a reliable tracking link without external calls.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- If `tracking_url` exists, it is **not** overridden.
- If `tracking_url` missing but carrier + tracking number present, generate official carrier URL.
- No PII in tests or artifacts; tracking numbers are synthetic placeholders only.

**Non-goals (explicitly not changed):**
- No changes to Shopify fetch logic or order lookup.
- No changes to reply wording beyond effective tracking URL.

### 4) What changed
**Core changes:**
- Added `build_tracking_url()` with carrier normalization and official templates.
- Updated `build_tracking_reply()` to use generated URL when missing.
- Added unit tests in `scripts/test_delivery_estimate.py`.

**Design decisions (why this way):**
- Single helper keeps URL construction consistent and testable.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/delivery_estimate.py`

**Tests:**
- `scripts/test_delivery_estimate.py`

**Artifacts / docs:**
- `REHYDRATION_PACK/RUNS/B75/A/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B75/A/CHANGES.md`
- `REHYDRATION_PACK/RUNS/B75/A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B75/A/PROOF/secrets_preflight_dev.json`
- `REHYDRATION_PACK/RUNS/B75/A/PROOF/tracking_url_unit_proof.json`

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/test_delivery_estimate.py`

### 7) Results & evidence
**CI:** not run locally  
**Codecov:** not run locally  
**Bugbot:** not run locally  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B75/A/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B75/A/PROOF/tracking_url_unit_proof.json`
- `REHYDRATION_PACK/RUNS/B75/A/PROOF/secrets_preflight_dev.json`

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — touches tracking reply generation logic.

**Failure impact:** Tracking links may be missing or malformed for supported carriers.

**Rollback plan:**
- Revert this PR to restore previous behavior.

### 9) Reviewer + tool focus
**Please double-check:**
- Carrier normalization and URL templates.
- Tests for override/unknown carriers and URL encoding.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
