# R010 — Prompt or template change release

Last updated: 2025-12-22  
Default severity: **SEV-3 (planned) / SEV-1 (if emergency hotfix)**

---

## When to use this runbook
Use when:
- updating prompt(s), schemas, thresholds, or templates
- enabling/disabling templates
- changing routing mapping

Goal: make changes safely and reversibly.


---

## Immediate actions (stop the bleeding)
For emergency hotfix:
- consider `automation_enabled=false` while deploying
- keep routing stable if possible
- communicate to Support Ops

For planned changes:
- follow staged rollout and CI gates


---

## Diagnosis steps
Before change:
- identify what’s changing (prompt/template/schema/threshold)
- identify customer impact scope
- ensure you can roll back quickly

Validate change:
- run CI gates (schema validation + LLM regression gates)
- run smoke test pack in staging


---

## Mitigation / repair actions
Rollout pattern (recommended):
1) Deploy code/schema changes first (no behavior change)
2) Deploy templates/prompts as versioned artifacts
3) Enable feature flags gradually:
   - route-only first
   - Tier 1 templates next
   - Tier 2 templates last

Rollback pattern:
- revert to last known good artifact version
- disable template or disable automation if uncertain


---

## Verify recovery
- smoke test pack passes
- dashboards show stable error rates and no new misroute spikes
- feedback tags remain within expected range


---

## Post-incident follow-ups
- record change in Decision Log / Change Log
- update training if workflows changed


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard A — System Health (Wave 08)
- Dashboard C — Quality & Safety (Wave 08)
- Go/No-Go checklist (Wave 09)

### Metrics to check
- `mw.worker.jobs_failed_total`
- `mw.policy.automation_blocked_total`
- `mw.vendor.openai.errors_total`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, mw_release, ticket_id, mw_trace_id,
       decision.primary_intent, decision.template_id, decision.tier, decision.action
| filter ts >= ago(6h)
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- Deploy with automation disabled first; then progressive enablement (Wave 09 runbook).
- Rollback: set automation_enabled=false, revert template bundle, revert prompt/schema versions.

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- Minimum subset: ST-001..ST-005, ST-010, ST-040..ST-041, ST-060, ST-070..ST-071
- Recommended: run full Smoke_Test_Pack_v1.md


## Related docs
- [Go/no-go checklist](../../09_Deployment_Operations/Go_No_Go_Checklist.md)
- [Smoke test pack](../../08_Testing_Quality/Smoke_Test_Pack_v1.md)
- [LLM regression gates](../../08_Testing_Quality/LLM_Regression_Gates_Checklist.md)
- [Macro governance](../../05_FAQ_Automation/Macro_Alignment_and_Governance.md)

