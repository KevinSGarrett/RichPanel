<!-- PR_QUALITY: title_score=96/100; body_score=97/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-02-02 -->

**Run ID:** `RUN_20260202_1522Z`  
**Agents:** B  
**Labels:** `risk:R2`, `gate:claude`  
**Risk:** `risk:R2`  
**Claude gate model (used):** `pending — gate not run`  
**Anthropic response id:** `pending — gate not run`

### 1) Summary
- Production cutover runbook now defines prerequisites, phased enablement, and rollback for Order Status.
- Minimum monitoring (alarms + dashboard) is deployed for 429s, worker error rate, OpenAI failures, and token refresh errors.
- Preflight now validates env flags, Secrets Manager, Richpanel GET, Shopify REST + GraphQL, and refresh success within 8h.

### 2) Why
- **Problem / risk:** prod canary enablement lacked a single cutover runbook, minimal alarms, and a robust preflight.
- **Pre-change failure mode:** no single-step enable/rollback guide; missing alarms for 429s/refresh/OpenAI; preflight did not check GraphQL or refresh freshness.
- **Why this approach:** targeted infra + docs + script updates minimize refactor risk while adding operational safety gates.

### 3) Expected behavior & invariants
**Must hold (invariants):**
- Preflight fails closed if required env flags or secrets are missing.
- PII-safe evidence only (no ticket bodies or emails in artifacts).
- Read-only guard remains enforced for shadow validation runs.

**Non-goals (explicitly not changed):**
- No changes to routing logic or order-status classification thresholds.
- No change to customer-facing messaging content or templates.

### 4) What changed
**Core changes:**
- Added production cutover runbook with Phase 0–2 + rollback steps.
- Added CloudWatch alarms + dashboard with explicit alarm names for retrieval.
- Expanded preflight to include Secrets Manager, Shopify GraphQL, and refresh “last success”.
- Regenerated docs registry outputs after adding new docs (required by validate check).
- Made docs registry regen use tracked docs only to avoid untracked drift in CI.

**Design decisions (why this way):**
- Metric filters rely on explicit log markers for 429s and OpenAI intent failures.
- Preflight uses log stream inspection to avoid filter-pattern edge cases.

**How to use this:**
- Run preflight: `python scripts/preflight_order_status_prod.py --env prod --out-md REHYDRATION_PACK/RUNS/B67/C/PROOF/preflight.md`
- Find alarms: CloudWatch → Alarms → `rp-mw-prod-*` (see `rp-mw-prod-*-` alarm names in monitoring doc)

### 5) Scope / files touched
**Runtime code:**
- `backend/src/richpanel_middleware/integrations/richpanel/client.py`
- `backend/src/integrations/shopify/client.py`
- `infra/cdk/lib/richpanel-middleware-stack.ts`
- `scripts/order_status_preflight_check.py`
- `scripts/preflight_order_status_prod.py`

**Tests:**
- `scripts/test_order_status_preflight_check.py`

**CI / workflows:**
- (None)

**Docs / artifacts:**
- `PM_REHYDRATION_PACK/DEADLINE_SCHEDULE/08_PRODUCTION_CUTOVER_PLAN.md`
- `docs/09_Deployment/Order_Status_Preflight.md`
- `docs/09_Deployment/Order_Status_Monitoring.md`
- `docs/REGISTRY.md`
- `docs/_generated/doc_outline.json`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_registry.json`
- `docs/_generated/heading_index.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/preflight.md`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/cloudwatch_alarms.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/cloudwatch_dashboards.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/cloudformation_stack_status.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/shopify_token_refresh_log.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/shopify_token_refresh_invoke.json`

### 6) Test plan
**Local / CI-equivalent:**
- `AWS_PROFILE=rp-admin-prod AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 ENVIRONMENT=prod RICHPANEL_ENV=prod MW_ENV=prod MW_ALLOW_NETWORK_READS=true RICHPANEL_READ_ONLY=true RICHPANEL_WRITE_DISABLED=true RICHPANEL_OUTBOUND_ENABLED=false SHOPIFY_OUTBOUND_ENABLED=true SHOPIFY_WRITE_DISABLED=true SHOPIFY_SHOP_DOMAIN=scentimen-t.myshopify.com python scripts/preflight_order_status_prod.py --env prod --out-md REHYDRATION_PACK/RUNS/B67/C/PROOF/preflight.md`
- `npx cdk deploy RichpanelMiddleware-prod --require-approval never --profile rp-admin-prod`

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- (None)

### 7) Results & evidence
**CI:** pending — PR not created yet  
**Codecov:** pending — PR not created yet  
**Bugbot:** pending — PR not created yet (trigger via `@cursor review`)  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/preflight.md`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/cloudwatch_alarms.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/cloudwatch_dashboards.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/cloudformation_stack_status.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/shopify_token_refresh_log.json`
- `REHYDRATION_PACK/RUNS/B67/C/PROOF/shopify_token_refresh_invoke.json`

**Proof snippet(s) (PII-safe):**
```text
overall_status PASS
shopify_token_refresh_last_success PASS last_success_age_hours=0.07
```

### 8) Risk & rollback
**Risk rationale:** `risk:R2` — infra + docs + scripts change prod monitoring/preflight paths.  

**Failure impact:** missing alarms or preflight false negatives could allow unsafe canary.  

**Rollback plan:**
- Revert PR
- `npx cdk deploy RichpanelMiddleware-prod --require-approval never --profile rp-admin-prod`
- Re-run preflight to confirm PASS and alarms still present

### 9) Reviewer + tool focus
**Please double-check:**
- Alarm thresholds + names match monitoring doc.
- Preflight refresh-success detection logic is robust.

**Please ignore:**
- Rehydration pack artifacts except referenced proof files.
- Generated registries unless CI flags an issue.
- Line-number shifts outside touched files.
