# R003 — Automation wrong reply or PII risk

Last updated: 2025-12-22  
Default severity: **SEV-0 (treat as critical until proven otherwise)**

---

## When to use this runbook
Use when:
- any report of automation revealing wrong order details
- suspected disclosure of email/phone/order/tracking to the wrong person
- automation sends an obviously incorrect template at scale
- prompt injection / jailbreak causes unsafe output that escapes expected behavior

Even a single credible report should be treated as SEV-0 until contained.


---

## Immediate actions (stop the bleeding)
1) **Disable automation immediately**: `automation_enabled=false`

2) Enable conservative routing:
- `safe_mode=true`

3) Preserve evidence (without spreading PII):
- record affected ticket IDs (not message bodies)
- capture timestamps and template_id used
- capture release version (prompt/template/model schema versions)

4) Notify leadership and Support Ops immediately.


---

## Diagnosis steps
A) Determine what happened
- wrong template_id selected?
- deterministic match incorrectly passed? (Tier 2 gate failure)
- template rendering bug? (variables filled incorrectly)
- order lookup bug (wrong order linked)?
- human misinterpretation (not automation)?

B) Check gating logs (PII-safe)
- confirm Tier 2 verifier outcome
- confirm “eligible_for_tier2” was true only when deterministic match existed
- confirm policy engine enforced Tier 0/Tier 2 rules

C) Scope the incident
- how many tickets in timeframe have `mw:automation_sent:true`?
- are they all same intent/template?
- is it a single channel?

D) If PII exposure is possible
- follow Wave 06 security incident runbook procedures
- consider customer notification depending on severity and policy


---

## Mitigation / repair actions
- Keep automation disabled until root cause fixed and validated.
- If it’s a specific template or intent:
  - disable only that template via template enablement flag (optional) after global automation is already off
- Roll back to last known good template/prompt release.
- If deterministic match is unreliable:
  - temporarily downgrade order status to Tier 1 ask-for-order# only.


---

## Verify recovery
- No new incorrect auto-replies observed
- Sampled tickets show automation is off
- Gate logs show deterministic match enforced
- Fix validated in staging with Smoke Test Pack


---

## Post-incident follow-ups
- Postmortem required
- Add/strengthen tests:
  - Tier 2 gating unit tests
  - “PII leak” adversarial cases in golden set
- Review whether additional redaction/logging safeguards are needed


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard C — Quality & Safety (Wave 08)
- Security monitoring dashboards (Wave 06)
- Dashboard B — Vendor Health (Wave 08)

### Metrics to check
- `mw.policy.automation_attempt_total`
- `mw.policy.automation_blocked_total`
- `mw.vendor.richpanel.errors_total`
- `mw.vendor.openai.errors_total`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, ticket_id, mw_trace_id, channel,
       decision.primary_intent, decision.tier, decision.template_id, decision.action,
       vendor.name, vendor.operation, vendor.http_status, vendor.error_code
| filter event in ["policy.decision.made","action.send_reply.attempt","action.send_reply.result","vendor.call.failed"]
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- Immediate: `automation_enabled=false` (stop replies).
- Then: `safe_mode=true` (route-only) to prevent further harm while investigating.
- Disable specific template(s): `template_enabled.<template_id>=false`.

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- ST-040 (tier2_verified_no_match)
- ST-041 (tier2_verified_match)
- ST-010 (tier0 chargeback_dispute)
- ST-070/071 (kill switch tests)


## Related docs
- [Kill switch and safe mode](../../06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md)
- [Incident response security runbooks](../../06_Security_Privacy_Compliance/Incident_Response_Security_Runbooks.md)
- [Order status automation spec](../../05_FAQ_Automation/Order_Status_Automation.md)
- [Smoke test pack](../../08_Testing_Quality/Smoke_Test_Pack_v1.md)

