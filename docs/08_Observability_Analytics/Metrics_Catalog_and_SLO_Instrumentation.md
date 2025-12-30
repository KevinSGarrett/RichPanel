# Metrics Catalog and SLO Instrumentation (Wave 08)

Last updated: 2025-12-22

This document defines the **metric taxonomy** for v1 and how those metrics support:
- SLO monitoring (Wave 07)
- alerting (Wave 06 + Wave 07)
- quality/drift detection (Wave 04 + Wave 08)

Key principle: **metrics must be low-cardinality and actionable**.  
Related cross-wave alignment map (Waves 06–08):
- `docs/08_Observability_Analytics/Cross_Wave_Alignment_Map.md`

High-cardinality breakdowns (per ticket/customer) belong in **logs** or exported analytics, not CloudWatch metrics.

---

## 1) Metric design rules (v1)

### Naming convention
`mw.<component>.<metric_name>`

Examples:
- `mw.ingress.requests_total`
- `mw.worker.end_to_end_latency_ms`
- `mw.vendor.openai.errors_total`
- `mw.policy.automation_blocked_total`

### Allowed dimensions (keep small)
Use dimensions sparingly to avoid cardinality explosions.

Recommended dimensions:
- `env` (dev/stage/prod)
- `channel` (livechat/email/<other>)
- `result` (success/failed/blocked)
- `vendor` (openai/richpanel/shopify)

Use only in **aggregate** (daily/weekly export), not per-request metrics:
- `template_id`
- `primary_intent`
- `department`

---

## 2) Core SLO metrics (required)

### Ingress SLOs (ACK-fast)
| Metric | Type | Unit | Notes |
|---|---|---:|---|
| `mw.ingress.requests_total` | Count | 1 | all inbound webhook hits |
| `mw.ingress.rejected_total` | Count | 1 | auth/schema rejected |
| `mw.ingress.ack_latency_ms` | Distribution | ms | p50/p95/p99 for request ACK |

### Pipeline SLOs (routing/automation latency)
| Metric | Type | Unit | Notes |
|---|---|---:|---|
| `mw.worker.jobs_started_total` | Count | 1 | worker starts |
| `mw.worker.jobs_succeeded_total` | Count | 1 | worker success |
| `mw.worker.jobs_failed_total` | Count | 1 | worker failure |
| `mw.worker.end_to_end_latency_ms` | Distribution | ms | ingest → decision → actions complete |

### Queue health
| Metric | Type | Unit | Notes |
|---|---|---:|---|
| `mw.queue.depth` | Gauge | 1 | SQS visible messages |
| `mw.queue.oldest_age_s` | Gauge | seconds | oldest message age (critical) |
| `mw.queue.dlq_depth` | Gauge | 1 | DLQ visible messages |

---

## 3) Vendor health metrics (required)

### OpenAI
| Metric | Type | Unit | Notes |
|---|---|---:|---|
| `mw.vendor.openai.requests_total` | Count | 1 | classification + verifier |
| `mw.vendor.openai.errors_total` | Count | 1 | includes schema/timeout |
| `mw.vendor.openai.latency_ms` | Distribution | ms | p50/p95/p99 |
| `mw.vendor.openai.rate_limited_total` | Count | 1 | 429s |

### Richpanel
| Metric | Type | Unit | Notes |
|---|---|---:|---|
| `mw.vendor.richpanel.requests_total` | Count | 1 | context fetch + tags + send msg + order |
| `mw.vendor.richpanel.errors_total` | Count | 1 | non-2xx |
| `mw.vendor.richpanel.latency_ms` | Distribution | ms | p50/p95/p99 |
| `mw.vendor.richpanel.rate_limited_total` | Count | 1 | 429s |

### Shopify (optional / only if used)
| Metric | Type | Unit |
|---|---|---:|
| `mw.vendor.shopify.requests_total` | Count | 1 |
| `mw.vendor.shopify.errors_total` | Count | 1 |
| `mw.vendor.shopify.latency_ms` | Distribution | ms |

---

## 4) Safety + policy metrics (required)

| Metric | Type | Unit | Notes |
|---|---|---:|---|
| `mw.policy.decisions_total` | Count | 1 | all decisions |
| `mw.policy.tier0_total` | Count | 1 | Tier 0 detected |
| `mw.policy.automation_attempt_total` | Count | 1 | attempted auto reply |
| `mw.policy.automation_blocked_total` | Count | 1 | blocked by policy |
| `mw.policy.safe_mode_total` | Count | 1 | decisions made while safe_mode=true |

**Reason breakdown:** use logs/exports for per-reason counts to avoid cardinality.

---

## 5) Automation impact metrics (recommended)

These metrics quantify “is this actually helping?”

| Metric | Type | Unit | Notes |
|---|---|---:|---|
| `mw.automation.reply_sent_total` | Count | 1 | successful auto replies |
| `mw.automation.reply_failed_total` | Count | 1 | failures |
| `mw.automation.route_only_total` | Count | 1 | route-only decisions |
| `mw.automation.deflection_proxy_total` | Count | 1 | optional proxy: auto reply + no agent reply within N minutes |

The deflection proxy is an **estimate**; true deflection measurement may require richer ticket lifecycle analytics (export pipeline).

---

## 6) Cost metrics (recommended)

| Metric | Type | Unit | Notes |
|---|---|---:|---|
| `mw.cost.tokens_in_total` | Count | 1 | aggregated (daily export preferred) |
| `mw.cost.tokens_out_total` | Count | 1 | aggregated |
| `mw.cost.usd_estimate` | Gauge | USD | computed from pricing config |

**Guardrail:** cost metrics are used for alarms (budget spikes) but must not include message content.

---

## 7) How metrics map to alarms
- Security-focused alarms are defined in: `docs/06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md`
- Reliability-focused triggers are defined in: `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`
- This file defines the canonical metrics those alarms should use.

---

## 8) Instrumentation approach (v1 recommended)
- Structured logs always
- Metrics emitted via EMF or a lightweight wrapper
- Traces optional (X-Ray / OpenTelemetry)

Implementation is tracked in build execution packs; this wave defines the contract.
