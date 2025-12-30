# R007 — Order status automation failure

Last updated: 2025-12-22  
Default severity: **SEV-2 (SEV-1 if widespread and customer-impacting)**

---

## When to use this runbook
Use when:
- order status auto-replies stop sending despite eligible messages
- deterministic match frequently fails unexpectedly
- tracking links/numbers missing even for linked orders
- customers complain about incorrect order status (escalate to R003 if PII risk)


---

## Immediate actions (stop the bleeding)
1) If correctness is uncertain:
- disable the order-status template(s) or disable automation entirely
- keep routing active

2) If eligibility dropped:
- temporarily downgrade order status flow to Tier 1 ask-for-order# only


---

## Diagnosis steps
A) Identify where it fails
- order linkage missing? (Richpanel order lookup returns empty)
- order details missing tracking fields?
- Shopify fallback not configured?
- template rendering missing variables?

B) Check vendor errors
- Richpanel / Shopify 429/5xx during order lookup

C) Confirm deterministic-match logic
- email/phone/order# matching rules
- conversation-to-order linkage requirements


---

## Mitigation / repair actions
- Add caching of linked order IDs (short TTL) to reduce repeated lookups
- Fix missing variable rendering issues
- If tracking fields missing in Richpanel payload:
  - use Shopify fallback (if available) OR keep Tier 1 approach


---

## Verify recovery
- eligible order-status tickets receive correct reply again
- no Tier 2 violations occur (must remain 0)


---

## Post-incident follow-ups
- Add monitoring: “order status automation success rate”
- Add regression tests for order lookup rendering


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard A — System Health (Wave 08)
- Dashboard B — Vendor Health (Wave 08)

### Metrics to check
- `mw.vendor.richpanel.errors_total`
- `mw.vendor.shopify.errors_total`
- `mw.policy.automation_attempt_total`
- `mw.policy.automation_blocked_total`
- `mw.worker.end_to_end_latency_ms`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, ticket_id, mw_trace_id,
       decision.primary_intent, decision.tier, decision.template_id, decision.action,
       vendor.name, vendor.operation, vendor.http_status, vendor.error_code
| filter decision.primary_intent = "order_status_tracking"
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- Disable only order-status template(s): `template_enabled.t_order_status_tracking_verified=false`.
- Fallback to Tier 1 intake template (ask for order #) if order lookup is failing.
- If widespread: `automation_enabled=false` until vendor/lookup is stable.

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- ST-002 (route-only order status)
- ST-040 (tier2 no match falls back to tier1)
- ST-041 (tier2 match includes tracking)


## Related docs
- [Order status automation spec](../../05_FAQ_Automation/Order_Status_Automation.md)
- [Richpanel API contracts](../../03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md)
- [Vendor rate limit storm](R004_Vendor_Rate_Limit_Storm.md)

