<!-- PR_QUALITY: title_score=98/100; body_score=98/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-02 -->

**Run ID:** `RUN_20260202_1052Z`  
**Agents:** C  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  

### 1) Summary
- Run scaled prod read-only shadow validation for order-status (250 tickets) with OpenAI classification enabled.
- Capture preflight health check output (Richpanel + Shopify auth OK) and PII-safe report artifacts.
- Add safe-run instructions for the prod shadow order-status report to the runbook.
- Update preflight Richpanel probe to use `/v1/users` (matches tenant permissioned endpoint).

### 2) Why
- **Problem / risk:** Need production validation of order-status routing + Shopify lookup without any writes.
- **Goal:** Quantify order-status share, match breakdown, tracking/ETA availability, and failure reasons with PII-safe proof.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Prod shadow run is read-only: no tags, closes, or outbound messages.
- All artifacts are PII-safe (hashed identifiers, sanitized excerpts).
- OpenAI is used only with explicit shadow flags enabled.

**Non-goals:**
- No production writes or customer contact.
- No schema changes outside the report + docs.

### 4) What changed
**Core changes:**
- Preflight Richpanel health check uses `/v1/users` to validate auth (matches tenant access).
- Added runbook section for safe execution of prod shadow order-status report.

**Artifacts:**
- `REHYDRATION_PACK/RUNS/B66/C/PROOF/preflight.md`
- `REHYDRATION_PACK/RUNS/B66/C/PROOF/prod_shadow_order_status_report.json`
- `REHYDRATION_PACK/RUNS/B66/C/PROOF/prod_shadow_order_status_report.md`

### 5) Scope / files touched
**Runtime code:**
- `scripts/order_status_preflight_check.py`

**Docs / artifacts:**
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- `REHYDRATION_PACK/RUNS/B66/C/PROOF/preflight.md`
- `REHYDRATION_PACK/RUNS/B66/C/PROOF/prod_shadow_order_status_report.json`
- `REHYDRATION_PACK/RUNS/B66/C/PROOF/prod_shadow_order_status_report.md`

### 6) Test plan
**E2E / proof runs (PII-safe):**
- `AWS_PROFILE=rp-admin-kevin AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 MW_ALLOW_NETWORK_READS=true RICHPANEL_READ_ONLY=true RICHPANEL_WRITE_DISABLED=true RICHPANEL_OUTBOUND_ENABLED=false SHOPIFY_OUTBOUND_ENABLED=true SHOPIFY_WRITE_DISABLED=true SHOPIFY_SHOP_DOMAIN=scentimen-t.myshopify.com MW_OPENAI_ROUTING_ENABLED=true MW_OPENAI_INTENT_ENABLED=true MW_OPENAI_SHADOW_ENABLED=true RICHPANEL_ENV=prod MW_ENV=prod ENVIRONMENT=prod RICH_PANEL_ENV=prod RICHPANEL_RATE_LIMIT_RPS=2 python scripts/prod_shadow_order_status_report.py --allow-ticket-fetch-failures --retry-diagnostics --request-trace --batch-size 25 --batch-delay-seconds 1 --throttle-seconds 0.3 --env prod --out-json REHYDRATION_PACK/RUNS/B66/C/PROOF/prod_shadow_order_status_report.json --out-md REHYDRATION_PACK/RUNS/B66/C/PROOF/prod_shadow_order_status_report.md --ticket-number <redacted...>`
- `AWS_PROFILE=rp-admin-kevin AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 RICHPANEL_ENV=prod ENVIRONMENT=prod MW_ALLOW_NETWORK_READS=true RICHPANEL_READ_ONLY=true RICHPANEL_WRITE_DISABLED=true RICHPANEL_OUTBOUND_ENABLED=false SHOPIFY_OUTBOUND_ENABLED=true SHOPIFY_WRITE_DISABLED=true SHOPIFY_SHOP_DOMAIN=scentimen-t.myshopify.com python scripts/order_status_preflight_check.py --env prod --out-md REHYDRATION_PACK/RUNS/B66/C/PROOF/preflight.md`

### 7) Results & evidence
**Preflight:** PASS — `REHYDRATION_PACK/RUNS/B66/C/PROOF/preflight.md`  
**Shadow report:** 250 tickets — `REHYDRATION_PACK/RUNS/B66/C/PROOF/prod_shadow_order_status_report.json` / `.md`

**Proof snippet(s) (PII-safe):**
```text
order_status_rate=32.0%; order_status_tickets=80
match_breakdown: order_number=58 (72.5%), email=17 (21.2%), no_match=5 (6.2%)
tracking_rate_matched=94.7%; eta_rate_matched=4.0%
shopify_errors=0; retry_after_violations=0
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — read-only validation + doc update + preflight probe path.  
**Rollback plan:** Revert this PR; rerun preflight and shadow report to confirm baseline behavior.

### 9) Reviewer + tool focus
**Please double-check:**
- Preflight Richpanel probe path + pass status.
- PII-safe artifacts and report metrics (match breakdown, tracking/ETA, error buckets).
- Runbook instructions for safe execution.
