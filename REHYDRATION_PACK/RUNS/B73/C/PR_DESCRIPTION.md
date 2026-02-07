<!-- PR_QUALITY: title_score=98/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-07 -->

**Run ID:** `RUN_B73_C_AGGREGATE`  
**Agents:** C  
**Risk:** `risk:R2`  
**Claude gate:** pending — `https://github.com/KevinSGarrett/RichPanel/pull/232`  

### 1) Summary
- Report now separates order-status subset match metrics from global counts and adds no-match reason codes.
- B73 prod shadow run completed at 595 tickets with per-batch reports and aggregated evidence.
- Proof artifacts include order-status match/quality rates plus rate-limit diagnostics.

### 2) Why
- **Problem / risk:** B72 global `no_match` rate mixed non-order-status tickets, overstating failures and blocking accurate Shopify match quality answers.
- **Pre-change failure mode:** reporting averaged `no_match` across all tickets; no conditioned metrics or no-match reason codes.
- **Why this approach:** add explicit conditioned metrics + PII-safe reason codes while preserving read-only, rate-limited prod proof runs.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Read-only gating remains enforced (`RICHPANEL_READ_ONLY=true`, `RICHPANEL_WRITE_DISABLED=true`, `RICHPANEL_OUTBOUND_ENABLED=false`).
- Shopify is read-only (`SHOPIFY_OUTBOUND_ENABLED=true`, `SHOPIFY_WRITE_DISABLED=true`); no writes or outbound messaging.
- Proof artifacts remain PII-safe (hashed identifiers, redacted excerpts).
- Request bursts stay ≤ 50 requests / 30s.

**Non-goals (explicitly not changed):**
- No changes to ticket acquisition endpoints or richpanel client behavior.
- No changes to Shopify lookup logic or routing classifier internals.

### 4) What changed
**Core changes:**
- Compute order-status subset metrics (match rate, tracking/ETA rates) and include them in report JSON/MD.
- Emit per-ticket `no_match_reason` and aggregate top no-match reasons.
- Aggregate 12 batch reports into a single B73 report with summary + run meta.
- Mark B73 proof JSONs as binary diff to keep PR diffs under review limits.
- Minify B73 proof JSON files to keep the PR diff under the Claude gate limit.

**Design decisions (why this way):**
- Use existing order-resolution diagnostics to map no-match reasons without exposing PII.
- Keep batch size at 50 to avoid Cursor timeouts while preserving >=500 ticket coverage.
- Suppress large JSON diffs so Claude gate can fetch the PR diff.
- Store proof JSONs as compact JSON to keep diff line count under GitHub limits.

### 5) Scope / files touched
**Runtime code:**
- `scripts/prod_shadow_order_status_report.py`
**Repo config:**
- `.gitattributes`

**Tests:**
- `scripts/test_shadow_order_status.py`

**CI / workflows:**
- None

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report.json`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report.md`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/analysis_summary.md`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/run_meta.json`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report_batch_*.json`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report_batch_*.md`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/run_meta_batch_*.json`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/batch_*_ticket_refs.txt`

**Hot files:**
- `scripts/prod_shadow_order_status_report.py`
- `scripts/test_shadow_order_status.py`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report.json`

### 6) Test plan
**Local / CI-equivalent:**
- Not run (no `python scripts/run_ci_checks.py --ci`).

**E2E / proof runs (PII-safe):**
- Ran 12 batches at 50 tickets each with 1.0 rps throttling:
  - `python scripts/prod_shadow_order_status_report.py --env prod --region us-east-2 --ticket-refs-path REHYDRATION_PACK/RUNS/B73/C/PROOF/batch_01_ticket_refs.txt --throttle-seconds 1.0 --retry-diagnostics --request-trace --openai-shadow-eval --aws-profile rp-admin-prod --expect-account-id 878145708918 --richpanel-secret-id rp-mw/prod/richpanel/api_key --shopify-secret-id rp-mw/prod/shopify/admin_api_token --require-secret rp-mw/prod/richpanel/api_key --require-secret rp-mw/prod/openai/api_key --require-secret rp-mw/prod/shopify/admin_api_token --out-json REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report_batch_01.json --out-md REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report_batch_01.md --retry-proof-path REHYDRATION_PACK/RUNS/B73/C/PROOF/run_meta_batch_01.json`
  - Same command repeated for `batch_02` … `batch_12` with matching output paths.

### 7) Results & evidence
**CI:** pending — `https://github.com/KevinSGarrett/RichPanel/pull/232/checks`  
**Codecov:** pending — `https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/232`  
**Bugbot:** pending — `https://github.com/KevinSGarrett/RichPanel/pull/232` (trigger via `@cursor review`)  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report.json`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report.md`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/analysis_summary.md`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/run_meta.json`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/prod_shadow_report_batch_*.json`
- `REHYDRATION_PACK/RUNS/B73/C/PROOF/run_meta_batch_*.json`

**Proof snippet(s) (PII-safe):**
```text
order_status_rate: 0.355
order_status_match_rate: 0.919
tracking_present_rate (matched only): 0.918
eta_available_rate (matched only): 0.067
max_requests_30s: 15
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — reporting logic changes and new metrics could misstate results if miscomputed, but no production writes or behavior changes.

**Failure impact:** Incorrect match-rate interpretation and misleading operational decisions.

**Rollback plan:**
- Revert PR.
- Re-run a single 50-ticket batch proof to confirm rollback restores previous schema.

### 9) Reviewer + tool focus
**Please double-check:**
- Order-status subset metrics and no-match reason mapping in `scripts/prod_shadow_order_status_report.py`.
- Aggregated B73 report values match batch evidence in `REHYDRATION_PACK/RUNS/B73/C/PROOF/`.
- PII-safe fields remain redacted/hashes only.

**Please ignore:**
- Batch proof artifacts except referenced B73 proof files.
- Line shifts in `prod_shadow_order_status_report.py` outside metrics/no-match logic.
