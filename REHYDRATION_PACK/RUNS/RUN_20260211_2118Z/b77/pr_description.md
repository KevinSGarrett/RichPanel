<!-- PR_QUALITY: title_score=100/100; body_score=95/100; rubric_title=07; rubric_body=03; risk=risk:R1; p0_ok=true; timestamp=2026-02-11 -->

**Run ID:** `RUN_20260211_2118Z`  
**Agents:** B  
**Labels:** `risk:R1`, `gate:claude`  
**Risk:** `risk:R1`  
**Claude gate model (used):** `pending — @cursor review`  
**Anthropic response id:** `pending — @cursor review`  

### 1) Summary
- Add Shopify line item product ID extraction to order summaries.
- Add opt-in enrichment to fetch only line item product IDs when requested.
- Expand tests/fixtures to cover numeric and GID product IDs.

### 2) Why
- **Problem / risk:** Pre-order detection needs product IDs from Shopify line items.
- **Pre-change failure mode:** Order summaries lacked product IDs for pre-order logic.
- **Why this approach:** Additive extraction + opt-in fetch keeps default behavior unchanged.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Existing summary keys/values remain unchanged unless opt-in flag is used.
- No new writes and no changes to ETA logic or messaging.
- Enrichment fail-closed: if Shopify fetch fails, summary is unchanged.

**Non-goals (explicitly not changed):**
- No modification to non-preorder ETA logic.
- No changes to messaging content or outbound write paths.

### 4) What changed
**Core changes:**
- Extract `line_item_product_ids` from Shopify `line_items` (numeric + GID forms).
- Add `require_line_item_product_ids` opt-in enrichment path for minimal Shopify fetch.
- Add test fixtures and assertions for product ID extraction.

**Design decisions (why this way):**
- Keep extraction in Shopify-only helper for predictable behavior.
- Use minimal field fetch to reduce payload while preserving safety.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/commerce/order_lookup.py`

**Tests:**
- `scripts/test_order_lookup.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/00_Project_Admin/Progress_Log.md`
- `docs/_generated/doc_registry.json`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_outline.json`
- `docs/_generated/heading_index.json`
- `REHYDRATION_PACK/RUNS/RUN_20260211_2118Z/b77/agent_b.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python -m unittest scripts.test_order_lookup`
- `python -m unittest discover -s scripts -p "test_*.py"`
- `python -m pytest -q scripts/test_order_lookup.py`
- `python scripts/run_ci_checks.py --ci`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- None

### 7) Results & evidence
**CI:** pending — `<link>`  
**Codecov:** pending — `<direct Codecov PR link>`  
**Bugbot:** pending — `<PR link>` (trigger via `@cursor review`)  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/RUN_20260211_2118Z/b77/agent_b.md`

**Proof snippet(s) (PII-safe):**
```text
[OK] CI-equivalent checks passed.
```

### 8) Risk & rollback
**Risk rationale:** `risk:R1` — additive read-only extraction with opt-in enrichment.

**Failure impact:** Product IDs missing from summaries; no change to fulfillment/ETA.

**Rollback plan:**
- Revert PR
- No data cleanup required
- Re-run `python scripts/run_ci_checks.py --ci`

### 9) Reviewer + tool focus
**Please double-check:**
- Additive behavior and opt-in gating in `lookup_order_summary()`.
- GID/numeric product ID normalization and uniqueness ordering.

**Please ignore:**
- Generated registries / line number shifts unless CI fails.
- Rehydration pack artifacts except referenced proof files.
