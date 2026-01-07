# Current State (Truth)

**As of:** 2026-01-07  
**Mode:** build (see `REHYDRATION_PACK/MODE.yaml`)  
**Stage:** dev + staging deployed; smoke tests green; prod gated  
**Estimated overall completion:** ~55% (conservative: prod go-live + Richpanel config + tier gating/verifier + real order-linkage remain)

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

### Core objective flow (order-status automation + routing)
Order-status automation is **advisory-first** and **fail-closed**:
1. Inbound message → ingress → queue
2. Worker normalizes the event + extracts minimal fields
3. **Deterministic** routing (keyword heuristics; no live LLM step in shipped v1)
4. Build a conservative plan (defaults to dry-run)
5. Persist idempotency (+ optional state/audit)
6. If explicitly enabled, execute allowlisted outbound actions (routing tags and/or deterministic order-status reply)

Source of truth for shipped vs roadmap pipeline: `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`.

### Shipped vs roadmap (explicit)
- **Shipped v1 (in `main`)**:
  - Deterministic keyword routing (no LLM classifier executed in the live worker)
  - Conservative plan builder + idempotency persistence
  - Offline-first / fail-closed gating (`safe_mode`, `automation_enabled`, outbound flags)
  - Order lookup scaffolding exists but is gated; outbound effects are blocked by default
- **Roadmap (designed, not fully wired into the worker)**:
  - LLM classifier (`mw_decision_v1`) + schema validation
  - Tier policy gating (Tier 0/1/2/3) enforced in application logic
  - Tier 2 verifier for order-status eligibility
  - Template-ID allowlist and Richpanel-template-based replies (vs free-form)

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
- Richpanel UI configuration runbook execution + evidence (teams/tags/rules/HTTP target) with staging-first rollout.
- Shopify / ShipStation: credentials + mapping + deterministic order linkage (Tier 2 prerequisite).
- Tier gating + verifier wiring (roadmap → shipped), while keeping LLM advisory and fail-closed.

---

## Notes
- This file is a snapshot. Evidence and GitHub ops details live in:
  - `REHYDRATION_PACK/GITHUB_STATE.md`
  - `docs/08_Testing_Quality/Test_Evidence_Log.md`
