<!-- PR_QUALITY: title_score=95/100; body_score=95/100; rubric_title=07; rubric_body=03; risk=risk:R1; p0_ok=true; timestamp=2026-02-13 -->

**Run ID:** `RUN_20260213_1603Z`  
**Agents:** C  
**Labels:** `risk:R1`, `gate:claude`  
**Risk:** `risk:R1`  
**Claude gate model (used):** `claude-sonnet-4-5`  
**Anthropic response id:** `pending — @cursor review triggered`

### 1) Summary
- Added PII-safe preorder proof signals to live read-only shadow eval output.
- Added unit tests + runbook guidance for preorder tag +45 rule and proof command.
- No runtime behavior change; scripts/tests/docs only.

### 2) Why
- **Problem / risk:** Need auditable, PII-safe proof that preorder detection + ETA rules are correct in prod read-only runs.
- **Pre-change failure mode:** Shadow eval output lacked explicit preorder signal checks without storing reply bodies.
- **Why this approach:** Add a compact, PII-safe signal extractor and wire it to shadow eval reports.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- No customer contact; outbound disabled (no sends/notes/closes/writes).
- No draft reply body stored; only fingerprints + signal booleans are emitted.
- Scripts/tests/docs only; no runtime behavior change.
- Shadow eval intent input concatenates subject + body for analysis; production may differ, so proof runs can diverge from live routing.

**Non-goals (explicitly not changed):**
- Production automation logic.
- Shopify/Richpanel integration behavior in prod runtime.

### 4) What changed
**Core changes:**
- Added `_extract_preorder_proof_signals()` to extract PII-safe preorder signals.
- Wired preorder proof signals into live read-only shadow eval output.
- Combined subject + customer body in shadow eval message extraction (script-only) to align intent classification with production inputs.

**Design decisions (why this way):**
- Use hash fingerprint + boolean checks to avoid persisting raw reply text.

### 5) Scope / files touched
**Runtime code:**
- `scripts/live_readonly_shadow_eval.py`

**Tests:**
- `scripts/test_live_readonly_shadow_eval.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- `docs/00_Project_Admin/Progress_Log.md`
- `REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/preflight_prod.json`
- `REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/preflight_prod.md`
- `REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_report.json`
- `REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_summary.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python -m unittest scripts.test_live_readonly_shadow_eval`
- `python scripts/run_ci_checks.py --ci` (PASS in prod env with read-only flags + SHOPIFY_SHOP_DOMAIN set)

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/live_readonly_shadow_eval.py --env prod --region us-east-2 --expect-account-id 878145708918 --allow-deterministic-only --shopify-probe --request-trace --allow-ticket-fetch-failures --ticket-id <redacted> ... --out REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_report.json --summary-md-out REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_summary.md`

### 7) Results & evidence
**CI:** pending — `https://github.com/KevinSGarrett/RichPanel/pull/249/checks`  
**Codecov:** pending — `https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/249`  
**Bugbot:** pending — `https://github.com/KevinSGarrett/RichPanel/pull/249` (@cursor review triggered)

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/preflight_prod.json`
- `REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/preflight_prod.md`
- `REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_report.json`
- `REHYDRATION_PACK/RUNS/RUN_20260213_1603Z/b80/shadow_eval_prod_summary.md`

**Proof snippet(s) (PII-safe):**
```text
shadow_eval_prod_report.json:
- run_id=RUN_20260213_1729Z
- tickets_scanned=7
- orders_matched=7
- would_reply_send=false (all tickets)
```

### 8) Risk & rollback
**Risk rationale:** `risk:R1` — scripts/tests/docs-only changes; no runtime behavior change.  

**Failure impact:** Missing/incorrect proof signals in read-only reports (no customer impact).  

**Rollback plan:**
- Revert PR
- Re-run read-only shadow eval to confirm proof signals are absent

### 9) Reviewer + tool focus
**Please double-check:**
- Preorder proof signal extraction is PII-safe and correctly wired.
- Runbook guidance aligns with the preorder tag +45 rule.

**Please ignore:**
- Generated registries / line number shifts unless CI fails.
- Rehydration pack artifacts except referenced proof files.
