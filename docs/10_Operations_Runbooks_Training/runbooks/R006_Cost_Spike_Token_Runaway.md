# R006 — Cost spike / token runaway

Last updated: 2025-12-22  
Default severity: **SEV-2 (SEV-1 if uncontrolled)**

---

## When to use this runbook
Use when:
- OpenAI token usage spikes sharply
- unexpected increase in automation volume
- cost guardrail alarms fire


---

## Immediate actions (stop the bleeding)
1) Enter safe mode:
- `safe_mode=true`

2) If automation is contributing:
- `automation_enabled=false`

3) Reduce LLM call volume:
- disable optional enrichment calls
- enforce strict max token budgets


---

## Diagnosis steps
A) Identify driver
- more messages than usual?
- prompt/template change increased tokens?
- retry storm causing repeated LLM calls?
- missing caching causing repeated classification?

B) Inspect distribution
- which intents/templates are highest volume?
- which model config is used?

C) Confirm guardrails
- per-message max token budget
- per-day budget alerting


---

## Mitigation / repair actions
- Roll back prompt change if token inflation is from prompt
- Tighten prompt/context:
  - send minimal context (no full history unless needed)
- Add caching for stable lookups (tags, teams, etc.)
- Add “budget stop” behavior:
  - automatically disable automation when exceeding budget threshold (optional)


---

## Verify recovery
- token usage returns to baseline within 1–2 hours
- cost forecast stabilizes
- routing continues to function


---

## Post-incident follow-ups
- Add cost anomaly alert if missing
- Update cost guardrails docs and parameter defaults


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard C — Quality & Safety (Wave 08)
- Dashboard B — Vendor Health (Wave 08)

### Metrics to check
- `mw.cost.usd_estimate`
- `mw.cost.tokens_in_total`
- `mw.cost.tokens_out_total`
- `mw.vendor.openai.requests_total`
- `mw.vendor.openai.errors_total`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, mw_trace_id, ticket_id, decision.primary_intent,
       vendor.name, vendor.operation, vendor.latency_ms, vendor.error_code
| filter vendor.name = "openai"
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- Immediate: `automation_enabled=false` to reduce LLM calls from reply flows.
- Reduce worker concurrency to limit QPS.
- Switch to cheaper model / shorter context (Wave 04 model config) and re-run eval gates (Wave 09).

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- ST-070 (automation disabled) still routes correctly


## Related docs
- [Cost guardrails and budgeting](../../07_Reliability_Scaling/Cost_Guardrails_and_Budgeting.md)
- [Cost model](../../07_Reliability_Scaling/Cost_Model.md)
- [Kill switch and safe mode](../../06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md)

