<!-- PR_QUALITY: title_score=95/100; body_score=95/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-09 -->

**Run ID:** `B74_B_20260209_1515Z`  
**Agents:** B  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `pending`  
**Anthropic response id:** `pending — not run`  

### 1) Summary
- Added a canonical AWS account/resource map and a Shopify secrets preflight.
- Hardened Shopify auth refresh handling (401/403 refresh + single retry).
- Captured DEV/PROD health check proof runs for Shopify tokens (3x each).

### 2) Why
- **Problem / risk:** Secrets Manager reads intermittently fail and Shopify tokens appear to expire, blocking deployments.
- **Pre-change failure mode:** No deterministic preflight for Shopify secrets; refresh failures were opaque.
- **Why this approach:** Preflight + deterministic health checks give fast, PII-safe validation and clear errors.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- No Shopify test orders or writes are created (read-only).
- No secret values or PII are logged.
- Refresh attempts happen once on 401/403 and then fail clearly.

**Non-goals (explicitly not changed):**
- No changes to Shopify store configuration.
- No changes to Richpanel prod write gates.

### 4) What changed
**Core changes:**
- Added `scripts/aws_secrets_preflight.py` to validate Shopify secret availability per env.
- Shopify client refresh path retries once on 401/403 and emits actionable errors.
- Run scripts support optional Shopify secrets preflight.

**Design decisions (why this way):**
- Keep secrets preflight PII-safe and deterministic.
- Fail fast on wrong-account/region to reduce Cursor/CI drift.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/integrations/shopify/client.py`

**Tests:**
- `scripts/test_shopify_client.py`
- `scripts/test_aws_secrets_preflight.py`

**CI / workflows:**
- `scripts/run_ci_checks.py`

**Docs / artifacts:**
- `docs/08_Engineering/AWS_ACCOUNT_RESOURCE_MAP.md`
- `REHYDRATION_PACK/RUNS/B74/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B74/B/EVIDENCE.md`

### 6) Test plan
**Local / CI-equivalent:**
- Not run (pending).

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/shopify_token_health_check.py --env dev --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --include-aws-account-id --out-json REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_dev_run1.json`
- `python scripts/shopify_token_health_check.py --env dev --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --include-aws-account-id --out-json REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_dev_run2.json`
- `python scripts/shopify_token_health_check.py --env dev --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --include-aws-account-id --out-json REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_dev_run3.json`
- `python scripts/shopify_token_health_check.py --env prod --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --include-aws-account-id --out-json REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_prod_run1.json`
- `python scripts/shopify_token_health_check.py --env prod --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --include-aws-account-id --out-json REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_prod_run2.json`
- `python scripts/shopify_token_health_check.py --env prod --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --include-aws-account-id --out-json REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_prod_run3.json`

### 7) Results & evidence
**CI:** pending  
**Codecov:** pending  
**Bugbot:** pending — trigger via `@cursor review`  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_dev.json`
- `REHYDRATION_PACK/RUNS/B74/B/PROOF/shopify_token_health_prod.json`
- `REHYDRATION_PACK/RUNS/B74/B/PROOF/secrets_preflight_dev.json`
- `REHYDRATION_PACK/RUNS/B74/B/PROOF/secrets_preflight_prod.json`

**Proof snippet(s) (PII-safe):**
```text
dev status=PASS health_check.status_code=200 aws_account_id=151124909266
prod status=PASS health_check.status_code=200 aws_account_id=878145708918
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — production auth behavior changes (refresh + error handling).

**Failure impact:** Shopify auth failures could block order lookups until rollback.

**Rollback plan:**
- Revert PR.
- Re-deploy prior Lambda versions.
- Re-run Shopify health checks to confirm rollback.

### 9) Reviewer + tool focus
**Please double-check:**
- Shopify auth refresh error handling and retry logic.
- Secrets preflight behavior and error messages.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
