# Docs Impact Map — Wave 08 Update 1

Date: 2025-12-22  
Wave: 08 (Observability/Analytics/EvalOps) — Update 1 (start)

This file lists **what changed** and **why it matters**.

---

## High impact changes

### 1) Canonical observability contract (events + schema)
Files:
- `docs/08_Observability_Analytics/Event_Taxonomy_and_Log_Schema.md`
- `docs/08_Observability_Analytics/observability_event_taxonomy_v1.yaml`
- `docs/08_Observability_Analytics/schemas/mw_observability_event_v1.schema.json`

Impact:
- Defines a stable instrumentation contract for ingress/worker/policy/actions.
- Enables consistent timeline reconstruction and safer analytics exports.
- Makes investigations faster and reduces “unknown unknowns”.

### 2) Metrics catalog mapped to SLOs and alarms
Files:
- `docs/08_Observability_Analytics/Metrics_Catalog_and_SLO_Instrumentation.md`

Impact:
- Prevents metric sprawl and high-cardinality cost issues.
- Ensures alarms tie directly to actionable metrics.

### 3) Quality monitoring and drift detection
Files:
- `docs/08_Observability_Analytics/Quality_Monitoring_and_Drift_Detection.md`
- `docs/08_Observability_Analytics/EvalOps_Scheduling_and_Runbooks.md`

Impact:
- Treats routing quality as an operational metric (not a one-time launch task).
- Provides repeatable response playbooks for regressions.

### 4) Feedback signals spec (agent overrides)
Files:
- `docs/08_Observability_Analytics/Feedback_Signals_and_Agent_Override_Macros.md`

Impact:
- Defines a high-signal feedback loop to improve routing and automation quickly.
- Enables drift detection based on explicit corrections.

---

## What to read first
If you read only 3 files from this update:
1) `docs/08_Observability_Analytics/Event_Taxonomy_and_Log_Schema.md`
2) `docs/08_Observability_Analytics/Dashboards_Alerts_and_Reports.md`
3) `docs/08_Observability_Analytics/Quality_Monitoring_and_Drift_Detection.md`
