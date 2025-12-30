# Docs Impact Map — Wave 10 Update 2

Generated: 2025-12-22

Wave 10 Update 2 focuses on **operational alignment** across Waves 06–09.

## Cross-wave links strengthened

### Wave 06 (Security / Kill switch)
Runbooks now consistently reference and operationalize:
- `safe_mode`
- `automation_enabled`
- per-template disablement (`template_enabled.<template_id>=false`)
Docs:
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`

### Wave 07 (Reliability / Tuning)
Runbooks now reference:
- reserved concurrency tuning
- backlog catch-up and DLQ handling strategy
Docs:
- `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`
- `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`

### Wave 08 (Observability)
Each runbook includes:
- dashboards to check (System Health / Vendor Health / Quality & Safety)
- metric names (e.g., `mw.queue.oldest_age_s`, `mw.vendor.openai.rate_limited_total`)
- PII-safe log query templates aligned with the v1 log schema
Docs:
- `docs/08_Observability_Analytics/Dashboards_Alerts_and_Reports.md`
- `docs/08_Observability_Analytics/Event_Taxonomy_and_Log_Schema.md`

### Wave 09 (Testing / Release readiness)
Each runbook includes:
- smoke-test IDs to validate “fixed” before restoring automation
Docs:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/09_Deployment_Operations/First_Production_Deploy_Runbook.md`

## Outcome
Operators can now follow a consistent flow:
1) symptom → dashboards/metrics
2) confirm via logs
3) apply safe lever(s)
4) validate with smoke tests
5) restore automation progressively
