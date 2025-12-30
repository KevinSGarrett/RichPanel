# Wave 07 Definition of Done Checklist

Last updated: 2025-12-22  
Status: **Complete ✅ (Wave 07 closeout)**

Wave 07 is “done” when reliability and scaling decisions are **specific enough to implement** and **testable**.

---

## A) Capacity and SLOs
- [x] SLOs documented (ACK latency, routing latency, queue age)
- [x] Current observed volume summarized (7-day heatmap)
- [x] Surge factor assumptions documented (10× peak)

## B) Concurrency and throughput
- [x] Worker reserved concurrency default documented (`parameter_defaults_v1.yaml`)
- [x] How we tune concurrency documented (`Tuning_Playbook_and_Degraded_Modes.md`)
- [x] Backpressure strategy documented (429 handling, retries, DLQ)

## C) Queueing and idempotency
- [x] SQS FIFO strategy documented (group id, dedup id, visibility timeout)
- [x] DLQ configuration documented (max receives, alarms)
- [x] Idempotency design referenced and aligned (Wave 02 schema)

## D) Resilience and degradation
- [x] Timeouts per downstream documented (OpenAI/Richpanel/Shopify)
- [x] Degraded mode behavior documented (route-only, disable automation)
- [x] Kill switch documented (Wave 06) and referenced

## E) Load testing
- [x] Load profiles defined (baseline, peak, surge, spike, soak)
- [x] Failure injection tests defined (OpenAI degraded, Richpanel 429, Shopify unavailable)
- [x] Pass/fail criteria defined (unsafe auto-reply = hard fail)

## F) Cost controls
- [x] Budget + alert plan documented (AWS + OpenAI usage)
- [x] Token usage metrics defined (tokens/message p95)
- [x] Logging retention controls documented

## G) DR + operational limits
- [x] DR posture documented (single region, multi-AZ)
- [x] Service quota checklist documented

---

## Closeout verification
- [x] Parameter defaults finalized and committed
- [x] Backlog catch-up + replay strategy documented
- [x] Wave 07 marked complete in `docs/00_Project_Admin/Progress_Wave_Schedule.md`
- [x] Wave 07 notes updated
