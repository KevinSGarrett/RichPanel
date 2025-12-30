# Observability, Analytics, and EvalOps Overview (Wave 08)

Last updated: 2025-12-22

Wave 08 defines the **production observability and quality monitoring** plan for the Richpanel routing + FAQ automation middleware.

This wave focuses on:
- **Operational observability** (logs, metrics, traces) for the serverless pipeline (API Gateway → Lambda → SQS FIFO → Lambda worker)
- **Product analytics** (routing outcomes, template usage, deflections, SLA impact)
- **Evaluation operations** (scheduled eval runs, drift detection, threshold recalibration, human feedback loops)

This wave is intentionally designed to be:
- **Security-aware** (PII-safe, aligned to Wave 06 controls)
- **Operator-friendly** (dashboards + alarms map to clear actions)
- **Low-ops** for v1 (CloudWatch first; optional exports later)

---

## 1) Scope and goals

### Goals (v1)
1) Make failures **visible within minutes**, not hours (routing failures, vendor outages, DLQ growth).
2) Make “silent quality failures” visible:
   - misroutes / wrong-team assignments
   - automation mistakes prevented by the policy engine
   - automation that is technically correct but creates customer friction
3) Provide a **continuous quality loop**:
   - daily sampling
   - weekly eval on the golden set
   - monthly (or as-needed) calibration of thresholds
4) Provide a **single source of truth** for “what happened” per ticket:
   - which model/prompt/template version
   - which decision path (Tier 0/1/2)
   - which downstream calls succeeded/failed

### Non-goals (v1)
- “Perfect BI” or heavy data-warehouse modeling
- Multi-region distributed tracing
- Storing raw customer message bodies for analytics (not allowed by default)

---

## 2) Design principles

1) **Security first**
   - No raw message bodies in prod logs by default.
   - Redaction and minimization are mandatory.
   - See: `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`

2) **Actionable metrics**
   - Every alarm must map to an operator action.
   - “Nice-to-have” metrics are still logged, but not alarmed.

3) **Consistent correlation**
   - All stages emit the same correlation identifiers:
     - `mw_trace_id` (generated at ingress)
     - `ticket_id` (Richpanel ticket / conversation id)
     - `mw_event_id` / `idempotency_key`
     - `mw_release` / `prompt_version` / `template_version`

4) **Fail-closed behavior is observable**
   - Any time the policy engine blocks automation, we emit a structured event.

---

## 3) Observability layers

### A) Logs (primary forensic source)
- Structured JSON logs (one event per major processing step)
- Stored in CloudWatch Logs
- Optional: export sanitized events to S3 for long retention + analytics

Docs:
- `Event_Taxonomy_and_Log_Schema.md`

### B) Metrics (primary alerting source)
- CloudWatch metrics for:
  - latency and throughput
  - error rates and 429s
  - queue depth/age, DLQ growth
  - automation counts by template_id
  - safety events (Tier 0 hits, blocked automation)
Docs:
- `Metrics_Catalog_and_SLO_Instrumentation.md`

### C) Tracing (optional but recommended)
- AWS X-Ray or OpenTelemetry tracing for:
  - ingress → enqueue → worker
  - downstream spans (Richpanel/OpenAI/Shopify) without PII
Docs:
- `Tracing_and_Correlation.md`

---

## 4) Analytics + reporting layers

### A) Operational dashboards (v1 required)
- “Ops” dashboard: health + SLOs
- “Quality” dashboard: confidence distribution, override rate, blocked automation
- “Automation impact” dashboard: auto-replies, deflections, time-to-first-response improvements
Docs:
- `Dashboards_Alerts_and_Reports.md`

### B) Optional exports for deeper analytics (v1 recommended if time allows)
- CloudWatch Logs subscription → Kinesis Firehose → S3 (sanitized events)
- Athena queries for weekly/monthly trend analysis
Docs:
- `Analytics_Data_Model_and_Exports.md`

---

## 5) Evaluation operations (“EvalOps”)

We treat model quality as **an operational metric**, not a one-time setup.

EvalOps includes:
- scheduled eval runs (golden set + fresh samples)
- drift detection + alerting (confidence drift, intent distribution drift, override drift)
- threshold calibration and controlled release

Docs:
- `EvalOps_Scheduling_and_Runbooks.md`
- `Quality_Monitoring_and_Drift_Detection.md`

---

## 6) Cross references
- Security-aware observability constraints: `docs/06_Security_Privacy_Compliance/Logging_Metrics_Tracing.md`
- Reliability scaling triggers: `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`
- LLM decision contract + gates: `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- Template IDs and copy: `docs/04_LLM_Design_Evaluation/Template_ID_Catalog.md` and `docs/05_FAQ_Automation/Templates_Library_v1.md`

---

## 7) Wave 08 output checklist
See: `Wave08_Definition_of_Done_Checklist.md`
