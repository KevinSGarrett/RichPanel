# Order Status Monitoring (MVP)

## Dashboard

- **CloudWatch Dashboard:** `rp-mw-<env>-order-status`
- Primary log group: `/aws/lambda/rp-mw-<env>-worker`

---

## Alarms (minimum)

**Log fields used by metric filters:**

- `richpanel.rate_limited status=429`
- `shopify.rate_limited status=429`
- `order_status_intent.request_failed`

### 1) Worker Lambda error rate

- **Metric:** `Errors / Invocations`
- **Window:** 15 minutes
- **Threshold:** > 5%
- **Purpose:** detect 5xx/unhandled failures in the worker
- **Alarm name:** `rp-mw-<env>-worker-error-rate`

### 2) Shopify token refresh Lambda errors

- **Metric:** `Errors`
- **Window:** 1 hour
- **Threshold:** > 0
- **Purpose:** refresh failures can invalidate Shopify access tokens
- **Alarm name:** `rp-mw-<env>-shopify-refresh-errors`

### 2b) Shopify token health check (scheduled)

- **Monitor:** GitHub Action `Shopify Token Health Check` (`.github/workflows/shopify_token_health_check.yml`)
- **Schedule:** cron (daily) + manual `workflow_dispatch`
- **Purpose:** detect 401/403 on the read-only token without waiting 48 hours
- **Artifact:** `artifacts/shopify/shopify_health_check.json`

### 3) Richpanel 429 spikes

- **Metric filter:** `richpanel.rate_limited status=429`
- **Window:** 15 minutes
- **Threshold:** >= 5 events
- **Purpose:** detect upstream rate-limit spikes
- **Alarm name:** `rp-mw-<env>-richpanel-429-spike`

### 4) Shopify 429 spikes

- **Metric filter:** `shopify.rate_limited status=429`
- **Window:** 15 minutes
- **Threshold:** >= 5 events
- **Purpose:** detect upstream rate-limit spikes
- **Alarm name:** `rp-mw-<env>-shopify-429-spike`

### 5) OpenAI intent failures

- **Metric filter:** `order_status_intent.request_failed`
- **Window:** 5 minutes
- **Threshold:** > 0
- **Purpose:** detect OpenAI request failures affecting order status routing
- **Alarm name:** `rp-mw-<env>-openai-intent-failures`

---

## Order-status anomaly (placeholder)

We will alert when **order_status_true rate** drops below 15% for N samples **once a scheduled shadow job exists**.

**TODO:** Wire a scheduled shadow job to emit a metric (e.g., `OrderStatusTrueRatePct`) and add a CloudWatch alarm:

- **Threshold:** < 15%
- **Samples:** N (e.g., 50+)

---

## Where to find alarms

- **CloudWatch Alarms:** search by `rp-mw-<env>` or `OrderStatus`
