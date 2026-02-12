<!-- PR_QUALITY: title_score=100/100; body_score=95/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-12 -->

**Run ID:** `RUN_20260212_0204Z`  
**Agents:** A  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-opus-4-5-20251101`  
**Anthropic response id:** `msg_01GnyPy6zpfGy7mwxECax5Ag`  

### 1) Summary
- Add preorder-aware ETA computation + reply branch for no-tracking order status.
- Enrich line item product IDs on-demand to detect preorder products.
- Add preorder tests + strict non-preorder reply regression test.
- Fix preorder reply ship-date fallback and omit negative day windows.

### 2) Why
- **Problem / risk:** preorder orders need deterministic ETA that references the known ship date.
- **Pre-change failure mode:** preorder orders received standard ETA wording without ship-date context.
- **Why this approach:** additive, fail-closed preorder logic gated on known product IDs + order date.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Non-preorder output unchanged (bit-for-bit).
- Fail-closed on missing/invalid data: standard logic used.
- No writes or outbound messages introduced.

**Non-goals (explicitly not changed):**
- No changes to tracking-present paths or non-order-status intents.
- No changes to standard ETA computation.

### 4) What changed
**Core changes:**
- Add preorder catalog/constants, canonicalization, detection, and ETA compute.
- Update no-tracking reply to include preorder ship date and items when applicable.
- Enrich `line_item_product_ids` for preorder detection when missing (allow-network only).
- Guard preorder reply ship date fallback and suppress negative “in X–Y days”.

**Design decisions (why this way):**
- Keep preorder computation separate to preserve existing ETA logic.
- Deterministic formatting and ordering for stable output.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/automation/delivery_estimate.py`
- `backend/src/richpanel_middleware/automation/pipeline.py`

**Tests:**
- `scripts/test_delivery_estimate.py`
- `scripts/test_read_only_shadow_mode.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/00_Project_Admin/Progress_Log.md`
- `docs/_generated/doc_registry.json`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_outline.json`
- `docs/_generated/heading_index.json`
- `REHYDRATION_PACK/RUNS/RUN_20260212_0204Z/b77/agent_a.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python -m unittest scripts.test_delivery_estimate`
- `python -m unittest discover -s scripts -p "test_*.py"`
- `python -m pytest -q scripts/test_delivery_estimate.py`
- `python scripts/run_ci_checks.py --ci`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- None

### 7) Results & evidence
**CI:** pass — https://github.com/KevinSGarrett/RichPanel/actions/runs/21933126956/job/63341272855  
**Codecov:** pass (patch 96.07%) — https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/244  
**Bugbot:** triggered via https://github.com/KevinSGarrett/RichPanel/pull/244#issuecomment-3888342105 (no findings posted)  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/RUN_20260212_0204Z/b77/agent_a.md`

**Proof snippet(s) (PII-safe):**
```text
python -m unittest scripts.test_delivery_estimate  # PASS
python -m pytest -q scripts/test_delivery_estimate.py  # PASS (30 tests)
python scripts/test_pipeline_handlers.py  # PASS
AWS_PROFILE=rp-admin-prod AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 python -m unittest discover -s scripts -p "test_*.py"  # PASS
python scripts/run_ci_checks.py --ci  # PASS
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — adds preorder-specific ETA + reply branch in order-status flow.

**Failure impact:** preorder orders may show a standard ETA or missing preorder details; non-preorder behavior must remain identical.

**Rollback plan:**
- Revert PR
- Re-run `python scripts/run_ci_checks.py --ci`

### 9) Reviewer + tool focus
**Please double-check:**
- Preorder gating conditions (product IDs + created_at < ship date).
- Fail-closed behavior and non-preorder reply regression.
- Preorder reply wording includes ship date and items.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
