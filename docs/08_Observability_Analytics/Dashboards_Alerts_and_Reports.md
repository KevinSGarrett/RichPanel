# Dashboards, Alerts, and Reports (Wave 08)

Last updated: 2025-12-22

This document defines the **minimum dashboards** and **reporting cadence** needed to operate the middleware safely.

Important:
- **Security-focused** alarms/dashboards are defined in Wave 06:
  - `docs/06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md`
- **Reliability tuning** triggers and degraded-mode actions are defined in Wave 07:
  - `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`

Wave 08 builds the “day-to-day ops + product quality” layer on top.

Operator quick start:
- `docs/08_Observability_Analytics/Operator_Quick_Start_Runbook.md`

Cross-wave alignment (Waves 06–08):
- `docs/08_Observability_Analytics/Cross_Wave_Alignment_Map.md`


---

## 1) Required dashboards (v1)

### Dashboard A — System Health (SLO dashboard)
Purpose: ensure routing is working and meeting latency targets.

Widgets (minimum):
- Ingress:
  - `mw.ingress.requests_total`
  - `mw.ingress.rejected_total`
  - `mw.ingress.ack_latency_ms` (p50/p95/p99)
- Queue:
  - `mw.queue.depth`
  - `mw.queue.oldest_age_s`
  - `mw.queue.dlq_depth`
- Worker:
  - `mw.worker.jobs_failed_total`
  - `mw.worker.end_to_end_latency_ms` (p50/p95/p99)

### Dashboard B — Vendor Health
Purpose: detect downstream outages and rate-limit storms early.

Widgets:
- OpenAI:
  - requests, errors, 429s, latency
- Richpanel:
  - requests, errors, 429s, latency
- (Optional) Shopify:
  - requests, errors, latency

### Dashboard C — Automation (Impact + Safety)
Purpose: ensure automation is helpful and not causing harm.

Widgets:
- `mw.policy.automation_attempt_total`
- `mw.policy.automation_blocked_total`
- `mw.automation.reply_sent_total`
- `mw.automation.reply_failed_total`
- `mw.policy.tier0_total` (should be non-zero over time)
- “safe mode enabled time” (from logs or a metric)

Recommended (from exports/logs):
- template_id usage over time
- deterministic-match success rate for Tier 2

### Dashboard D — Quality (Routing + Drift)
Purpose: detect misroutes, threshold drift, and “model getting worse”.

Widgets (v1 metric-friendly):
- confidence distribution snapshots (coarse bins from logs/export)
- automation blocked rate (should be stable)
- override signals per day/week (from tags/macros; see `Feedback_Signals_and_Agent_Override_Macros.md`)
- intent distribution shifts (from exports)

### Dashboard E — Cost
Purpose: prevent surprise spend and detect runaway loops.

Widgets:
- estimated OpenAI cost/day
- tokens/day
- tokens/message (rolling)
- spike alerts tied to budgets

---

## 2) Alert strategy (v1)

### Alarm classes
1) **Paging alarms** (must act immediately)
   - DLQ > 0 (sustained)
   - queue oldest age > threshold
   - ingress rejected spike (auth failure/abuse)
   - worker error spike (sustained)
2) **Ticket/Slack alerts** (act within business hours)
   - confidence distribution drift
   - template usage anomaly
   - automation blocked anomaly
   - cost anomaly warning

### Where alarms point
Every alarm must link to:
- the relevant runbook section
- the kill switch / safe mode doc (Wave 06)
- the tuning playbook (Wave 07)

---

## 3) Reports and cadence

### Daily (Support Ops / Engineering)
- total inbound volume
- routed distribution by department
- auto replies sent + failure rate
- top 5 intents and templates
- backlog and DLQ summary
- any alarm incidents and mitigation actions taken

### Weekly (Quality + calibration)
- override/misroute signals
- “unknown/other” rate (if used)
- Tier 0 false positives/negatives (from QA sampling)
- drift indicators:
  - confidence histogram shifts
  - intent distribution shifts
  - template mix shifts

### Monthly (Governance)
- threshold calibration recommendation
- prompt/template version changes and impact
- spend vs ROI trend

---

## 4) Dashboard implementation notes
- v1 default: CloudWatch dashboards + CloudWatch alarms
- optional: export sanitized logs to S3 + Athena for “weekly/monthly” queries

A starter dashboard JSON stub lives in:
- `dashboards/cloudwatch_dashboard_stub_v1.json`
