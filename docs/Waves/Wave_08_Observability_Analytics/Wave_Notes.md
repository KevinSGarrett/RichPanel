# Wave 8 — Observability, analytics, and evaluation ops

Last updated: 2025-12-22

This wave turns the architecture into an **operable** system by defining:
- what we log/measure
- how we alert
- how we monitor quality/drift
- how we run evaluations continuously (EvalOps)

---

## Goals
1) Make routing + automation failures visible quickly (minutes).
2) Make quality regressions visible (misroutes, automation issues).
3) Provide an EvalOps cadence: daily sampling, weekly golden-set eval, monthly calibration.
4) Keep everything PII-safe by default.

---

## Deliverables (Wave 08)
Core docs (under `docs/08_Observability_Analytics/`):
- `Observability_Analytics_Overview.md`
- `Event_Taxonomy_and_Log_Schema.md`
- `observability_event_taxonomy_v1.yaml`
- `schemas/mw_observability_event_v1.schema.json`
- `Metrics_Catalog_and_SLO_Instrumentation.md`
- `Tracing_and_Correlation.md`
- `Dashboards_Alerts_and_Reports.md`
- `Analytics_Data_Model_and_Exports.md`
- `Quality_Monitoring_and_Drift_Detection.md`
- `EvalOps_Scheduling_and_Runbooks.md`
- `Feedback_Signals_and_Agent_Override_Macros.md`
- `Wave08_Definition_of_Done_Checklist.md`
- `Cross_Wave_Alignment_Map.md`
- `Operator_Quick_Start_Runbook.md`

---

## Status
- **Started** ✅ (Wave 08 Update 1 — docs created and linked)
- **Update 2** ✅ (cross-wave alignment + operator quick start + analytics export decision)
- **Wave 08 status:** ✅ Complete

---

## Notes / follow-ups
- Cross-wave consistency alignment is tracked in the Wave 08 DoD checklist:
  - ensure dashboard alarms match Wave 06 + Wave 07 docs
- Tenant capability verification for Richpanel webhooks is still deferred; Wave 08 plans include fallbacks.
