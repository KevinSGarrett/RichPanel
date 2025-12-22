# Logging, Metrics, and Tracing (Security-aware)

Last updated: 2025-12-22

This document defines observability requirements *with security constraints* (no PII leakage).
Detailed dashboards/analytics are expanded in Wave 08, but we must establish safe defaults here.

Related:
- Security monitoring baseline: `Security_Monitoring_Alarms_and_Dashboards.md`
- Incident response: `Incident_Response_Security_Runbooks.md`


---

## 1) Logging principles (required)
- **No raw PII** in logs (redact before writing)
- **No secrets** in logs (headers, tokens)
- Prefer structured JSON logs for filtering
- Include correlation IDs to support incident response

---

## 2) Required log fields (v1)
| Field | Example | Notes |
|---|---|---|
| `request_id` | AWS request id | for tracing |
| `ticket_id` | `rp_...` | L2 identifier; ok |
| `event_id` / `idempotency_key` | hash | supports dedup |
| `decision.intent` | `order_status_tracking` | safe |
| `decision.template_id` | `order_status_tracking_verified` | safe |
| `decision.department` | `Returns Admin` | safe |
| `decision.confidence` | 0.92 | safe |
| `latency_ms` | 1800 | safe |
| `vendor.error_code` | 429 | safe |
| `safe_mode` | true/false | safe |

Optional: `redacted_message_preview` (dev/staging only; <=200 chars).

---

## 3) Metrics (v1 minimum)
### Reliability metrics
- ingress requests / min
- enqueue success rate
- worker success rate
- queue depth + age of oldest message
- vendor call rates + error rates (OpenAI/Richpanel/Shopify)
- p50/p95/p99 latency (route + auto-reply)

### Safety metrics
- Tier 0 detections per day
- automation send rate per template_id
- “safe mode enabled” time
- suspicious auth failures (401/403 spikes)

---

## 4) Alerts (security-focused)
- spike in 401/403 at webhook endpoint
- spike in auto-replies per minute
- sudden increase in a template_id (possible misclassification)
- OpenAI/Richpanel 429 storm
- DLQ growth

---

## 5) Tracing
Optional in v1:
- AWS X-Ray for ingress → worker correlation
- ensure trace metadata does not include PII

---

## 6) Log retention and access
See: `Data_Retention_and_Access.md` and `PII_Handling_and_Redaction.md`.