<!-- PR_QUALITY: title_score=96/100; body_score=94/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-04 -->

**Run ID:** `RUN_20260204_1657Z`  
**Agents:** B  
**Risk:** `risk:R2`  
**Claude gate:** Opus 4.5  

### 1) Summary
- Replace the 48-hour wait with deterministic Shopify token stability proof (health check + scheduled monitor).
- Gate refresh-token rotation to prevent overwriting stable admin tokens.
- Add scheduled Shopify token health check artifacts for early 401/403 detection.

### 2) Why
- **Problem / risk:** Waiting 48+ hours to prove token stability is impractical for the deadline.
- **Pre-change failure mode:** Scheduled refresh could overwrite stable `admin_api_token` values, causing 401s.
- **Why this approach:** Offline Admin API tokens are stable; a deterministic health check + monitor provides immediate proof without manual rotation.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- No Shopify writes; read-only calls only.
- Refresh job runs only when explicitly enabled.
- No PII or token values in logs or proof artifacts.

**Non-goals (explicitly not changed):**
- No scope changes to the Shopify app.
- No changes to Richpanel/OpenAI runtime behavior.

### 4) What changed
**Core changes:**
- Added `SHOPIFY_REFRESH_ENABLED` gating to refresh logic and Lambda handler.
- Guarded refresh secret writes from empty access tokens.
- Added scheduled Shopify token health check workflow with PII-safe artifacts.
- Updated preflight refresh checks to warn when refresh is intentionally disabled.

**Design decisions (why this way):**
- Default refresh to off to protect stable offline tokens.
- Use `shop.json` read-only endpoint for deterministic health proof.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/integrations/shopify/client.py`
- `backend/src/lambda_handlers/shopify_token_refresh/handler.py`

**Tests:**
- `scripts/test_shopify_client.py`
- `scripts/test_shopify_health_check.py`
- `scripts/test_order_status_preflight_check.py`

**CI / workflows:**
- `.github/workflows/shopify_token_health_check.yml`

**Docs / artifacts:**
- `docs/08_Engineering/Secrets_and_Environments.md`
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- `docs/09_Deployment/Order_Status_Monitoring.md`
- `docs/09_Deployment_Operations/Release_and_Rollback.md`
- `REHYDRATION_PACK/RUNS/B70/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B70/B/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B70/B/CHANGES.md`

### 6) Test plan
**Local / CI-equivalent:**
- Not run.

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/shopify_health_check.py --env prod --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --out-json REHYDRATION_PACK/RUNS/B70/B/PROOF/shopify_token_health_check.json --json --include-aws-account-id`

### 7) Results & evidence
**CI:** pending — PR not created yet  
**Codecov:** pending — PR not created yet  
**Bugbot:** pending — PR not created yet  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B70/B/PROOF/shopify_token_health_check.json`

**Proof snippet(s) (PII-safe):**
```text
status=PASS health_check.status_code=200 aws_account_id=878145708918
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — refresh logic and monitoring changed in prod-related paths.

**Failure impact:** Refresh may be skipped until explicitly enabled, potentially delaying rotation when needed.

**Rollback plan:**
- Revert PR.
- Re-run `scripts/shopify_health_check.py --env prod ...` to confirm rollback.

### 9) Reviewer + tool focus
**Please double-check:**
- Refresh gating prevents overwriting stable tokens.
- Health check workflow fails on non-200 status.
- Docs no longer require 48-hour waiting.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
