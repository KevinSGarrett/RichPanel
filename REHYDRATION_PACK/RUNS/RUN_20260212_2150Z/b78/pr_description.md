# PR Description

<!-- PR_QUALITY: title_score=95/100; body_score=95/100; rubric_title=07; rubric_body=03; risk=risk:R1; p0_ok=true; timestamp=2026-02-12 -->

**Run ID:** `RUN_20260212_2150Z`  
**Agents:** B  
**Labels:** `risk:R1`, `gate:claude`  
**Risk:** `risk:R1`  
**Claude gate model (used):** `pending — @cursor review`  
**Anthropic response id:** `pending — @cursor review`  

### 1) Summary
- Add Shopify order tags to `order_summary` as read-only extraction.
- Store both raw tags string and parsed list with stable dedupe.
- Update fixtures and tests for tags parsing and enrichment.

### 2) Why
- **Problem / risk:** Current preorder detection should use Shopify order tags but they are not extracted.
- **Pre-change failure mode:** Downstream logic cannot detect preorder tags from Shopify orders.
- **Why this approach:** Additive extraction only, enabling follow-up ETA logic without changing behavior now.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- No changes to ETA logic or draft reply content.
- Only adds `order_tags_raw` and `order_tags` when Shopify provides tags.
- No outbound writes; read-only extraction.

**Non-goals (explicitly not changed):**
- Delivery estimate logic remains unchanged.
- Routing logic and messaging remain unchanged.
- No customer contact or Shopify writes.

### 4) What changed
**Core changes:**
- Added `tags` to Shopify order field lists.
- Added `_parse_shopify_tags` helper for trim + stable dedupe.
- Extracted tags into `order_summary` with `setdefault` to avoid overwrites.

**Design decisions (why this way):**
- Preserve Shopify-provided casing and order.
- Fail-closed: no tags added if missing or empty.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/commerce/order_lookup.py`

**Tests:**
- `scripts/test_order_lookup.py`
- `scripts/fixtures/order_lookup/shopify_order.json`
- `scripts/fixtures/order_lookup/shopify_order_gid.json`

**CI / workflows:**
- (None)

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/b78/agent_b.md`
- `REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/RUN_SUMMARY.md`
- `REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/STRUCTURE_REPORT.md`
- `REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/DOCS_IMPACT_MAP.md`
- `REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/TEST_MATRIX.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python -m unittest scripts.test_order_lookup`
- `python -m unittest discover -s scripts -p "test_*.py"` (AWS_REGION=us-east-2)
- `python -m pytest -q scripts/test_order_lookup.py`
- `python scripts/run_ci_checks.py --ci`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- Not run (extraction-only change).

### 7) Results & evidence
**CI:** pending — `<link>`  
**Codecov:** pending — `<direct Codecov PR link>`  
**Bugbot:** pending — `<PR link>` (trigger via `@cursor review`)  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/b78/agent_b.md`

**Proof snippet(s) (PII-safe):**
```text
python -m pytest -q scripts/test_order_lookup.py
122 passed in 50.52s
```

### 8) Risk & rollback
**Risk rationale:** `risk:R1` — additive tag extraction only.

**Failure impact:** Missing or incorrect tags in order summary could block preorder detection in follow-up logic.

**Rollback plan:**
- Revert PR
- No cleanup steps required
- Re-run `python -m pytest -q scripts/test_order_lookup.py`

### 9) Reviewer + tool focus
**Please double-check:**
- Tag extraction respects additive-only behavior.
- Tag parsing preserves order and casing while deduping.

**Please ignore:**
- Generated registries / line number shifts unless CI fails.
- Rehydration pack artifacts except referenced proof files.
