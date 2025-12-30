# R005 — Backlog catch-up and DLQ handling

Last updated: 2025-12-22  
Default severity: **SEV-1 (SEV-2 if small backlog)**

---

## When to use this runbook
Use when:
- SQS backlog grows and oldest message age exceeds target
- DLQ begins to accumulate messages
- worker throughput is below ingress rate


---

## Immediate actions (stop the bleeding)
1) Confirm customer harm risk
- If automation is enabled and backlog is large, consider:
  - `safe_mode=true`
  - possibly `automation_enabled=false` to reduce call volume

2) Stabilize the system
- ensure vendor rate limits are respected
- ensure worker concurrency isn't causing 429 storms

3) Do not “blast drain” backlog.
- Follow controlled catch-up strategy.


---

## Diagnosis steps
A) Determine backlog cause
- ingress spike?
- worker errors?
- vendor throttling?
- code regression causing slow processing?

B) Review DLQ reasons
- inspect a sample of DLQ messages (ticket IDs only where possible)
- categorize: validation errors vs vendor errors vs persistent failures

C) Check whether backlog is FIFO blocked
- a single stuck conversation group can block that group only, but FIFO queue overall still processes other groups depending on strategy


---

## Mitigation / repair actions
- Apply the controlled catch-up plan:
  - increment concurrency gradually
  - monitor 429s and costs
- For DLQ:
  - fix root cause first
  - then replay a small batch with idempotency protection
- If backlog is from vendor outage:
  - keep safe mode enabled until vendor recovers


---

## Verify recovery
- oldest message age decreases consistently
- DLQ stops increasing
- throughput exceeds ingress rate (for catch-up)


---

## Post-incident follow-ups
- Add alert on oldest message age if missing
- Postmortem if backlog exceeded SLA or caused customer harm


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard A — System Health (Wave 08)

### Metrics to check
- `mw.queue.depth`
- `mw.queue.oldest_age_s`
- `mw.queue.dlq_depth`
- `mw.worker.jobs_failed_total`
- `mw.worker.jobs_succeeded_total`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, ticket_id, mw_trace_id, sqs_message_id, result, vendor.error_class, vendor.error_code
| filter result = "failed" or event like /dlq/
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- Increase worker reserved concurrency gradually (Wave 07 playbook).
- Enter `safe_mode=true` during catch-up to reduce costly automation.
- Redrive DLQ only after root cause is fixed (Wave 07 backlog strategy).

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- ST-060 (duplicate webhook/idempotency)
- ST-070 (automation disabled during recovery)


## Related docs
- [Backlog catch-up and replay strategy](../../07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md)
- [Backlog catchup and replay strategy (supplement)](../../07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md)
- [Load testing plan](../../07_Reliability_Scaling/Load_Testing_and_Soak_Test_Plan.md)

