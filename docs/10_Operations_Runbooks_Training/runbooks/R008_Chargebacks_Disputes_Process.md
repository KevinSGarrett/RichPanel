# R008 — Chargebacks / disputes process

Last updated: 2025-12-22  
Default severity: **SEV-2 (SEV-0 if mishandled at scale)**

---

## When to use this runbook
Use when:
- ticket intent is `chargeback_dispute`
- a customer threatens chargeback or mentions disputes with bank/card
- support team needs standard steps and escalation rules

This is primarily a workflow runbook, not a technical incident runbook.


---

## Immediate actions (stop the bleeding)
1) Ensure the ticket is assigned to the **Chargebacks / Disputes** team.
2) Confirm automation is not responding beyond neutral acknowledgement (Tier 0).
3) If chargeback tickets are being routed elsewhere, treat as SEV-1 routing defect and escalate.


---

## Diagnosis steps
- Confirm whether message is:
  - chargeback threat (pre-empt)
  - active dispute already filed
  - payment/billing confusion (may be Tier 1)
- Confirm whether the customer is requesting a refund vs disputing payment.


---

## Mitigation / repair actions
Operational steps (suggested):
- Acknowledge receipt and advise that the specialized team will review.
- Request minimal identifiers (order #) if missing.
- Follow internal chargeback/dispute SOP (outside scope of this doc set).
- Do not promise outcomes; avoid legal language.

Technical steps if misrouted:
- Apply feedback tags and open a routing defect task.


---

## Verify recovery
- Ticket is in the correct queue
- No automation reply with sensitive details was sent
- The team can proceed with internal process


---

## Post-incident follow-ups
- Add chargeback examples to Tier 0 adversarial set
- Ensure chargeback queue staffing coverage is adequate


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard C — Quality & Safety (Wave 08)

### Metrics to check
- `mw.policy.tier0_total`
- `mw.policy.decisions_total`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, ticket_id, mw_trace_id, decision.primary_intent, decision.tier, decision.action, decision.template_id
| filter decision.primary_intent = "chargeback_dispute"
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- Keep automation off for Tier 0; ensure policy engine blocks replies.
- Verify routing to Chargebacks/Disputes team and correct tags.

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- ST-010 (tier0 chargeback_dispute)
- ST-052 (multi-intent tier0 override)


## Related docs
- [Tier policies](../../04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md)
- [On-call escalation](../On_Call_and_Escalation.md)

