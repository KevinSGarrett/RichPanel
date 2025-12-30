# EP03 — Middleware core pipeline

Last updated: 2025-12-23

## Purpose

Build the serverless middleware pipeline with durability (SQS), idempotency (DynamoDB), and safe degraded modes.


## Ticket list

- [W12-EP03-T030 — Implement API Gateway + ingress Lambda (fast ACK, validation, enqueue)](../03_Tickets/W12-EP03-T030_Implement_API_Gateway_ingress_Lambda_fast_ACK_validation_enqueue.md)
- [W12-EP03-T031 — Provision SQS FIFO + DLQ and internal message schema (conversation-ordered processing)](../03_Tickets/W12-EP03-T031_Provision_SQS_FIFO_DLQ_and_internal_message_schema_conversation_ordered_processi.md)
- [W12-EP03-T032 — Create DynamoDB tables for idempotency + minimal conversation state with TTL](../03_Tickets/W12-EP03-T032_Create_DynamoDB_tables_for_idempotency_minimal_conversation_state_with_TTL.md)
- [W12-EP03-T033 — Implement worker Lambda skeleton (dequeue, fetch context, decision pipeline placeholder, action stub)](../03_Tickets/W12-EP03-T033_Implement_worker_Lambda_skeleton_dequeue_fetch_context_decision_pipeline_placeho.md)
- [W12-EP03-T034 — Implement runtime feature flags (safe_mode, automation_enabled, per-template toggles) with caching](../03_Tickets/W12-EP03-T034_Implement_runtime_feature_flags_safe_mode_automation_enabled_per_template_toggle.md)
- [W12-EP03-T035 — Implement observability event logging + correlation IDs (ingress and worker)](../03_Tickets/W12-EP03-T035_Implement_observability_event_logging_correlation_IDs_ingress_and_worker.md)
- [W12-EP03-T036 — Implement vendor retry/backoff utilities and concurrency bounds (prevent rate-limit storms)](../03_Tickets/W12-EP03-T036_Implement_vendor_retry_backoff_utilities_and_concurrency_bounds_prevent_rate_lim.md)


## Dependencies

- EP02 required.
- EP04/EP06 depend on EP03.
