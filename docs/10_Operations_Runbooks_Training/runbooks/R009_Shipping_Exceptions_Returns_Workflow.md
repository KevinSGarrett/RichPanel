# R009 — Shipping exceptions / returns workflow

Last updated: 2025-12-22  
Default severity: **SEV-3 (workflow) / SEV-2 (if automation misbehaves)**

---

## When to use this runbook
Use when:
- intent: missing items, wrong items, damaged in transit, lost, delivered-not-received
- support wants the standard “intake first” playbook


---

## Immediate actions (stop the bleeding)
1) Ensure ticket routes to Returns Admin (v1 simplicity).
2) If automation is enabled, confirm it only sends Tier 1 intake messages (no promises).
3) If “delivered-not-received” and customer is angry, consider immediate human reply.


---

## Diagnosis steps
- Determine which category applies:
  - missing items
  - incorrect items
  - damaged
  - lost in transit
  - delivered-not-received
- Confirm whether order identifiers exist.
- Confirm whether photos/packing slip evidence is required by policy.


---

## Mitigation / repair actions
Suggested intake (Tier 1 safe assist):
- ask for order #
- list missing/incorrect items
- ask about packaging damage
- ask for photo evidence if required

Do not:
- commit to refund/reship before investigation
- disclose addresses or payment info via automation


---

## Verify recovery
- Returns Admin receives ticket with needed info
- reduced back-and-forth
- customer receives a clear next step


---

## Post-incident follow-ups
- Update templates if the policy changes
- Add representative examples to golden set for intent classification


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard A — System Health (Wave 08)
- Dashboard C — Quality & Safety (Wave 08)

### Metrics to check
- `mw.policy.decisions_total`
- `mw.policy.automation_attempt_total`
- `mw.vendor.richpanel.errors_total`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, ticket_id, mw_trace_id, channel,
       decision.primary_intent, decision.tier, decision.template_id, decision.action
| filter decision.primary_intent in ["delivered_not_received","missing_items_in_shipment","return_request","refund_request"]
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- If intake replies are wrong/too frequent: disable specific intake template(s).
- If escalations are needed: set safe_mode=true (route-only) temporarily.

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- ST-022 (DNR tier1 intake)
- ST-023 (missing items intake)
- ST-030 (return request intake)
- ST-032 (refund request intake)
- ST-071 (safe_mode route-only)


## Related docs
- [Top FAQs playbooks](../../05_FAQ_Automation/Top_FAQs_Playbooks.md)
- [Templates library](../../05_FAQ_Automation/Templates_Library_v1.md)

