# Analytics Data Model and Exports (Wave 08)

Last updated: 2025-12-22

This document defines how we generate **longer-term analytics** without storing raw PII.

v1 philosophy:
- CloudWatch is sufficient for day-to-day operations.
- For weekly/monthly product insights and drift analysis, export **sanitized structured events** to S3.

## Decision: analytics export posture (v1 default)

**Default (v1):** CloudWatch-first is **required** for operations. Sanitized S3 export is **optional**, but recommended once you are comfortable with the PII posture.

Best-suggested rollout:
- **Staging:** enable the S3 export pipeline early (to validate schema, partitioning, and access controls).
- **Prod:** start CloudWatch-only for the first rollout window; enable sanitized S3 export after you have:
  - verified redaction is correct in staging
  - validated the event schema doesn’t include message bodies
  - confirmed retention/deletion posture is acceptable for your org.

Rationale:
- avoids blocking go-live on analytics plumbing
- keeps long-term trending cheap and queryable once enabled (S3/Athena),
- reduces the risk of accidentally exporting sensitive payload fields.

---


## 1) What we export (and what we do NOT export)

### Exported (sanitized)
- middleware event logs (structured JSON)
- decision summaries (intent/department/tier/template_id/confidence)
- vendor call metadata (status/latency/retry)
- automation outcomes (sent/blocked/failed)
- override signals (tags/macros applied by agents)

### Not exported
- raw message text
- email/phone/address
- tracking URLs
- any secrets or auth headers

---

## 2) Recommended export pipeline (v1)

### Option A (recommended): CloudWatch Logs → subscription → Firehose → S3
- Subscription filter includes only middleware log groups
- Firehose delivers gzip-compressed JSON lines
- Optional later: convert to Parquet for cost/performance (not required v1)

### Option B (minimal): periodic CloudWatch Logs Insights queries
- Good for ad-hoc, but not ideal for long-term trending

---

## 3) S3 layout and partitioning (recommended)

Bucket: `s3://<org>-mw-analytics-<env>/`

Prefix design:
- `events/env=<env>/dt=<YYYY-MM-DD>/hr=<HH>/<OBJECT>.json.gz`
- `eval_runs/env=<env>/dt=<YYYY-MM-DD>/run_id=<RUN_ID>/<FILE>`

Example:
- `events/env=prod/dt=2025-12-22/hr=14/part-0000.json.gz`
- `eval_runs/env=prod/dt=2025-12-22/run_id=eval_<RUN_ID>/metrics.json`

This layout makes Athena queries fast and cheap.

---

## 4) Athena table sketch (JSON lines)

Event table:
- `mw_events_v1`

Suggested columns (projection):
- `ts` (timestamp)
- `event` (string)
- `env` (string)
- `ticket_id` (string)
- `mw_trace_id` (string)
- `channel` (string)
- `step` (string)
- `result` (string)
- `latency_ms` (double)
- `decision.primary_intent` (string)
- `decision.department` (string)
- `decision.tier` (int)
- `decision.template_id` (string)
- `decision.confidence` (double)
- `vendor.name` (string)
- `vendor.operation` (string)
- `vendor.http_status` (int)
- `vendor.retry_count` (int)

**Note:** any “rich” analysis fields should remain optional so schema evolution is painless.

---

## 5) Analytics use cases (v1)

### Operational trending
- weekly routing volume by channel/department
- backlog incidents frequency
- vendor error rate trends

### Quality trending
- confidence drift (histogram shifts)
- template usage anomalies
- override/misroute signal trends

### Automation ROI trending
- automation reply count
- estimated deflection proxy
- response time improvements (if ticket lifecycle data is available)

---

## 6) Retention and access controls
Retention and access are governed by Wave 06:
- `docs/06_Security_Privacy_Compliance/Data_Retention_and_Access.md`

Recommended defaults:
- CloudWatch logs: 30–90 days
- S3 exports: 180–365 days (sanitized)
- Eval artifacts: 180 days (sanitized)

Access:
- analytics bucket read is restricted to Engineering + Support Ops leads
- all access is audited (CloudTrail)

---

## 7) Schema evolution strategy
- Additive changes only for v1 (new optional fields)
- Any breaking changes require:
  - new versioned table (`mw_events_v2`)
  - update dashboards and eval tooling
  - entry in `Decision_Log.md` + `Change_Log.md`