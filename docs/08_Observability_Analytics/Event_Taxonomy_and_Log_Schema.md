# Event Taxonomy and Log Schema (Wave 08)

Last updated: 2025-12-22

This document defines the **canonical event taxonomy** and **structured log schema** for the middleware.

Goals:
- make investigations fast (single ticket timeline)
- support dashboards and quality monitoring
- keep logs **PII-safe by default**

Security constraints:
- Never log raw message bodies or attachments in production.
- Never log webhook secrets, API keys, or auth headers.
- Follow: `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`

---

## 1) Canonical event naming

### Naming rules
- Use **dot-separated** names: `stage.action.outcome`
- Stage is one of: `ingress`, `worker`, `policy`, `action`, `vendor`, `eval`, `system`
- Outcomes are explicit: `success`, `blocked`, `skipped`, `failed`, `retry`, `timeout`

### Required event set (v1)

#### Ingress (webhook ingestion)
- `ingress.request.received`
- `ingress.request.rejected` (auth/schema)
- `ingress.enqueue.success`
- `ingress.enqueue.failed`

#### Worker lifecycle
- `worker.job.start`
- `worker.context.fetch.success`
- `worker.context.fetch.failed`
- `worker.job.complete`
- `worker.job.failed`

#### LLM + policy
- `vendor.openai.classify.success`
- `vendor.openai.classify.failed`
- `policy.decision.made` (always emitted)
- `policy.automation.blocked` (Tier 0 / no deterministic match / verifier failed)

#### Order lookup (deterministic match)
- `vendor.richpanel.order_link.lookup.success`
- `vendor.richpanel.order_link.lookup.empty`
- `vendor.richpanel.order.fetch.success`
- `vendor.richpanel.order.fetch.failed`

#### Richpanel actions
- `vendor.richpanel.tags.add.success`
- `vendor.richpanel.tags.add.failed`
- `vendor.richpanel.message.send.success`
- `vendor.richpanel.message.send.failed`

#### System safeguards
- `system.safe_mode.enabled`
- `system.automation.disabled`
- `system.idempotency.duplicate_event_detected`
- `system.dlq.message_written`

---

## 2) Structured log envelope (required fields)

All events must include this envelope.

| Field | Type | Example | Notes |
|---|---|---|---|
| `ts` | string (ISO8601) | `2025-12-22T14:05:11Z` | event time |
| `level` | string | `INFO` | `DEBUG/INFO/WARN/ERROR` |
| `event` | string | `policy.decision.made` | canonical event name |
| `mw_trace_id` | string | `trc_<TRACE_ID>` | generated at ingress; carried end-to-end |
| `mw_release` | string | `mw-2025.12.22.1` | code release identifier |
| `env` | string | `dev/stage/prod` | environment |
| `ticket_id` | string | `rp_ticket_<TICKET_ID>` | Richpanel ticket/conversation id |
| `channel` | string | `livechat` | normalized channel |
| `idempotency_key` | string | `evt_<EVENT_ID>` | used for dedup |
| `step` | string | `ingress/worker/policy/action` | stage label |
| `latency_ms` | number | 1830 | optional; event-specific |
| `result` | string | `success/failed/blocked/skipped` | required for action/vendor events |

### Recommended additional envelope fields
| Field | Type | Example | Notes |
|---|---|---|---|
| `account` | string | `prod` | AWS account nickname |
| `aws_request_id` | string | `<VALUE>` | for Lambda correlation |
| `sqs_message_id` | string | `<VALUE>` | when worker processes queue |
| `customer_id_hash` | string | `h_<HASH>` | hashed; optional |
| `order_id_hash` | string | `h_<HASH>` | hashed; optional |

---

## 3) Decision payload (policy.decision.made)

This event is the “truth record” for what we decided.

Required fields (in `decision.*`):
| Field | Example |
|---|---|
| `decision.primary_intent` | `order_status_tracking` |
| `decision.secondary_intents` | `["returns_policy"]` |
| `decision.department` | `Email Support Team` |
| `decision.tier` | `0/1/2` |
| `decision.template_id` | `order_status_tracking_verified` |
| `decision.confidence` | `0.91` |
| `decision.action` | `route_only` / `send_reply` |
| `decision.reason_codes` | `["tier2_verified"]` |

### Reason code conventions
Reason codes must be short and enumerable. Examples:
- `tier0_always_handoff`
- `tier1_safe_assist`
- `tier2_verified`
- `tier2_missing_deterministic_match`
- `tier2_verifier_failed`
- `safe_mode_route_only`
- `automation_disabled`
- `schema_invalid_fail_closed`
- `vendor_error_fail_closed`

---

## 4) Vendor call schema (vendor.* events)

Required fields:
| Field | Example |
|---|---|
| `vendor.name` | `openai` / `richpanel` / `shopify` |
| `vendor.operation` | `classify` / `add_tags` / `send_message` / `get_order` |
| `vendor.http_status` | 200 / 429 / 500 |
| `vendor.latency_ms` | 812 |
| `vendor.retry_count` | 1 |
| `vendor.rate_limit.retry_after_s` | 10 |
| `vendor.error_code` | `rate_limited` |
| `vendor.error_class` | `TimeoutError` |

**Important:** vendor payloads must not include raw PII or full request bodies.

---

## 5) PII-safe logging rules (hard requirements)

### Never log
- raw message text or attachments (prod)
- emails, phone numbers, addresses
- tracking URLs
- webhook tokens, `x-richpanel-key`, OpenAI keys

### Allowed to log (safe metadata)
- message length (chars)
- language (if computed locally)
- hashed identifiers (salted)
- template IDs, intent labels, confidence
- HTTP status codes, latency, retry counts

### Hashing guidance
If you need joinable identifiers (for analytics):
- use a **salted hash** that is unique per environment
- do not reuse prod salt in non-prod
- keep salts in Secrets Manager

---

## 6) Example events (sanitized)

### Example: policy decision (send reply)
```json
{
  "ts": "2025-12-22T14:05:11Z",
  "level": "INFO",
  "event": "policy.decision.made",
  "mw_trace_id": "trc_<TRACE_ULID>",
  "mw_release": "mw-2025.12.22.1",
  "env": "prod",
  "ticket_id": "rp_123456",
  "channel": "livechat",
  "idempotency_key": "evt_abc",
  "step": "policy",
  "decision": {
    "primary_intent": "order_status_tracking",
    "secondary_intents": [],
    "department": "Email Support Team",
    "tier": 2,
    "template_id": "order_status_tracking_verified",
    "confidence": 0.93,
    "action": "send_reply",
    "reason_codes": ["tier2_verified"]
  }
}
```

### Example: automation blocked due to missing deterministic match
```json
{
  "ts": "2025-12-22T14:05:11Z",
  "level": "INFO",
  "event": "policy.automation.blocked",
  "mw_trace_id": "trc_<TRACE_ULID>",
  "mw_release": "mw-2025.12.22.1",
  "env": "prod",
  "ticket_id": "rp_123456",
  "channel": "email",
  "idempotency_key": "evt_abc",
  "step": "policy",
  "result": "blocked",
  "reason": "tier2_missing_deterministic_match"
}
```

---

## 7) Canonical taxonomy file

The v1 taxonomy of events is tracked in:
- `observability_event_taxonomy_v1.yaml`

This file is used as a reference for:
- instrumentation implementation
- dashboards/alerts mapping
- validation during code review

---

## 8) Implementation notes (non-binding)
Recommended libraries (choose one stack, don’t mix):
- AWS Lambda Powertools (Python/Node) for structured logs + metrics
- AWS X-Ray or OpenTelemetry for tracing
