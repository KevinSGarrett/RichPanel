# R001 — Webhook failures and duplicate storms

Last updated: 2025-12-22  
Default severity: **SEV-1 (can be SEV-0 if causing wrong replies)**

---

## When to use this runbook
Use when:
- API Gateway or ingress Lambda errors spike
- Richpanel stops triggering or triggers repeatedly
- duplicated automation messages are observed
- idempotency table indicates repeated event keys (or missing keys)

Common symptoms:
- sudden increase in inbound events but no routing outcomes
- repeated tags being applied
- repeated auto-replies (should be prevented by action idempotency)


---

## Immediate actions (stop the bleeding)
1) **Enable safe mode**: `safe_mode=true`  
   This keeps routing conservative and prevents risky automation.

2) If customers are receiving repeated/wrong messages:
   - **Disable automation**: `automation_enabled=false`

3) Confirm ingress ACK behavior:
   - Ingress must respond 2xx quickly after enqueueing.
   - If it’s failing before enqueue, treat as **data loss risk**.

4) If duplicates are overwhelming workers:
   - Temporarily lower worker concurrency
   - Consider pausing processing by disabling the worker event source mapping (only if absolutely necessary and you understand backlog impact)


---

## Diagnosis steps
A) Check ingress health
- API Gateway 4xx/5xx spikes
- Lambda ingress error count and duration
- WAF blocks (if enabled)

B) Check whether duplicates are from:
- Richpanel retries (same ticket triggers repeatedly)
- internal retries (worker reprocessing)
- multiple automation rules firing the same HTTP Target

C) Verify idempotency keys
- Confirm idempotency keys are based on stable identifiers:
  - ticket_id + message_id (preferred) OR
  - ticket_id + inbound_timestamp (fallback)
- Confirm conditional writes are working (no “overwrite” behavior).

D) Look for automation loops
- Does the middleware’s own outbound message re-trigger the inbound rule?
  - Ensure inbound trigger is customer messages only.
  - Ensure tag guard exists (`mw:routed:true` or `mw:processed:true`).


---

## Mitigation / repair actions
If ingress is failing:
- Fix request validation/auth configuration
- Reduce payload to minimal (ticket_id only)
- Ensure secrets/token not expired

If duplicates are from Richpanel rule configuration:
- Add “tag not present” guard:
  - do not trigger if `mw:processed:true` already applied
- Ensure middleware trigger rule is early in ordering and does NOT “skip subsequent rules” unless intended.

If duplicates are from worker retries:
- Confirm vendor calls handle `Retry-After` and use jittered backoff.
- Confirm DLQ behavior is configured and not immediately redriving.

If duplicates are causing wrong replies:
- Keep automation off until you confirm action-level idempotency is working.


---

## Verify recovery
- Ingress success rate returns to normal
- Queue depth stabilizes and oldest message age decreases
- Duplicate action attempts drop (reply/tag/assign)
- No new customer reports of repeated messages
- Safe mode can be disabled gradually (route-only first, automation later)


---

## Post-incident follow-ups
- Add or fix an alert: “duplicate action attempts” / “idempotency conflict rate”
- Update Richpanel automation ordering documentation if root cause is configuration
- Create a postmortem if SEV-1+ or if repeated


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard A — System Health (Wave 08)
- Security monitoring dashboards (Wave 06)

### Metrics to check
- `mw.ingress.requests_total`
- `mw.ingress.rejected_total`
- `mw.ingress.ack_latency_ms`
- `mw.worker.jobs_started_total`
- `mw.worker.jobs_failed_total`
- `mw.queue.depth`
- `mw.queue.oldest_age_s`
- `mw.queue.dlq_depth`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, ticket_id, mw_trace_id, idempotency_key, result, aws_request_id
| filter event like /ingress\./ or event like /worker\./
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- Set `safe_mode=true` if automation/routing loops are suspected.
- Set `automation_enabled=false` if duplicate replies are being sent.
- Reduce worker reserved concurrency (Wave 07 tuning) to slow amplification.

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- ST-060 (idempotency_duplicate_webhook)
- ST-070 (kill_switch_automation_disabled)


## Related docs
- [Kill switch and safe mode](../../06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md)
- [Idempotency, retry, dedup](../../03_Richpanel_Integration/Idempotency_Retry_Dedup.md)
- [Backlog catch-up and replay](../../07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md)

