# R004 — Vendor rate limit storm (Richpanel / OpenAI / Shopify)

Last updated: 2025-12-22  
Default severity: **SEV-1 (can be SEV-0 if causing wrong replies)**

---

## When to use this runbook
Use when:
- 429 responses spike from Richpanel/OpenAI/Shopify
- queue backlog grows because worker is throttled
- retry storms are suspected (increasing errors with no progress)


---

## Immediate actions (stop the bleeding)
1) Reduce outbound pressure
- lower worker concurrency
- increase backoff (if configurable)
- ensure we respect `Retry-After` where provided

2) Consider safe mode
- `safe_mode=true` to reduce action types and vendor calls

3) If automation contributes to call volume:
- `automation_enabled=false` temporarily

4) Confirm DLQ is not rapidly filling.


---

## Diagnosis steps
A) Identify which vendor is throttling
- Richpanel 429?
- OpenAI 429?
- Shopify 429?

B) Determine the cause
- legitimate volume spike?
- backlog catch-up draining too aggressively?
- bug causing repeated calls per ticket?
- missing caching for order lookups / tag IDs?

C) Confirm retry behavior
- exponential backoff with jitter
- max retries capped
- respects Retry-After


---

## Mitigation / repair actions
- Apply concurrency caps per vendor (token bucket approach)
- Add caching (tag id map, team map, order lookup) where safe
- Delay non-critical actions (analytics export, optional enrichments)
- If OpenAI is throttling:
  - consider smaller model or fewer calls per ticket
  - tighten prompt to reduce tokens


---

## Verify recovery
- 429 rate returns to baseline
- backlog begins to drain steadily (no oscillation)
- DLQ stops growing


---

## Post-incident follow-ups
- Add a “vendor 429 spike” alert if missing
- Update parameter defaults for concurrency and backoff
- Postmortem if SEV-1+


---


---

## Signals (dashboards, metrics, logs)

### Dashboards to check
- Dashboard B — Vendor Health (Wave 08)
- Dashboard A — System Health (Wave 08)

### Metrics to check
- `mw.vendor.openai.rate_limited_total`
- `mw.vendor.richpanel.rate_limited_total`
- `mw.vendor.shopify.errors_total`
- `mw.vendor.openai.latency_ms`
- `mw.vendor.richpanel.latency_ms`
- `mw.worker.end_to_end_latency_ms`
- `mw.queue.oldest_age_s`

### Log queries (CloudWatch Logs Insights)
```sql
fields ts, level, event, ticket_id, mw_trace_id,
       vendor.name, vendor.operation, vendor.http_status, vendor.rate_limit.retry_after_s, vendor.retry_count, vendor.error_code
| filter vendor.http_status = 429 or vendor.error_code = "rate_limited"
| sort ts desc
| limit 200
```

---

## Operator levers (safe actions)
- Reduce worker reserved concurrency (Wave 07 tuning) to lower QPS.
- Respect `Retry-After` and increase backoff/jitter (Wave 07).
- If needed: `safe_mode=true` or `automation_enabled=false` to reduce vendor calls.

---

## Smoke tests to validate the fix
Run the relevant cases from:
- `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`

Minimum set for this runbook:
- ST-070 (automation disabled) + confirm routing still works
- ST-071 (safe_mode route-only)


## Related docs
- [Rate limiting and backpressure](../../07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md)
- [Tuning playbook](../../07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md)
- [Service quotas and operational limits](../../07_Reliability_Scaling/Service_Quotas_and_Operational_Limits.md)

