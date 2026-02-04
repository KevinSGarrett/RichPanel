# Release and Rollback Plan

Last updated: 2025-12-22  
Scope: Wave 09 (Testing/QA/Release readiness).

This plan ensures production deployment is safe, observable, and reversible.

---

## Core release principles
- Release **routing first**, then automation.
- Use **progressive enablement** (feature flags and template whitelists).
- Prefer “configuration rollback” over “code rollback” when possible.
- Observe metrics before broadening exposure.

---

## Release stages (recommended)

### Stage 0 — Preconditions
Before any prod deploy:
- CI merge gates pass
- LLM regression gates pass for prompt/template changes
- staging smoke tests pass
- alarms/dashboards exist (Wave 06 + Wave 08)

### Stage 1 — Deploy to prod (safe baseline)
Deploy the new version with:
- `safe_mode=true` (route-only)
- `automation_enabled=false`

Validate for 2–4 hours, plus scheduled health checks:
- routing latency + backlog
- error rates
- vendor rate-limit behavior
- mapping drift events

### Stage 2 — Enable automation (limited, low-risk)
Enable:
- `automation_enabled=true`
Keep:
- `safe_mode=false` only if you intend to send replies

Start with a **template whitelist**:
- Tier 1 “ask for order #”
- delivered-but-not-received safe-assist
- (optional) basic troubleshooting safe-assist

Do not enable Tier 2 order-status disclosure yet unless deterministic matching is verified in production.

### Stage 3 — Enable Tier 2 verified order status
Enable Tier 2 only when:
- deterministic match rate is acceptable
- Tier 2 verifier shows low false positives
- no PII leak incidents in prior stage

Start with:
- a subset of tickets (tag-based allowlist) or
- a subset of channels (LiveChat first)

### Stage 4 — Gradual expansion
Expand templates and coverage only after:
- weekly eval results stable
- support ops agrees automation is helping

---

## Rollback options (fast → slow)

### Option A — Kill switch (fastest)
- set `automation_enabled=false`
- set `safe_mode=true`

This stops customer-facing automation immediately while preserving routing.

### Option B — Template kill (surgical)
- disable a single template_id or intent mapping
- keep rest of automation enabled

### Option C — Deploy previous version
- revert to previous code/IaC version
- use this only if Options A/B are insufficient

---

## Rollback triggers (go/no-go)
Immediate rollback (Option A) if any of these occur:
- automation loop detected (repeated replies)
- Tier 0 intent is auto-responded to
- any suspected private data disclosure
- sudden spike in customer complaints related to wrong automation

Rollback evaluation triggers:
- routing error spike (measured by feedback tags)
- vendor 429 storm causing large backlog
- cost spike beyond expected range

---

## Release checklist and approval
Use:
- `docs/09_Deployment_Operations/Go_No_Go_Checklist.md`
- `docs/08_Testing_Quality/Manual_QA_Checklists.md`

---

## Post-release monitoring (first 24 hours)
Monitor:
- queue depth / oldest message age
- automation send count
- policy_override rate
- Tier 0 escalation volume
- customer reply dissatisfaction signals (if available)

See:
- `docs/08_Observability_Analytics/Dashboards_Alerts_and_Reports.md`
- `docs/08_Observability_Analytics/Operator_Quick_Start_Runbook.md`
