# Tracing and Correlation IDs (Wave 08)

Last updated: 2025-12-22

This document defines how we correlate:
- ingress → queue → worker processing
- downstream vendor calls (OpenAI, Richpanel, Shopify)
- policy decisions and actions

Tracing is optional in v1, but correlation IDs are required.

---

## 1) Required correlation identifiers (v1)

### `mw_trace_id` (required)
- Generated at ingress for every webhook
- Carried through queue and all worker logs
- Appears in every structured event log and major metric events (where feasible)

Format suggestion:
- `trc_<ulid>` or `trc_<uuidv7>` (monotonic + sortable is helpful)

### `idempotency_key` (required)
- Event-level dedup key (ingress delivery id if available; otherwise hash of ticket_id + message_id + timestamp)
- Used to prevent duplicate effects
- Logged on all major events

### `ticket_id` (required)
- Richpanel ticket/conversation id (string)
- Used for timeline reconstruction and linking to the support tool

### `mw_release` / `prompt_version` / `template_version` (required)
- Enables “what changed?” investigations:
  - Was it a code change?
  - A prompt change?
  - A template copy change?

---

## 2) Propagation plan across components

### Ingress → SQS
The ingress Lambda must:
- generate `mw_trace_id` if not present
- attach it to the SQS message body and/or message attributes
- include `idempotency_key`

### Worker
The worker Lambda must:
- read `mw_trace_id` and re-use it for all logs/metrics in that execution
- include it in downstream call logs

---

## 3) Tracing options

### Option A (v1 recommended if available): AWS X-Ray
Pros:
- native AWS integration for Lambda/API Gateway
- simple service map
- good enough for request latency debugging

Cons:
- limited for deep vendor instrumentation unless we add custom subsegments

**PII rule:** never add message text to X-Ray annotations.

### Option B: OpenTelemetry (OTel)
Pros:
- vendor-neutral
- richer spans for OpenAI/Richpanel/Shopify calls

Cons:
- more configuration overhead

---

## 4) What to trace (minimum useful spans)
If tracing is enabled, capture spans for:
- `ingress.validate`
- `ingress.enqueue`
- `worker.fetch_context`
- `worker.classify`
- `worker.policy_decide`
- `worker.order_lookup`
- `worker.apply_tags`
- `worker.send_message`

Each span should record **safe attributes** only:
- status code
- latency
- retry count
- template_id (optional)
- tier/action (safe)

---

## 5) Correlation for human investigations (support + engineering)
When investigating a ticket:
1) Use `ticket_id` to find events in logs.
2) Use `mw_trace_id` to reconstruct the end-to-end chain across ingress/worker.
3) Check `mw_release` and `prompt_version` to see what changed.
4) Use the decision event (`policy.decision.made`) as the authoritative summary.

---

## 6) Related docs
- Event schema: `Event_Taxonomy_and_Log_Schema.md`
- Security constraints: `docs/06_Security_Privacy_Compliance/Logging_Metrics_Tracing.md`
- Reliability tuning: `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`
