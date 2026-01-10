# Operator Quick Start Runbook (Wave 08)

Last updated: 2025-12-22  
Status: **Final (Wave 08 Update 2)**

This runbook is the fastest way to answer: **“Is the middleware healthy?”** and **“What should I do next?”**  
It is written for *operators* (engineering + support ops) and intentionally links to the deeper runbooks in Waves 06–07.

Related:
- Security monitoring + incident runbooks: `docs/06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md`
- Kill switch / safe mode: `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- Tuning playbook + degraded modes: `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`
- Backlog catch-up / replay: `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`

---

## 1) 60‑second health check

1. **Check alerts first**
   - DLQ > 0?
   - Queue “oldest message age” increasing?
   - Worker errors/throttles?
   - Vendor 429 spikes (Richpanel / OpenAI)?

2. **Check the “System Health” dashboard**
   - ingress ACK success rate (should be ~100%)
   - queue age + backlog
   - end-to-end latency p95 (routing/automation)
   - automation enabled? safe mode?

If alerts are firing: follow the relevant “Top investigations” below.

---

## 2) The two emergency levers (safe by default)

These are **non-code** levers and should be used early if anything looks unsafe:

1) **Route‑Only Safe Mode**
- Set `safe_mode=true`
- Effect: routing continues, automation is blocked
- Use when: quality/safety is in doubt (wrong replies, possible PII leak, model instability)

2) **Hard stop for automation**
- Set `automation_enabled=false`
- Effect: no auto-replies, even if safe_mode is off
- Use when: you suspect loops or runaway costs, or any mass-customer-impacting issue

See: `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`

---

## 3) Top 10 investigations (symptom → checks → actions)

### 1) “Customers say we sent the wrong automated message”
**Checks**
- Is automation enabled?
- Look for spikes in:
  - `mw.policy.automation_sent_total`
  - `mw.policy.automation_blocked_total`
  - agent feedback tags (`mw_feedback_auto_reply_wrong`) if adopted

**Immediate action**
- Turn on `safe_mode=true` (route-only)
- If the issue appears widespread: set `automation_enabled=false`

**Follow-up**
- Run the latest EvalOps regression (Wave 08) and compare against baseline.
- Review recent prompt/template changes (Wave 05 + Wave 04).

---

### 2) “Possible PII leak” (high severity)
**Checks**
- Any logs containing raw message bodies? (should be *no* by policy)
- Any abnormal spikes in “redaction failed” events (if instrumented)

**Immediate action**
- Set `automation_enabled=false` and `safe_mode=true`
- Trigger the security incident runbook:  
  `docs/06_Security_Privacy_Compliance/Incident_Response_Security_Runbooks.md`

---

### 3) “Messages aren’t routing / tickets aren’t getting tags”
**Checks**
- ingress requests_total increasing but worker processed_total flat?
- SQS backlog / oldest message age
- Worker errors or throttles

**Immediate action**
- If queue is growing: increase worker concurrency *gradually* (Wave 07 tuning playbook)
- If vendor 429 spikes: reduce concurrency and let queue buffer

---

### 4) “Queue backlog keeps growing”
**Checks**
- `mw.queue.depth` and `mw.queue.oldest_message_age_seconds`
- worker concurrency vs throttles
- vendor latency (OpenAI/Richpanel)

**Immediate action**
- Apply the tuning playbook:
  - raise concurrency if CPU/timeouts allow and vendor isn’t rate-limiting
  - lower concurrency if 429s rise (vendor is the limiter)
- If backlog is extreme, follow `Backlog_Catchup_and_Replay_Strategy.md`

---

### 5) “DLQ is non-zero”
**Checks**
- DLQ age and count
- Common failure reason (timeout, 429 exhaustion, schema validation failure, auth failure)

**Immediate action**
- Do **not** blind-redrive.
- Sample a small set first, classify failure category, then redrive with throttling.

See: `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`

---

### 6) “Richpanel is returning 429 / rate limited”
**Checks**
- `mw.vendor.richpanel.http_429_total` trending up
- retry counts increasing

**Immediate action**
- Reduce worker concurrency
- Ensure retries respect `Retry-After`
- Keep queue buffering; do not drop events

---

### 7) “OpenAI latency/errors rising”
**Checks**
- `mw.vendor.openai.errors_total` + latency metrics
- timeouts on worker

**Immediate action**
- Enter route-only mode (`safe_mode=true`) if automation depends on OpenAI quality
- Reduce concurrency if retries are amplifying load
- Consider temporary model downgrade only if documented (Wave 04 model versioning)

---

### 8) “Automation loops / duplicate replies”
**Checks**
- spikes in automation_sent_total for the same ticket family (if correlated)
- evidence of inbound triggers firing on our own outbound messages (integration issue)

**Immediate action**
- `automation_enabled=false`
- verify idempotency tags/keys are applied
- verify Richpanel rules are not re-triggering (Wave 03 design + deferred tenant checks)

---

### 9) “Costs spiking” (token/runaway)
**Checks**
- average prompt tokens
- automation_sent_total increase
- OpenAI usage logs (sanitized)

**Immediate action**
- Disable automation (`automation_enabled=false`)
- Reduce template scope (disable high-volume templates first)
- Re-run offline eval and inspect worst offenders

---

### 10) “Quality drift / misroutes increasing”
**Checks**
- agent feedback tags (`mw_feedback_misroute`) if adopted
- confusion matrix drift on weekly eval run
- changes in traffic mix (new products, new promos, new issues)

**Immediate action**
- Route-only mode if high-risk categories are affected
- Adjust thresholds (Wave 04) only after a regression run
- Expand golden set and re-run evals

---

## 4) Fast log search (PII-safe)

**Rule:** we do not search by customer email/phone/address. Use ticket_id / request_id.

Example CloudWatch Logs Insights queries (pseudo):

1) Find events by ticket_id
```sql
fields @timestamp, event, ticket_id, correlation_id, result, latency_ms
| filter ticket_id = "TICKET_ID_HERE"
| sort @timestamp desc
| limit 200
```

2) Find errors in the last 15 minutes
```sql
fields @timestamp, event, result, error.type, error.message
| filter result = "error"
| filter @timestamp > ago(15m)
| sort @timestamp desc
| limit 200
```

---

## 5) Operator cadence (recommended)

Daily (5 minutes):
- check dashboard
- check DLQ
- check vendor 429 trend

Weekly:
- review eval run results + feedback tags
- review top automation templates by volume + outcomes

Monthly:
- calibration review (thresholds, taxonomy drift, new-intent candidates)


---

## 6) DEV proof window (Richpanel middleware)
- Secret prerequisite: AWS Secrets Manager must contain `/rp-mw/dev/richpanel/api_key` (default lookup uses `MW_ENV=dev`).
- Enable outbound for the proof window: set `RICHPANEL_OUTBOUND_ENABLED=true` on the worker. Keep `safe_mode` / `automation_enabled` aligned with the proof scope.
- If SSM writes are blocked: set `MW_ALLOW_ENV_FLAG_OVERRIDE=true` plus `MW_SAFE_MODE_OVERRIDE=false` and `MW_AUTOMATION_ENABLED_OVERRIDE=true` for the window; remove afterward.
- Evidence capture (CLI-friendly):
  - DynamoDB: query `rp_mw_dev_idempotency` by `event_id` for `status`, `payload_sha256`, and `payload_bytes` (no payload bodies stored).
  - CloudWatch Logs: filter `/aws/lambda/rp-mw-dev-worker` (and ingress) on `event_id` with markers like `worker.processed`, `automation.routing_tags.applied`, `automation.order_status_reply.sent` to bound the proof window.
