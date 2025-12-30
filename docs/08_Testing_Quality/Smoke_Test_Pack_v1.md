# Smoke Test Pack (v1)

Last updated: 2025-12-29  
Scope: Wave 09 (Testing/QA/Release readiness) — **Closeout pack**

This smoke test pack is the **minimum high-signal** set of tests to run before:
- enabling any production automation, and
- after any change to prompts, schemas, templates, routing rules, or vendor integrations.

It is designed to validate the system end-to-end at the level that matters most:
- correct **routing**
- correct **tier gating** (Tier 0 never automated; Tier 2 requires deterministic match)
- no **duplicate replies** (idempotency)
- kill switch works (**safe_mode** / **automation_enabled**)
- no obvious **PII leaks** in logs or replies

---

## How to use this pack

### Inputs
- The authoritative test case list is in:
  - `smoke_tests/smoke_test_cases_v1.csv`

Each test case specifies:
- channel (livechat / email / other)
- an example inbound customer message
- expected primary intent (and sometimes a secondary intent)
- expected destination team + tags
- expected template_id (or `None`)
- expected policy outcome (route-only vs auto-reply)

### Execution modes
Choose one:

1) **Staging (recommended)**
- create test tickets in Richpanel (or send synthetic webhooks)
- verify tags/routing + replies

2) **Prod-safe verification (route-only)**
- run with `safe_mode=true` and `automation_enabled=false`
- validate routing only (no replies)

### Preconditions
- Observability dashboards are available (Wave 08).
- Kill switch is available (Wave 06):
  - `safe_mode=true` forces route-only
  - `automation_enabled=false` blocks all auto-replies
- Idempotency and dedup controls are enabled (Wave 02/03).

---

## Required test subsets (minimum)

### A) Routing baseline (must pass)
Run all cases with `expected_action = route_only` in the CSV.
- Validates intent taxonomy mapping → team routing
- Validates low-confidence fallback

### B) Tier 0 escalation safety (must pass)
Run all cases with Tier 0 intents:
- `chargeback_dispute`
- `legal_threat`
- `fraud_suspected`
- `harassment_threats`

**Pass condition:** No auto-reply (unless you explicitly enabled a neutral acknowledgement template; v1 default is route-only).

### C) Tier 1 safe-assist automation (only if automation enabled)
Run Tier 1 cases only after:
- `automation_enabled=true`
- `safe_mode=false`

**Pass condition:** Replies are intake/info only (no order-specific disclosure).

### D) Tier 2 verified order status (only if deterministic match is available)
Run Tier 2 cases only after:
- Richpanel order linkage is verified for your tenant (or Shopify fallback exists)
- deterministic match gate is enforced

**Pass condition:**  
- If **no** deterministic match -> `t_order_status_ask_order_number` (Tier 1)  
- If **yes** deterministic match + tracking exists -> `t_order_status_verified` (Tier 2)  
- If **yes** deterministic match + no tracking yet (within SLA window) -> `t_order_eta_no_tracking_verified` (Tier 2, auto-close eligible)  
- If **yes** deterministic match + no tracking and outside SLA window -> `t_shipping_delay_verified` + route to human  
- Never disclose order details without deterministic match.

### E) Idempotency / duplicates (must pass)
Run duplicate-delivery cases.
**Pass condition:** no duplicate replies and no repeated side-effects.

### F) Kill switch / safe mode (must pass)
Validate:
- flipping `automation_enabled=false` stops replies immediately
- flipping `safe_mode=true` forces route-only immediately

---

## Evidence to capture (for Go/No-Go)
For each subset above, capture:
- a screenshot or log excerpt showing tags/assignment outcome
- any auto-reply content (if enabled)
- the correlation ID (request_id / ticket_id) in logs
- confirmation that logs are PII-safe (no raw message bodies stored)

---

## Related documents
- `docs/05_FAQ_Automation/Top_FAQs_Playbooks.md`
- `docs/04_LLM_Design_Evaluation/Template_ID_Catalog.md`
- `docs/04_LLM_Design_Evaluation/Multi_Intent_Priority_Matrix.md`
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- `docs/09_Deployment_Operations/First_Production_Deploy_Runbook.md`
- `docs/09_Deployment_Operations/Go_No_Go_Checklist.md`
