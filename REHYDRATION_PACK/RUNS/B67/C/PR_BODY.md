<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-03 -->

**Run ID:** `RUN_20260203_0404Z`  
**Agents:** C  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** pending — `<link>`  
**Anthropic response id:** pending — `<link>`  

### 1) Summary
- Prod shadow order-status report now separates global vs order-status metrics with explicit denominators.
- Three prod read-only shadow runs (250 tickets each) show stable order-status rate and healthy match rate.
- Nightly workflow added to repeat the prod shadow run and enforce metric bands.

### 2) Why
- **Problem / risk:** prior reports were misread because global counts were treated as match failures within order-status tickets.
- **Pre-change failure mode:** `no_match` was interpreted as broken Shopify matching without noting the global denominator.
- **Why this approach:** explicit global + conditional stats plus a scheduled run provides repeatable, PII-safe confidence signals.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- No writes to prod; read-only guard blocks non-GET operations.
- All artifacts remain PII-safe (hashed identifiers and redacted excerpts).
- Shadow reports fail closed if read-only flags are missing.

**Non-goals (explicitly not changed):**
- No changes to routing/classification logic or Shopify matching rules.
- No changes to customer-facing messaging/templates.

### 4) What changed
**Core changes:**
- Added global + order-status subset stats (and denominators) to the prod shadow report.
- Captured failure modes for both global and order-status subsets.
- Added nightly workflow to run prod shadow validation and enforce metric bands.

**Design decisions (why this way):**
- Keep shadow runs read-only with explicit env flags and no outbound.
- Metrics gating relies on report JSON fields to avoid manual interpretation.

### 5) Scope / files touched
**Runtime code:**
- `scripts/prod_shadow_order_status_report.py`

**Tests:**
- (None)

**CI / workflows:**
- `.github/workflows/order_status_prod_shadow.yml`

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run1.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run1.md`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run2.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run2.md`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run3.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run3.md`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/summary.md`
- `REHYDRATION_PACK/RUNS/B67/C/EVIDENCE.md`

### 6) Test plan
**Local / CI-equivalent:**
- (Not run) `python scripts/run_ci_checks.py --ci`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `AWS_PROFILE=rp-admin-kevin AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 MW_ALLOW_NETWORK_READS=true RICHPANEL_READ_ONLY=true RICHPANEL_WRITE_DISABLED=true RICHPANEL_OUTBOUND_ENABLED=false SHOPIFY_OUTBOUND_ENABLED=true SHOPIFY_WRITE_DISABLED=true SHOPIFY_SHOP_DOMAIN=scentimen-t.myshopify.com MW_OPENAI_ROUTING_ENABLED=true MW_OPENAI_INTENT_ENABLED=true MW_OPENAI_SHADOW_ENABLED=true RICHPANEL_ENV=prod MW_ENV=prod ENVIRONMENT=prod RICH_PANEL_ENV=prod RICHPANEL_RATE_LIMIT_RPS=2 python scripts/prod_shadow_order_status_report.py --allow-ticket-fetch-failures --retry-diagnostics --request-trace --batch-size 25 --batch-delay-seconds 0 --throttle-seconds 0 --env prod --richpanel-secret-id rp-mw/prod/richpanel/api_key --shopify-secret-id rp-mw/prod/shopify/admin_api_token --out-json REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run1.json --out-md REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run1.md --ticket-number <redacted...>`
- (Same command + `--out-json`/`--out-md` for run2 + run3; see `REHYDRATION_PACK/RUNS/B67/C/EVIDENCE.md`)

### 7) Results & evidence
**CI:** pending — `<link>`  
**Codecov:** pending — `<direct Codecov PR link>`  
**Bugbot:** pending — `<PR link>` (trigger via `@cursor review`)  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run1.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run2.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/prod_shadow_order_status_report_run3.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/summary.md`
- `REHYDRATION_PACK/RUNS/B67/C/EVIDENCE.md`

**Proof snippet(s) (PII-safe):**
```text
run1: order_status_rate=28.4%, match_rate_among_order_status=93.0%
run2: order_status_rate=30.4%, match_rate_among_order_status=93.4%
run3: order_status_rate=29.2%, match_rate_among_order_status=93.2%
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — prod read-only reporting + workflow change; no writes or outbound.

**Failure impact:** metrics could be misread if denominators drift or workflow thresholds are wrong.

**Rollback plan:**
- Revert PR
- Re-run prod shadow report with prior script to confirm baseline metrics

### 9) Reviewer + tool focus
**Please double-check:**
- Denominator explanation and conditional metrics in `prod_shadow_order_status_report.py`.
- Workflow threshold gates in `.github/workflows/order_status_prod_shadow.yml`.
- PII-safe artifacts in `REHYDRATION_PACK/RUNS/B67/C/PROOF`.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
- Log/JSON noise in proof artifacts.
