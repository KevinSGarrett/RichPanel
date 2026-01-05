# Current State (Truth)

**As of:** 2026-01-05  
**Mode:** build (see `REHYDRATION_PACK/MODE.yaml`)  
**Stage:** dev + staging deployed; smoke tests green; prod gated  
**Estimated overall completion:** ~65%

---

## What exists now (shipped in `main`)

### Deployments + smoke tests (dev/staging)
- Dev deploy: ✅ green  
  - Evidence: `https://github.com/KevinSGarrett/RichPanel/actions/runs/20671603896`
- Dev E2E smoke: ✅ green  
  - Evidence: `https://github.com/KevinSGarrett/RichPanel/actions/runs/20671633587`
- Staging deploy: ✅ green  
  - Evidence: `https://github.com/KevinSGarrett/RichPanel/actions/runs/20673604749`
- Staging E2E smoke: ✅ green  
  - Evidence: `https://github.com/KevinSGarrett/RichPanel/actions/runs/20673641283`

### Runtime pipeline exists (end-to-end)
- Runtime path: **API → ingress → SQS → worker → DynamoDB**
- Ingress enqueues events to SQS; worker processes, plans, and persists **idempotency** records.  
  - Worker code supports optional **conversation state + audit trail** persistence when tables are configured.
- Automation candidates now include an order lookup (Shopify + ShipStation behind dry-run gates) and plan an `order_status_draft_reply` action with prompt fingerprints; outbound remains blocked by default.

### Safety gates are in place (conservative defaults)
- Kill switches: `safe_mode` + `automation_enabled`
- Execution defaults to **dry-run** (no side effects unless explicitly enabled)

### Docs anti-drift gate exists
- CI runs `python scripts/verify_admin_logs_sync.py` to prevent “admin docs vs reality” drift.

### GitHub + CI baseline is stable
- Repo is hosted on GitHub (`KevinSGarrett/RichPanel`).
- `main` is protected with required status check **`validate`**.
- Merge policy is constrained (merge-commit only; delete branch on merge).
- Bugbot review is part of the PR loop (trigger via `@cursor review`; see `docs/08_Engineering/CI_and_Actions_Runbook.md`).

---

## Prod status (gated)
- Prod workflows exist (`Deploy Prod Stack`, `Prod E2E Smoke`) but are **not yet green in recent runs**.
- Promotion to prod is **explicitly human-gated** (go/no-go + evidence capture).

---

## What’s next (highest leverage)
- Shopify / ShipStation integration work (data + credentials + mapping).
- Richpanel UI configuration + operational controls (confirm how/where operators configure and toggle behavior).

---

## Notes
- This file is a snapshot. Evidence and GitHub ops details live in:
  - `REHYDRATION_PACK/GITHUB_STATE.md`
  - `docs/08_Testing_Quality/Test_Evidence_Log.md`
