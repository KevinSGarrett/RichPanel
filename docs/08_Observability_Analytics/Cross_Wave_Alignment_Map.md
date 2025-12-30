# Cross-Wave Alignment Map (Waves 06–08)

Last updated: 2025-12-22  
Status: **Final (Wave 08 Update 2)**

This document prevents “split brain” across:
- **Wave 06** — security/privacy monitoring + incident response
- **Wave 07** — reliability/scaling/capacity + tuning/degraded modes
- **Wave 08** — observability/analytics/eval ops + quality/drift

If two docs conflict, follow this priority:
1) Wave 06 for **security/privacy** response and monitoring
2) Wave 07 for **system reliability/capacity** response and tuning
3) Wave 08 for **quality/product/analytics** monitoring and reporting

---

## 1) What each wave owns (source of truth)

### Wave 06 (Security/Privacy/Compliance)
Owns:
- invalid/spoofed webhook detection
- key rotation + break-glass access
- PII leak response
- “kill switch / safe mode” design

Docs:
- `docs/06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md`
- `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`

### Wave 07 (Reliability/Scaling/Capacity)
Owns:
- queue health, backlog, DLQ handling
- concurrency tuning
- retry/backoff posture
- catch-up / replay strategy

Docs:
- `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`
- `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`

### Wave 08 (Observability/Analytics/EvalOps)
Owns:
- log/event schema and metric taxonomy
- dashboards + reporting cadence
- drift detection + EvalOps cadence
- agent feedback signal schema

Docs:
- `docs/08_Observability_Analytics/Event_Taxonomy_and_Log_Schema.md`
- `docs/08_Observability_Analytics/Metrics_Catalog_and_SLO_Instrumentation.md`
- `docs/08_Observability_Analytics/Operator_Quick_Start_Runbook.md`

---

## 2) Field alignment: decision schema ↔ observability events

**Requirement:** any field required for dashboards/analytics must be present in the middleware “decision output” schema (`mw_decision_v1`) or derived deterministically.

Minimum decision fields referenced by Wave 08 analytics:
- `primary_intent`
- `department`
- `tier`
- `template_id` (optional, only when automation is eligible)
- `confidence`
- `reasons` / `notes` (optional, not for metrics)

Wave 08 events store these under a `decision.*` object in structured logs.  
See: `docs/08_Observability_Analytics/Event_Taxonomy_and_Log_Schema.md`

---

## 3) Alarm map (minimum)

| Alarm class | Primary signal | Where thresholds are defined | Runbook |
|---|---|---|---|
| Webhook abuse / invalid token spike | invalid auth count | Wave 06 | Wave 06 incident runbooks |
| PII leak suspicion | policy violations / manual report | Wave 06 | Wave 06 incident runbooks |
| Queue backlog / oldest age rising | SQS age + depth | Wave 07 | Wave 07 tuning playbook |
| DLQ > 0 | DLQ count / age | Wave 07 | Wave 07 replay strategy |
| Vendor 429 storms | 429 rate | Wave 07 (ops) + Wave 06 (abuse) | Wave 07 tuning |
| Quality regression | feedback tags + eval results | Wave 08 | Wave 08 EvalOps + Wave 04 calibration |

Note: Wave 08 dashboards should *display* the above metrics, but do not override thresholds owned by Wave 06/07.

---

## 4) Degraded modes alignment

Degraded modes (Wave 07) must be visible in dashboards (Wave 08) and actionable from runbooks (Wave 06/07):

- `safe_mode=true`  
  - dashboard: show “route-only mode active”
  - effect: blocks automation, routing continues
- `automation_enabled=false`  
  - dashboard: show “automation disabled”
  - effect: no auto-replies

See:
- Wave 06 kill switch: `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- Wave 07 tuning: `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`

---

## 5) Wave 08 Update 2 verification (what we checked)

- Dashboards doc references Wave 06 + Wave 07 as authoritative.
- Metrics catalog contains queue/vendor/policy metrics needed by Wave 06/07 alarms.
- Operator quick start links to the correct deeper runbooks.
