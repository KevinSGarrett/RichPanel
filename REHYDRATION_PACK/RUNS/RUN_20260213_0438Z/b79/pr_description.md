<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-13 -->

**Run ID:** `RUN_20260213_0438Z`  
**Agents:** A  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-sonnet-4-5-20250929`  
**Anthropic response id:** `msg_0182fTkBCENDxPgzMBnLqLry`

### 1) Summary
- Pre-order detection based ONLY on Shopify order tag with fail-closed behavior.
- Ship date = order_date + 45 calendar days; delivery = ship_date + shipping business-day window.
- Non-preorder reply output unchanged (bit-for-bit), verified by regression test.
- No outbound writes; no customer contact; read-only development.

### 2) Why
- **Problem / risk:** Pre-order ETA logic was incorrect (product IDs + fixed date), causing wrong ship/ETA messaging.
- **Pre-change failure mode:** Tag-marked pre-orders could receive a fixed ship date and incorrect delivery window.
- **Why this approach:** Shopify order tags are the source of truth for pre-order status; using +45 calendar days preserves policy and stays deterministic.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Pre-order detection uses only order tags (`order_tags` or `order_tags_raw`), not product IDs.
- Ship date is always `order_date + 45` calendar days for preorder-tagged orders.
- Delivery window uses business days from ship date and never falls back to standard estimates for preorder.
- Non-preorder reply body is bit-for-bit unchanged.
- No outbound writes during development; tests run with read-only env flags.

**Non-goals (explicitly not changed):**
- Tracking-present reply flow.
- Standard (non-preorder) delivery estimate logic.

### 4) What changed
**Core changes:**
- Added tag-based preorder detection helper and rebuilt preorder ETA computation.
- Updated no-tracking preorder reply copy to include ship date + ship/arrival day windows.
- Pipeline now passes order tags and removes product-id enrichment for preorder detection.

**Design decisions (why this way):**
- Fail-closed tag detection to avoid false positives.
- Keep non-preorder branch identical to preserve regression behavior.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/delivery_estimate.py`
- `backend/src/richpanel_middleware/automation/pipeline.py`

**Tests:**
- `scripts/test_delivery_estimate.py`
- `scripts/test_pipeline_handlers.py`
- `scripts/test_read_only_shadow_mode.py`
- `scripts/test_order_status_send_message.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/00_Project_Admin/Progress_Log.md`
- `docs/_generated/doc_outline.json`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_registry.json`
- `docs/_generated/heading_index.json`
- `REHYDRATION_PACK/RUNS/RUN_20260213_0438Z/b79/agent_a.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python -m unittest scripts.test_delivery_estimate`
- `python -m unittest scripts.test_pipeline_handlers`
- `python -m unittest discover -s scripts -p "test_*.py"`
- `python -m pytest -q scripts/test_delivery_estimate.py`
- `python -m pytest -q scripts/test_pipeline_handlers.py`
- `python scripts/run_ci_checks.py --ci`

**Env flags set for tests:**
- `RICHPANEL_READ_ONLY=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `RICHPANEL_OUTBOUND_ENABLED=false`
- `SHOPIFY_WRITE_DISABLED=true`

### 7) Results & evidence
**CI:** pending â€” https://github.com/KevinSGarrett/RichPanel/pull/248/checks  
**Codecov:** pending â€” https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/248  
**Bugbot:** N/A â€” workflow retired; checks link: https://github.com/KevinSGarrett/RichPanel/pull/248/checks

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/RUN_20260213_0438Z/b79/agent_a.md`

**Proof snippet(s) (PII-safe):**
```text
Ran 34 tests in 0.010s â€” OK
Ran 206 tests in 52.340s â€” OK
[OK] CI-equivalent checks passed.
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` â€” Order-status messaging changes affect preorder ETA copy and timing calculations.

**Failure impact:** Incorrect ship/ETA messaging for preorder-tagged orders.

**Rollback plan:**
- Revert PR.
- Re-run `python scripts/run_ci_checks.py --ci`.
- Spot-check preorder example unit test for expected window.

### 9) Reviewer + tool focus
**Please double-check:**
- Tag normalization and fail-closed detection in `has_preorder_tag()`.
- Preorder ETA calculation and business-day window in `compute_preorder_delivery_estimate()`.
- No-tracking reply preorder branch formatting and non-preorder regression.
- Pipeline tag wiring and removal of product-id enrichment.

**Please ignore:**
- Generated doc registries unless CI fails.
- Rehydration pack artifacts except referenced proof file.
