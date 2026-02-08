<!-- PR_QUALITY: title_score=92/100; body_score=90/100; rubric_title=07; rubric_body=03; risk=risk:R1; p0_ok=true; timestamp=2026-02-08 -->

**Run ID:** `RUN_20260208_1726Z`  
**Agents:** B  
**Risk:** `risk:R1`  
**Claude gate:** N/A  

### 1) Summary
- Added a Shopify token health-check wrapper that prints the active AWS account to prevent wrong-account confusion.
- Added runtime logging to make Shopify refresh attempt decisions operator-visible without exposing tokens.
- Updated order-status runbook commands for the token health check.

### 2) Why
- **Problem / risk:** Token health checks can silently run against the wrong AWS account or fail to refresh with unclear diagnostics.
- **Pre-change failure mode:** No up-front account banner for token health checks; refresh failures were not clearly surfaced at runtime.
- **Why this approach:** Lightweight guardrail + structured logs improve operator clarity without changing token semantics.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- No Richpanel PROD writes; Shopify access stays read-only.
- No tokens or secret values are logged.
- Refresh attempts occur only when refresh metadata exists and flags allow it.

**Non-goals (explicitly not changed):**
- No changes to Shopify auth flows or token formats.
- No new refresh token creation behavior.

### 4) What changed
**Core changes:**
- Added `scripts/shopify_token_health_check.py` wrapper to print `Account=<id>` then delegate to the existing health check.
- Added a structured refresh-attempt log and actionable failure log in `backend/src/integrations/shopify/client.py`.
- Updated `REHYDRATION_PACK/SHOPIFY_STRATEGY/SHADOW_MODE_RUNBOOK.md` health check commands.

**Design decisions (why this way):**
- Wrapper keeps the existing health-check logic unchanged while adding account guardrails.
- Logging is single-line structured output to keep observability minimal and safe.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/integrations/shopify/client.py`

**Tests:**
- None (proof runs only)

**CI / workflows:**
- None

**Docs / artifacts:**
- `REHYDRATION_PACK/SHOPIFY_STRATEGY/SHADOW_MODE_RUNBOOK.md`
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/aws_sts_dev.txt`
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/aws_sts_prod.txt`
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/shopify_token_health_dev.txt`
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/shopify_token_health_prod.txt`
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/shopify_shop_domain_dev.txt`
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/shopify_shop_domain_prod.txt`

### 6) Test plan
**Local / CI-equivalent:**
- `python -m pytest scripts/test_shopify_token_health_check.py`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `aws sts get-caller-identity --profile rp-admin-dev`
- `aws sts get-caller-identity --profile rp-admin-prod`
- `python scripts/shopify_token_health_check.py --env dev --aws-region us-east-2 --include-aws-account-id --shop-domain scentimen-t.myshopify.com`
- `python scripts/shopify_token_health_check.py --env prod --aws-region us-east-2 --include-aws-account-id --refresh --shop-domain scentimen-t.myshopify.com`

### 7) Results & evidence
**CI:** pending — not run  
**Codecov:** pending — not run  
**Bugbot:** pending — not run  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/aws_sts_dev.txt`
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/aws_sts_prod.txt`
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/shopify_token_health_dev.txt`
- `REHYDRATION_PACK/RUNS/B73/B/PROOF/shopify_token_health_prod.txt`

**Proof snippet(s) (PII-safe):**
```text
Account=151124909266
"status": "PASS"
"refresh_enabled": false
```
```text
Account=878145708918
"status": "PASS"
"refresh_enabled": true
"refresh_error": "non_admin_token_source"
```

### 8) Risk & rollback
**Risk rationale:** `risk:R1` — logging/guardrail changes only; no behavior or secret formats changed.

**Failure impact:** Reduced observability or incorrect operator assumptions about refresh attempts.

**Rollback plan:**
- Revert PR
- Re-run `scripts/shopify_token_health_check.py` for dev/prod to confirm baseline behavior

### 9) Reviewer + tool focus
**Please double-check:**
- Refresh attempt logging is structured and does not leak token data.
- Health check guardrail prints correct AWS account at start.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
