# Production Cutover Runbook — Order Status

Last updated: 2026-02-02  
Status: Canonical

## Goal

Safely transition Order Status from **sandbox proof** to **production canary**, with a clear enablement and rollback path, minimal blast radius, and PII-safe evidence.

---

## Prereqs (must be true before Phase 0)

- **Secrets present (AWS Secrets Manager):**
  - `rp-mw/prod/richpanel/api_key`
  - `rp-mw/prod/shopify/admin_api_token`
  - `rp-mw/prod/shopify/client_id`
  - `rp-mw/prod/shopify/client_secret`
  - `rp-mw/prod/openai/api_key`
- **Bot agent id configured:** `RICHPANEL_BOT_AGENT_ID` / `RICHPANEL_BOT_AUTHOR_ID` set for prod worker.
- **Shopify token refresh Lambda deployed** and scheduled every 4 hours.
- **Runtime kill switches available in SSM:**
  - `/rp-mw/prod/safe_mode`
  - `/rp-mw/prod/automation_enabled`
- **Preflight passes** using the production preflight script.
- **PII-safe evidence location** identified (no raw ticket bodies or emails).

---

## Phase 0 — Prod Read-Only Shadow Validation

**Goal:** Validate real production traffic with **no writes or outbound**.

### Enable read-only shadow mode

- SSM flags (safe mode ON):
  - `safe_mode=true`
  - `automation_enabled=false`
- Lambda env vars:
  - `MW_ALLOW_NETWORK_READS=true`
  - `RICHPANEL_READ_ONLY=true`
  - `RICHPANEL_WRITE_DISABLED=true`
  - `RICHPANEL_OUTBOUND_ENABLED=false`
  - `SHOPIFY_OUTBOUND_ENABLED=true`
  - `SHOPIFY_WRITE_DISABLED=true`

### Run shadow report

Use the prod shadow report for Order Status:

```powershell
python scripts/prod_shadow_order_status_report.py `
  --env prod `
  --sample-size 250 `
  --batch-size 10 `
  --batch-delay-seconds 2 `
  --retry-diagnostics `
  --request-trace
```

### Green criteria

All of the following must be true:

- **No writes** in CloudWatch logs (no POST/PUT/PATCH/DELETE to Richpanel/Shopify).
- **Shadow report exits cleanly** (non-zero exit is a block).
- **Match success rate** is within acceptable baseline (compare to most recent successful run).
- **No drift alerts** in `drift_watch.alerts`.
- **429s not spiking** (no sustained rate-limit warnings).

If any criteria fail, **do not proceed**. Fix and rerun Phase 0.

---

## Phase 1 — Canary Enable (restricted blast radius)

**Goal:** Enable outbound for a small controlled cohort (allowlisted).

### Enable automation + outbound, keep allowlist

1) **SSM flags:**
   - `safe_mode=false`
   - `automation_enabled=true`

2) **Worker env vars (prod):**
   - `RICHPANEL_OUTBOUND_ENABLED=true`
   - `RICHPANEL_WRITE_DISABLED=false`
   - `MW_OUTBOUND_ENABLED=true`
   - `MW_PROD_WRITES_ACK=I_UNDERSTAND_PROD_WRITES`

3) **Allowlist (canary scope):**
   - `MW_OUTBOUND_ALLOWLIST_EMAILS=<small list>`
   - `MW_OUTBOUND_ALLOWLIST_DOMAINS=<optional>`

### Canary verification (first 30–60 min)

- Richpanel UI: confirm **only allowlisted** tickets receive replies/tags.
- CloudWatch: confirm **no error spikes**, **no 429 spikes**, **OpenAI failures = 0**.
- Keep log evidence PII-safe.

If issues occur, **rollback immediately**.

---

## Phase 2 — Scale Up

**Goal:** Expand traffic safely once canary is stable.

1) Increase allowlist size (or remove allowlist once stable).
2) Continue monitoring alarms and CloudWatch logs.
3) Record change in `PM_REHYDRATION_PACK/03_PROGRESS_LOG.md`.

---

## Rollback (fast and explicit)

**Immediate rollback steps:**

- Set `RICHPANEL_OUTBOUND_ENABLED=false`
- Set `MW_OUTBOUND_ENABLED=false`
- Set `RICHPANEL_WRITE_DISABLED=true`
- Set `safe_mode=true`, `automation_enabled=false` in SSM
- Disable OpenAI intent if needed:
  - `MW_OPENAI_INTENT_ENABLED=false`

**Fallback:** Route tickets to manual support only (no automation).

---

## Verification Checklist (prod enablement)

- [ ] Preflight script passes with **PASS**.
- [ ] Shadow report meets green criteria.
- [ ] Alarms created (worker errors, 429s, OpenAI failures, refresh errors).
- [ ] Canary allowlist in place.
- [ ] CloudWatch logs show no unexpected writes.
- [ ] Richpanel UI confirms correct behavior.

---

## Where to check

- **Richpanel UI:** ticket history + tags + comments for allowlisted conversations.
- **CloudWatch Logs:** `/aws/lambda/rp-mw-prod-worker`
- **CloudWatch Alarms/Dashboard:** `rp-mw-prod-order-status`

---

## Related docs

- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- `docs/09_Deployment/Order_Status_Preflight.md`
- `docs/09_Deployment/Order_Status_Monitoring.md`
