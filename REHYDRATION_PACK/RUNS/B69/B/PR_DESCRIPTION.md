<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-04 -->

**Run ID:** `RUN_20260204_0012Z`  
**Agents:** B  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `claude-sonnet-4.5`  
**Anthropic response id:** `pending — https://github.com/KevinSGarrett/RichPanel/pull/220`

### 1) Summary
- Prevent Shopify refresh from overwriting stable admin API tokens unless a refresh token is present.
- Add health check status classification + `--json` output for CI automation.
- Default prod Shopify token sourcing in workflows to AWS Secrets Manager via OIDC.

### 2) Why
- **Problem / risk:** Shopify access tokens were reported as “expiring” and required manual rotation in GitHub/AWS.
- **Pre-change failure mode:** Scheduled refresh attempted client-credentials refresh, wrote rotating/invalid token to `admin_api_token`, and later `shop.json` calls returned `401`.
- **Why this approach:** Offline Admin API tokens are stable; rotation should only occur when a refresh token exists.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- No Shopify writes; read-only behavior preserved.
- No token values are logged or written to repo.
- Runtime Shopify token source remains AWS Secrets Manager.

**Non-goals (explicitly not changed):**
- No changes to Shopify scopes or app configuration.
- No changes to Richpanel/OpenAI runtime behavior.

### 4) What changed
**Core changes:**
- Skip refresh unless a refresh token exists; log refresh success/skip.
- Health check returns actionable statuses and compact JSON mode.
- Workflows resolve Shopify token from AWS Secrets Manager via OIDC by default.

**Design decisions (why this way):**
- Avoids overwriting stable `shpat_` tokens with short-lived tokens.
- Keeps a single source of truth in AWS while supporting CI.

### 5) Scope / files touched
**Runtime code:**
- `backend/src/integrations/shopify/client.py`
- `backend/src/lambda_handlers/shopify_token_refresh/handler.py`

**Tests:**
- `scripts/test_shopify_client.py`
- `scripts/test_shopify_health_check.py`

**CI / workflows:**
- `.github/workflows/order_status_prod_shadow.yml`
- `.github/workflows/shadow_live_readonly_eval.yml`

**Docs / artifacts:**
- `docs/08_Engineering/Secrets_and_Environments.md`
- `REHYDRATION_PACK/RUNS/B69/B/RUN_REPORT.md`
- `REHYDRATION_PACK/RUNS/B69/B/EVIDENCE.md`
- `REHYDRATION_PACK/RUNS/B69/B/CHANGES.md`

### 6) Test plan
**Local / CI-equivalent:**
- `python -m pytest scripts/test_shopify_health_check.py`
- `python -m pytest scripts/test_shopify_client.py -k "refresh_access_token_returns_false_without_refresh_token or refresh_access_token_client_credentials or refresh_error_includes_error_code"`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/shopify_health_check.py --env prod --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --out-json REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_prod.json --json --verbose`
- `python scripts/shopify_health_check.py --env prod --aws-region us-east-2 --shop-domain scentimen-t.myshopify.com --out-json REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_invalid.json --json --verbose`
- `python scripts/shopify_health_check.py --refresh-dry-run --json --out-json REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_dry_run.json --verbose`

### 7) Results & evidence
**CI:** pending — https://github.com/KevinSGarrett/RichPanel/pull/220/checks  
**Codecov:** pending — https://app.codecov.io/gh/KevinSGarrett/RichPanel/pull/220  
**Bugbot:** pending — https://github.com/KevinSGarrett/RichPanel/pull/220  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_prod.json`
- `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_invalid.json`
- `REHYDRATION_PACK/RUNS/B69/B/PROOF/shopify_health_check_dry_run.json`
- `REHYDRATION_PACK/RUNS/B69/B/EVIDENCE.md`

**Proof snippet(s) (PII-safe):**
```text
status=PASS health_check.status_code=200 token_type=offline
status=FAIL_INVALID_TOKEN health_check.status_code=401
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — touches token refresh logic and prod workflow secret sourcing.

**Failure impact:** Token refresh may be skipped when a refresh token is missing, which is intended for stable admin tokens.

**Rollback plan:**
- Revert PR.
- Re-run `scripts/shopify_health_check.py --refresh-dry-run ...` to confirm prior behavior.

### 9) Reviewer + tool focus
**Please double-check:**
- Refresh now requires a refresh token; stable admin tokens remain untouched.
- Workflows use OIDC to read `rp-mw/prod/shopify/admin_api_token` by default.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
