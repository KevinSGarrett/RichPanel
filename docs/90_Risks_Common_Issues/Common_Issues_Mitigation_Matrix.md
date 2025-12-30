# Common Issues Mitigation Matrix

Last updated: 2025-12-21

This matrix maps each item from `CommonIssues.zip` to:
- where it is handled in the architecture/design
- required controls
- testing/monitoring signals

We will expand this throughout Waves 03–10.

---

## Matrix (v0.2)

| Common issue file | Risk theme | Planned controls (summary) | Primary documentation home |
|---|---|---|---|
| 01-automation-loops.md | Automation loops | inbound-only triggers; processed tag/field; prevent self-trigger; loop alerts | `03_Richpanel_Integration/*` + Wave 10 runbooks |
| 02-webhook-spoofing.md | Spoofing | shared secret/signature verification; replay protection; rate limits | Wave 06 security + `03_Richpanel_Integration/Webhooks_and_Event_Handling.md` |
| 03-idempotency-duplicate-events.md | Duplicate processing | idempotency keys; dedup store; safe retries; action-level idempotency | `03_Richpanel_Integration/Idempotency_Retry_Dedup.md` |
| 04-webhook-timeouts-ack-fast.md | Timeouts | ACK fast; async queue; never block on LLM/API | `03_Richpanel_Integration/Webhooks_and_Event_Handling.md` |
| 05-rate-limits.md | Rate limits | backoff+jitter; queueing; caching; concurrency controls | Wave 07 scaling + `06_Security_Privacy_Compliance/Logging_Metrics_Tracing.md` |
| 06-ticket-state-conflicts.md | State conflicts | minimal updates; agent override rules; compare-and-set when possible | Wave 03 integration + Wave 10 ops |
| 07-team-mapping-drift.md | Drift | central mapping config; audits; mapping versioning | `03_Richpanel_Integration/Team_Tag_Mapping_and_Drift.md` + Wave 11 |
| 08-confidence-score-calibration.md | Calibration | offline eval; threshold tuning; calibration curves | `04_LLM_Design_Evaluation/Confidence_Scoring_and_Thresholds.md` + Wave 11 |
| 09-llm-classification-failures.md | LLM failures | structured outputs; fallbacks; multi-intent handling; safe default routing | Wave 04 + Wave 09 tests |
| 10-order-status-pitfalls.md | Privacy leaks | deterministic order match; minimal disclosure; safe fallback ask-for-info | `01_Product_Scope_Requirements/FAQ_Automation_Scope.md` + Wave 05 |
| 11-practical-dev-checklist.md | Implementation gaps | checklist for payloads, retries, logs, alerts, rollbacks | Wave 10 runbooks + Wave 12 tickets |
| 12-http-target-no-retry.md | No retries | treat failures as final; persist events; internal retry + sweeper | Wave 03 + Wave 10 |
| 13-missing-identifiers-in-payload.md | Missing IDs | versioned payload contract; include conversation_id + message_id + channel | `03_Richpanel_Integration/Webhooks_and_Event_Handling.md` |
| 14-pagination-mistakes.md | Pagination bugs | shared pagination helper; contract tests; limits | Wave 03 API contract + Wave 09 tests |
| 15-attachments-non-text-payload-too-large.md | Attachments | size limits; skip/route; summarize only when safe | `03_Richpanel_Integration/Attachments_Playbook.md` |
| 16-richpanel-api-error-handling.md | API errors | robust retries; classify errors; circuit breaker; observability | `03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md` |
| 17-attachment-inline-base64.md | Large payloads | never send inline base64 to LLM; fetch via URL; enforce limits | `03_Richpanel_Integration/Attachments_Playbook.md` |
| 18-too-much-context-overflow.md | Context overflow | context windowing; summarization; truncation policy | Wave 04 LLM design + Wave 07 scaling |
| 19-attachment-bursts-rate-limits.md | Bursts | per-ticket attachment queue; concurrency caps; backpressure | Wave 07 scaling |
| 20-attachment-fetch-failures.md | Fetch failures | retry fetch; fallback to agent; tag for visibility | `03_Richpanel_Integration/Attachments_Playbook.md` + Wave 10 |
| 21-non-text-only-zero-intent.md | Zero-intent | safe fallback; ask clarifying; route to default | Wave 04 + Wave 05 |
| 22-simple-attachment-playbook.md | Attachments | standard workflow for images/PDFs; safe summary | `03_Richpanel_Integration/Attachments_Playbook.md` |

