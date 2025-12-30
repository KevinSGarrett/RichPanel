# R002 — Misrouting spike

Last updated: 2025-12-22  
Default severity: **SEV-2 (SEV-1 if widespread and customer-impacting)**

---

## When to use this runbook
Use when:
- spike in `mw:feedback:misroute` / override tags
- support agents report “wrong team” frequently
- confusion matrix shows new dominant error pair
- a recent model/prompt/template change correlates with worse routing


---

## Immediate actions (stop the bleeding)
1) If misroutes are causing customer harm at scale:
   - enable `safe_mode=true` (route-only conservative)
   - optionally restrict automation templates if they are contributing

2) If caused by a recent change:
   - roll back prompt/model/template to last known good release

3) Notify Support Ops so agents know to treat routing tags as suggestions during mitigation.


---

## Diagnosis steps
A) Confirm scope
- which channels? (LiveChat vs email)
- which intents/teams affected?
- is it all messages or a subset (language, product line, keywords)?

B) Check for drift triggers
- new product launch / promo keywords
- seasonal shipping issues
- new policy or macro changes that altered wording

C) Validate that gating is still correct
- Tier 0 intents must still route safely
- Tier 2 deterministic-match must still be enforced

D) Review sample set
- Pull 20–50 recent misrouted tickets
- Compare what the customer asked vs selected intent/team
- Identify new “missing intent” or taxonomy gap vs threshold issue.


---

## Mitigation / repair actions
- If taxonomy gap:
  - add a new intent or refine definitions (Wave 04 labeling guide)
  - add a few-shot example to prompt library
- If threshold issue:
  - adjust confidence thresholds and re-run eval gates
- If content shift:
  - add keyword-based pre-filters for known high-signal patterns (non-LLM guardrail)
- If the model is unstable:
  - switch to a more reliable model config for routing (still schema-validated)


---

## Verify recovery
- feedback tags return to baseline
- spot-check 20 tickets across teams shows improved routing
- eval run shows improved precision/recall for top affected intents


---

## Post-incident follow-ups
- Document taxonomy changes and update the labeling guide
- Add misroute examples to the golden set
- Add an alert: “misroute feedback rate” threshold


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard C — Quality & Safety (Wave 08)
- Dashboard A — System Health (Wave 08)

### Metrics to check
- `mw.policy.decisions_total`
- `mw.policy.tier0_total`
- `mw.policy.automation_attempt_total`
- `mw.policy.automation_blocked_total`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, ticket_id, mw_trace_id, channel,
       decision.primary_intent, decision.department, decision.tier, decision.confidence, decision.template_id
| filter event = "policy.decision.made"
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- Enter `safe_mode=true` (route-only) if customers are being harmed.
- Disable automation: `automation_enabled=false`.
- Raise confidence thresholds or tighten priority rules (Wave 04).

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- ST-001..ST-005 (route-only baseline set)
- ST-050..ST-052 (multi_intent priority enforcement)


## Related docs
- [Intent taxonomy and labeling guide](../../04_LLM_Design_Evaluation/Intent_Taxonomy_and_Labeling_Guide.md)
- [Quality monitoring and drift detection](../../08_Observability_Analytics/Quality_Monitoring_and_Drift_Detection.md)
- [LLM regression gates](../../08_Testing_Quality/LLM_Regression_Gates_Checklist.md)

