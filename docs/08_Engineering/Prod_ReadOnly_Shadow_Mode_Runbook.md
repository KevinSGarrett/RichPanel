# Production Read-Only Shadow Mode Runbook

Last updated: 2026-01-17  
Status: Canonical

## Goal

Validate production data shapes and integration behavior **without any writes or customer contact**. This mode allows you to run the middleware against real production traffic to verify:

- Data structures returned by Richpanel, Shopify, and other integrations
- Routing/classification accuracy
- Order lookup behavior
- Template rendering logic

...while guaranteeing **zero writes** to any external system and **zero outbound communications** to customers.

---

## Required configuration

To enable production read-only shadow mode, you must configure both **runtime kill switches (SSM)** and **Lambda environment variables**:

### Environment contract (explicit)

Use these exact env var settings depending on mode.

#### Live read-only shadow runs (production data, no writes)
- `RICHPANEL_ENV=prod`
- `RICHPANEL_READ_ONLY=true`
- `RICHPANEL_WRITE_DISABLED=true`
- `RICHPANEL_OUTBOUND_ENABLED=false`
- `MW_OUTBOUND_ENABLED=false`

#### Go-live (intentional outbound)
- `RICHPANEL_READ_ONLY=false`
- `RICHPANEL_OUTBOUND_ENABLED=true`
- `MW_OUTBOUND_ENABLED=true`
- `MW_PROD_WRITES_ACK=I_UNDERSTAND_PROD_WRITES` (prod only; explicit two-man acknowledgment)
- Checklist: [ ] Explicitly confirm "We are now live" (record in Progress Log)

### Production write acknowledgment (two-man rule)

To prevent accidental live-customer contact (see B54/B58), production writes
require a **second explicit acknowledgment** in addition to the existing
kill-switches. This fails closed even if other env vars are misconfigured.

**Requirement (prod only):**
- `MW_PROD_WRITES_ACK=I_UNDERSTAND_PROD_WRITES` (preferred) or `MW_PROD_WRITES_ACK=true`

**Interlocks (all must allow):**
- `safe_mode=false` and `automation_enabled=true` (SSM parameters)
- `RICHPANEL_OUTBOUND_ENABLED=true` (outbound communications)
- `RICHPANEL_WRITE_DISABLED=false` (no write lock)

**Environment resolution:** prod is detected via `RICHPANEL_ENV` → `RICH_PANEL_ENV`
→ `MW_ENV` → `ENV` → `ENVIRONMENT` (lowercased).

### Runtime kill switches (safe_mode + automation_enabled)

The worker reads `safe_mode` and `automation_enabled` from **SSM Parameter Store** (not direct Lambda env vars).

**Preferred method (all environments):** Use the `set-runtime-flags.yml` workflow to update SSM parameters:

```powershell
# Set SSM parameters for shadow mode
gh workflow run set-runtime-flags.yml `
  --ref main `
  -f environment=<dev|staging|prod> `
  -f safe_mode=true `
  -f automation_enabled=false
```

**DEV-only fallback (env override):** For rapid iteration in DEV, you can override SSM values with Lambda env vars (requires BOTH override vars):

```bash
MW_ALLOW_ENV_FLAG_OVERRIDE=true
MW_SAFE_MODE_OVERRIDE=true
MW_AUTOMATION_ENABLED_OVERRIDE=false
```

**Note:** If `MW_ALLOW_ENV_FLAG_OVERRIDE=true` but either override var is missing, the override does NOT apply (system fails closed to SSM values).

### Lambda environment variables

Set these on the worker Lambda directly (AWS Console, CDK, or workflow):

```bash
# Allow network reads for Richpanel/Shopify/ShipStation APIs
MW_ALLOW_NETWORK_READS=true

# Block ALL writes to Richpanel (tags, comments, status updates, routing)
RICHPANEL_WRITE_DISABLED=true

# Block ALL writes to Shopify (optional but recommended for full read-only guarantee)
SHOPIFY_WRITE_DISABLED=true

# Explicit production write acknowledgment (required for prod writes)
MW_PROD_WRITES_ACK=I_UNDERSTAND_PROD_WRITES

# Disable ALL outbound communications (email, SMS, push notifications)
RICHPANEL_OUTBOUND_ENABLED=false
```

### Verification checklist

Before enabling shadow mode in production:

- [ ] Confirm SSM parameters are set: `safe_mode=true`, `automation_enabled=false` (via workflow or SSM console)
- [ ] Confirm Lambda env vars are set: `MW_ALLOW_NETWORK_READS=true`, `RICHPANEL_WRITE_DISABLED=true`, `RICHPANEL_OUTBOUND_ENABLED=false`
- [ ] (Optional) Confirm `SHOPIFY_WRITE_DISABLED=true` is set
- [ ] For go-live in prod, confirm `MW_PROD_WRITES_ACK=I_UNDERSTAND_PROD_WRITES` is set
- [ ] Review CloudWatch logs to confirm no write operations are attempted
- [ ] Run the "Prove zero writes" audit (see below)

### Multi-account + secrets preflight (required)
Run the preflight before any prod shadow run to guarantee you are in the correct
AWS account and region and can read the required secrets/SSM kill switches:

```bash
python scripts/secrets_preflight.py --env prod --region us-east-2 --out artifacts/preflight_prod.json
```

If the preflight fails with `AccessDenied`, update the IAM policy for the role
used by Cursor/GitHub OIDC (typically `arn:aws:iam::<account_id>:role/rp-ci-deploy`)
to allow `secretsmanager:DescribeSecret`, `secretsmanager:GetSecretValue`, and
`ssm:DescribeParameters` on the required paths.

**Important:** The preflight only checks **existence/readability** of secrets and
SSM parameters. It does **not** validate external API tokens (no HTTP 200 probe).

### Live read-only shadow eval script (local)

- Script: `scripts/live_readonly_shadow_eval.py`
- Preferred execution: workflow dispatch `shadow_live_readonly_eval.yml` (uses GH secrets; no local prod secrets)
- Required secrets (AWS Secrets Manager):
  - `rp-mw/prod/richpanel/api_key`
  - `rp-mw/prod/shopify/admin_api_token` (canonical; legacy fallback: `rp-mw/prod/shopify/access_token`)
  - If prod uses the same Shopify store as dev (single-store setup), keep the prod secret
    aligned to the dev token so `--env prod` reads succeed.
- Required env vars (the script enforces/fails-closed):
  - `RICHPANEL_ENV=prod` (or `ENVIRONMENT=prod`)
  - `MW_ALLOW_NETWORK_READS=true`
  - `RICHPANEL_READ_ONLY=true`
  - `RICHPANEL_WRITE_DISABLED=true`
- `RICHPANEL_OUTBOUND_ENABLED=false` (required; outbound must stay off)
- Optional overrides:
  - `RICHPANEL_API_KEY_OVERRIDE` (set to `PROD_RICHPANEL_API_KEY` for prod runs)
  - `SHOPIFY_SHOP_DOMAIN` (or `--shop-domain` flag) to target the correct store
  - `RICHPANEL_API_KEY_SECRET_ID` can be overridden with `--richpanel-secret-id`
- Run locally (PowerShell example, requires AWS creds with secrets access):

```powershell
$env:RICHPANEL_API_KEY_OVERRIDE = $env:PROD_RICHPANEL_API_KEY
$env:MW_ALLOW_NETWORK_READS = "true"
$env:RICHPANEL_OUTBOUND_ENABLED = "false"
$env:RICHPANEL_READ_ONLY = "true"
$env:RICHPANEL_WRITE_DISABLED = "true"

python scripts/live_readonly_shadow_eval.py `
  --max-tickets 10 `
  --richpanel-secret-id rp-mw/prod/richpanel/api_key `
  --shop-domain <myshop.myshopify.com>
```

### Validate Shopify token (read-only)
Use the probe to confirm the token + shop domain combination works (GET-only):

```powershell
$env:RICHPANEL_ENV = "prod"
$env:MW_ALLOW_NETWORK_READS = "true"
$env:RICHPANEL_READ_ONLY = "true"
$env:RICHPANEL_WRITE_DISABLED = "true"
$env:RICHPANEL_OUTBOUND_ENABLED = "false"
$env:SHOPIFY_OUTBOUND_ENABLED = "true"
$env:SHOPIFY_WRITE_DISABLED = "true"
$env:SHOPIFY_SHOP_DOMAIN = "<shop>.myshopify.com"

python scripts/live_readonly_shadow_eval.py `
  --ticket-id <ticket-or-conversation-id> `
  --shop-domain <shop>.myshopify.com `
  --shopify-probe
```

**Expected:** `shopify_probe.ok=true` and `status_code=200` in the JSON/MD report.

What it does:
- Requires the read-only env flags above (fails closed if missing or incorrect)
- Reads ticket + conversation, performs order lookup (Shopify fallback) with `allow_network` gated to reads only
- Builds a dry-run action plan without sending messages, tagging, or closing tickets
- Writes a PII-safe JSON report to `artifacts/readonly_shadow/live_readonly_shadow_eval_report_<RUN_ID>.json`
  (or `live_shadow_report.json` when `--out` is used)
- Writes a PII-safe markdown report to `artifacts/readonly_shadow/live_readonly_shadow_eval_report_<RUN_ID>.md`
  (or `live_shadow_summary.md` when `--summary-md-out` is used)
- Captures a redacted HTTP trace to `artifacts/readonly_shadow/live_readonly_shadow_eval_http_trace_<RUN_ID>.json`
  (or `live_shadow_http_trace.json` when `--out` is used) and fails if any non-GET calls are observed

### Daily live read-only shadow eval (CI)
- Workflow: `Shadow Live Read-Only Eval` (`.github/workflows/shadow_live_readonly_eval.yml`)
- Schedule: daily at **03:00 UTC** (plus manual `workflow_dispatch`)
- Scheduled runs require `PROD_SHOPIFY_SHOP_DOMAIN` (repo secret) for `SHOPIFY_SHOP_DOMAIN`
- Optional: `PROD_RICHPANEL_TICKET_IDS` (comma-separated) to bypass 403 list endpoints
- Optional input: `shopify-token-source=api` to force `PROD_SHOPIFY_API_TOKEN` when the admin token is stale
- Artifact location: GitHub Actions run → `live-readonly-shadow-eval` artifact
- Artifact contents (PII-safe):
  - `artifacts/readonly_shadow/live_shadow_report.json`
  - `artifacts/readonly_shadow/live_shadow_summary.json`
  - `artifacts/readonly_shadow/live_shadow_http_trace.json`
  - `artifacts/readonly_shadow/live_shadow_summary.md`
- Summary highlights (machine-readable): match success rate, tracking/ETA availability rate, match failure buckets, channel counts, timing stats, top failure reasons, fetch failure counts, schema drift
- Note: local runs without `--out` continue to write `live_readonly_shadow_eval_report_<RUN_ID>.json` and related legacy filenames.
- Drift threshold: **warning** when >20% of samples have a new schema fingerprint (ticket snapshot or Shopify summary)

### Prod shadow order status report (scaled)

- Script: `scripts/prod_shadow_order_status_report.py`
- Required env flags (fail-closed if missing):
  - `RICHPANEL_ENV=prod` (or `ENVIRONMENT=prod`)
  - `MW_ALLOW_NETWORK_READS=true`
  - `RICHPANEL_READ_ONLY=true`
  - `RICHPANEL_WRITE_DISABLED=true`
  - `RICHPANEL_OUTBOUND_ENABLED=false`
  - `SHOPIFY_OUTBOUND_ENABLED=true`
  - `SHOPIFY_WRITE_DISABLED=true`
  - `MW_OPENAI_ROUTING_ENABLED=true`
  - `MW_OPENAI_INTENT_ENABLED=true`
  - `MW_OPENAI_SHADOW_ENABLED=true`
- Sample size: use `--sample-size <N>` or `--max-tickets <N>` (not both). For scaled runs, target 250–500 and enable throttling:
  - `--batch-size <N>` + `--batch-delay-seconds <N>` to reduce bursts
  - `--throttle-seconds <N>` between ticket fetches
  - Optional: `RICHPANEL_RATE_LIMIT_RPS=<N>` for client-side rate limiting
- Diagnostics for 429/retry: add `--retry-diagnostics --request-trace` (optional `--retry-proof-path <path>`).
- Required artifacts to commit:
  - `REHYDRATION_PACK/RUNS/<RUN_ID>/C/PROOF/prod_shadow_order_status_report.json`
  - `REHYDRATION_PACK/RUNS/<RUN_ID>/C/PROOF/prod_shadow_order_status_report.md`

#### B61/C: Enhanced Diagnostic Metrics

The shadow eval report now includes **diagnostic and actionable metrics** to help identify drift and performance issues:

**Route Decision Distribution:**
- Tracks how tickets are classified: `order_status`, `non_order_status`, or `unknown`
- Helps identify if fewer tickets are being classified as order status inquiries
- Location: `route_decisions` and `route_decision_percentages` in summary JSON

**Match Method Telemetry:**
- Tracks which matching strategy succeeded for each order lookup:
  - `order_number`: Matched via order number from ticket
  - `name_email`: Matched via customer name + email
  - `email_only`: Matched via email only (single or most recent)
  - `none`: No match found
  - `parse_error`: Match failed due to parsing issues
- Helps identify if a specific match method is degrading
- Location: `match_methods` and `match_method_percentages` in summary JSON

**Failure Reason Buckets (PII-safe):**
- Categorizes failures into stable buckets:
  - `no_identifiers`: Missing customer email or order identifiers
  - `shopify_api_error`: Shopify API failures (timeouts, 5xx, etc.)
  - `richpanel_api_error`: Richpanel API failures
  - `ambiguous_match`: Multiple orders matched, unable to disambiguate
  - `no_order_candidates`: No matching orders found in Shopify
  - `parse_error`: Data parsing or extraction failures
  - `other_error` / `other_failure`: Catch-all for other issues
- Location: `failure_buckets` in summary JSON

**Match Failure Buckets (Deployment Gate):**
- Categorizes order-match failures into gate-friendly buckets:
  - `no_email`, `no_order_number`, `ambiguous_customer`, `no_order_candidates`
- Location: `match_failure_buckets` in summary JSON

**Drift Watch Thresholds:**
- Compares current metrics to defined thresholds:
  - **Match Rate Drop**: Alert if match rate drops > 10 percentage points (requires historical baseline)
  - **API Error Rate**: Alert if API errors exceed 5% of tickets
  - **Order Number Share Drop**: Alert if order_number match share drops > 15% (requires historical baseline)
  - **Schema Drift**: Alert if > 20% of schemas are new (uses filtered key paths)
- Location: `drift_watch` in summary JSON with `alerts` array
- Note: Historical comparison not yet implemented; current version shows absolute thresholds only
  - Filtered schema drift ignores ids, timestamps, pagination, and volatile subtrees (comments, tags, custom fields)
  - See `schema_key_stats` in summary JSON for the top filtered vs ignored key paths (ignored paths include nested keys under skipped subtrees)
  - `ticket_fetch_failed` is treated as a run warning and excluded from API error rate
  - `ticket_fetch_failure_rate_pct` is reported in `drift_watch.current_values` for visibility

When drift or match failures spike:
- If `run_warnings` includes `ticket_listing_403`, provide explicit `ticket-ids` or set `PROD_RICHPANEL_TICKET_IDS`
- Review `top_failure_reasons` plus `richpanel_fetch_failures` / `shopify_fetch_failures`
- **NEW (B61/C):** Check `failure_buckets` for PII-safe categorization of failures
- **NEW (B61/C):** Review `route_decisions` to see if classification is shifting
- **NEW (B61/C):** Check `match_methods` to identify if a specific match strategy is failing
- **NEW (B61/C):** Review `drift_watch.alerts` for threshold violations
- For `shopify_401`/`shopify_403`: verify token + `SHOPIFY_SHOP_DOMAIN`, confirm read-only scopes
- For `no_customer_email` / `no_order_candidates`: inspect recent ticket payloads and extraction paths
- Compare `ticket_schema_fingerprint` / `shopify_schema_fingerprint` in the report to identify new payload shapes
- Re-run `workflow_dispatch` with explicit ticket IDs + `--shopify-probe` for deeper inspection

### Deployment gate criteria (recommended)

Block deployment if any of the following occur:

- Script exits non-zero (read-only guard tripped or API failures).
- `http_trace_summary.allowed_methods_only=false` or non-read-only HTTP entries appear.
- `would_reply_send=true` in the report (should be false for prod read-only).
- `ticket_count=0` or `run_warnings` includes `ticket_listing_failed` (no usable sample).
- `run_warnings` includes `ticket_fetch_failed` (ticket IDs stale or access revoked).
- `drift_watch.has_alerts=true` (API error rate or schema drift exceeds thresholds).

Treat `match_success_rate` and `tracking_or_eta_available_rate` as baseline health signals;
compare to the most recent successful run for that environment, and block if they regress materially.

### Common failure modes (401 / 403)
- **401 Unauthorized (Shopify):** token invalid/expired, wrong `SHOPIFY_SHOP_DOMAIN`, or secret still
  contains a placeholder value. Fix by updating `rp-mw/prod/shopify/admin_api_token` (and ensure the
  shop domain matches the token's store). If there is a single store, align prod + dev secrets.
- **403 Forbidden (Shopify):** token lacks required scopes (`read_orders`, `read_fulfillments`, etc.)
  or the app is not installed on the target store. Reinstall the app and mint a read-only token.
- **403 Forbidden (Richpanel conversations):** conversation endpoints may be restricted even when
  ticket reads succeed. Use explicit ticket IDs for shadow runs if list endpoints are blocked.

Success evidence for PRs:
- Command used (including flags)
- Paths to the report JSON/MD and HTTP trace JSON (GET/HEAD only)
- Cross-reference Shopify data expectations in `docs/SHOPIFY_STRATEGY/` for store-specific nuances
- **B61/C:** Include drift watch summary showing current values vs thresholds
- **B61/C:** Include route decision and match method distributions

---

## Interpreting Shadow Eval Metrics (B61/C)

The shadow eval report includes several diagnostic metrics to help you understand system behavior and identify drift:

### Route Decision Distribution

**What it measures:** How tickets are classified by the routing logic.

**Values:**
- `order_status`: Tickets classified as order status inquiries
- `non_order_status`: Tickets classified as other intents (returns, general inquiry, etc.)
- `unknown`: Tickets that couldn't be classified

**When to investigate:**
- If `order_status` percentage drops significantly, check:
  - Are customers phrasing inquiries differently?
  - Has the routing prompt or model changed?
  - Are ticket payloads missing expected fields?

### Match Method Telemetry

**What it measures:** Which matching strategy successfully resolved each order lookup.

**Values:**
- `order_number`: Matched via explicit order number in ticket (highest confidence)
- `name_email`: Matched via customer name + email (high confidence)
- `email_only`: Matched via email only (medium confidence, may be ambiguous)
- `none`: No match found
- `parse_error`: Failed due to data parsing issues

**When to investigate:**
- If `order_number` share drops, check:
  - Are customers including order numbers less often?
  - Is order number extraction failing (regex patterns, field names)?
- If `email_only` increases significantly, check:
  - Are name fields missing or malformed?
  - Is this causing ambiguous matches (multiple orders per email)?
- If `none` increases, check:
  - Are customer identifiers (email, name) missing?
  - Is Shopify API returning empty results?

### Schema Key Stats (PII-safe)

**What it measures:** Top field-path frequencies for ticket + Shopify payloads after filtering noisy keys.

**Location:** `schema_key_stats` in summary JSON.

**When to investigate:**
- Review `filtered_top_paths` to understand stable contract shape.
- Review `ignored_top_paths` to confirm the noisy keys being suppressed (ids, timestamps, pagination, comments/tags/custom fields), including nested keys under skipped subtrees.

### Failure Buckets (PII-safe)

**What it measures:** Categorizes failures into stable, actionable buckets.

**Buckets:**
- `no_identifiers`: Missing customer email or order identifiers → Check ticket payload structure
- `shopify_api_error`: Shopify API failures → Check API status, rate limits, token validity
- `richpanel_api_error`: Richpanel API failures → Check API status, token validity
- `ambiguous_match`: Multiple orders matched → Improve disambiguation logic or require order numbers
- `no_order_candidates`: No matching orders in Shopify → Customer may not have orders, or email mismatch
- `parse_error`: Data parsing failures → Check payload structure changes
- `other_error` / `other_failure`: Catch-all → Review raw failure reasons in `failure_reasons`

**When to investigate:**
- If `shopify_api_error` or `richpanel_api_error` spike, check API health and credentials
- If `no_identifiers` increases, check ticket payload structure (are email fields present?)
- If `ambiguous_match` increases, consider requiring order numbers for disambiguation

### Drift Watch Thresholds

**What it measures:** Compares current metrics to defined thresholds to detect anomalies.

**Thresholds:**
- **Match Rate Drop**: Alert if match rate drops > 10 percentage points (requires historical baseline)
- **API Error Rate**: Alert if API errors exceed 5% of tickets
- **Order Number Share Drop**: Alert if order_number match share drops > 15% (requires historical baseline)
- **Schema Drift**: Alert if > 20% of schemas are new (indicates payload structure changes)

**When to investigate:**
- If **API Error Rate** exceeds threshold:
  - Check API status pages (Shopify, Richpanel)
  - Verify tokens and credentials
  - Check for rate limiting
- If **Schema Drift** exceeds threshold:
  - Review new schema fingerprints in report
  - Check if Richpanel or Shopify changed their API response structure
  - Update extraction logic if needed
- If **Match Rate Drop** or **Order Number Share Drop** alerts trigger (future):
  - Compare to historical baselines
  - Investigate recent changes to routing, extraction, or customer behavior

**Note:** Historical comparison is not yet implemented. Current version shows absolute thresholds only. Future enhancements will track metrics over time to detect drops.

---

## How to enable shadow mode

### Step 1: Set runtime kill switches (SSM)

Use the `set-runtime-flags.yml` workflow to update SSM parameters:

```powershell
gh workflow run set-runtime-flags.yml `
  --ref main `
  -f environment=<dev|staging|prod> `
  -f safe_mode=true `
  -f automation_enabled=false
```

Verify SSM parameters were set:

```powershell
# View SSM parameter values (requires AWS CLI + appropriate role)
aws ssm get-parameters `
  --names "/rp-mw/<env>/safe_mode" "/rp-mw/<env>/automation_enabled" `
  --region us-east-2 `
  --query 'Parameters[*].[Name,Value]' `
  --output table
```

### Step 2: Set Lambda environment variables

**Option A: GitHub Actions workflow (recommended for dev/staging)**

```powershell
# Note: This sets Lambda env vars; SSM parameters are separate (Step 1)
gh workflow run set-runtime-flags.yml `
  --ref main `
  -f environment=staging `
  -f richpanel_write_disabled=true `
  -f richpanel_outbound_enabled=false `
  -f mw_allow_network_reads=true
```

Verify Lambda env vars were applied:

```powershell
aws lambda get-function-configuration `
  --function-name rp-mw-staging-worker `
  --region us-east-2 `
  --query 'Environment.Variables' `
  --output json
```

**Option B: Manual AWS Console (production)**

For **production**, manual changes require explicit PM/lead approval and change control:

**Set Lambda env vars:**
1. Navigate to: AWS Console → Lambda → `rp-mw-prod-worker` → Configuration → Environment variables
2. Click **Edit**
3. Add/update: `MW_ALLOW_NETWORK_READS=true`, `RICHPANEL_WRITE_DISABLED=true`, `RICHPANEL_OUTBOUND_ENABLED=false`, `SHOPIFY_WRITE_DISABLED=true`
4. Click **Save**

**Set SSM parameters:**
1. Navigate to: AWS Console → Systems Manager → Parameter Store
2. Update `/rp-mw/prod/safe_mode` → `true`
3. Update `/rp-mw/prod/automation_enabled` → `false`

**Document the change:**
5. Record change in `docs/00_Project_Admin/Progress_Log.md` with PM/lead approval timestamp and incident response plan

**Do not enable shadow mode in production without:**
- Explicit PM/lead sign-off recorded in Progress Log
- Staging shadow mode validation completed and documented
- Incident response plan identified (who can disable the flags if issues arise)

### Option 3: Infrastructure-as-Code (CDK)

If your CDK stack supports environment variable overrides, add them to the worker Lambda construct:

```typescript
// infra/cdk/lib/richpanel-middleware-stack.ts (example)
const workerLambda = new lambda.Function(this, 'WorkerFunction', {
  // ... other config ...
  environment: {
    MW_ALLOW_NETWORK_READS: 'true',
    RICHPANEL_WRITE_DISABLED: 'true',
    SHOPIFY_WRITE_DISABLED: 'true',
    RICHPANEL_OUTBOUND_ENABLED: 'false',
    // Note: automation_enabled is controlled via SSM parameters, not Lambda env vars
    // Use set-runtime-flags.yml workflow to set automation_enabled=false
  },
});
```

**Note:** CDK changes require a full stack deployment; use runtime workflows for quick toggles (especially for SSM parameters).

---

## Prove zero writes (audit procedure)

After enabling shadow mode, verify that no writes are occurring:

### Step 1: Review CloudWatch Logs

Search for write operations in the worker Lambda logs:

```bash
# PowerShell-safe CloudWatch Insights query (replace <START_TIME> and <END_TIME>)
$logGroup = "/aws/lambda/rp-mw-staging-worker"
$queryString = @"
fields @timestamp, @message
| filter @message like /POST|PUT|PATCH|DELETE/
| filter @message like /richpanel|shopify|shipstation/
| sort @timestamp desc
| limit 100
"@

aws logs start-query `
  --log-group-name $logGroup `
  --start-time <START_TIME_EPOCH> `
  --end-time <END_TIME_EPOCH> `
  --query-string $queryString `
  --region us-east-2
```

**Expected result:** No POST/PUT/PATCH/DELETE calls to Richpanel, Shopify, or ShipStation APIs.

If you see write operations, **immediately disable shadow mode** and investigate.

### Step 2: Audit middleware request logs

The middleware logs all HTTP requests with the following structure:

```json
{
  "level": "INFO",
  "message": "Richpanel API request",
  "method": "GET",
  "url": "/api/v1/conversations/<conversation_id>",
  "redacted": true
}
```

Search for non-GET requests:

```bash
# CloudWatch Insights query for non-GET Richpanel requests
fields @timestamp, method, url, message
| filter method != "GET"
| filter message like /Richpanel API request/
| sort @timestamp desc
```

**Expected result:** Zero non-GET requests.

### Step 3: Verify write-disabled errors are logged

When `RICHPANEL_WRITE_DISABLED=true`, the middleware should **refuse** write operations and log a `RichpanelWriteDisabledError`:

```bash
# CloudWatch Insights query for write-disabled errors
fields @timestamp, @message
| filter @message like /RichpanelWriteDisabledError|RICHPANEL_WRITE_DISABLED/
| sort @timestamp desc
```

**Expected result:** If the worker attempts a write (e.g., during testing), you should see:

```
RichpanelWriteDisabledError: Richpanel write operation blocked (RICHPANEL_WRITE_DISABLED=true)
```

If you do **not** see this error when testing a write operation, the flag may not be configured correctly.

### Step 4: Check for outbound communications

Verify that no emails, SMS, or push notifications were sent:

```bash
# CloudWatch Insights query for outbound sends
fields @timestamp, @message
| filter @message like /send_email|send_sms|send_notification|outbound/
| sort @timestamp desc
```

**Expected result:** Zero outbound communications.

If `RICHPANEL_OUTBOUND_ENABLED=false` is set, any outbound attempt should log:

```
Outbound communication skipped (RICHPANEL_OUTBOUND_ENABLED=false)
```

---

## Configure middleware to hard-fail on non-GET calls

For maximum safety, configure the middleware to **raise an exception** (instead of just logging) when a write is attempted in shadow mode.

### Enforcement in code

The Richpanel client enforces write blocking via the `RICHPANEL_WRITE_DISABLED` flag:

```python
# backend/src/richpanel_middleware/integrations/richpanel/client.py (example)
def _request(self, method: str, path: str, **kwargs) -> RichpanelResponse:
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        if os.getenv("RICHPANEL_WRITE_DISABLED", "false").lower() == "true":
            raise RichpanelWriteDisabledError(
                f"Richpanel write operation blocked (RICHPANEL_WRITE_DISABLED=true): {method} {path}"
            )
    # ... proceed with request ...
```

### Testing the hard-fail behavior

To confirm the middleware refuses writes:

1. Enable shadow mode flags (see "How to enable shadow mode")
2. Trigger a test event that would normally write (e.g., order status update, tag application)
3. Verify the worker logs show `RichpanelWriteDisabledError` **and the Lambda invocation fails**
4. Confirm no writes occurred in Richpanel UI (check ticket history, tags, comments)

**Test command (dev environment):**

```powershell
# Send a synthetic webhook that triggers an order status reply (which includes tagging)
$eventId = "evt:shadow-test-" + (Get-Date -Format 'yyyyMMddHHmmss')
python scripts/dev_e2e_smoke.py `
  --env dev `
  --region us-east-2 `
  --scenario order_status_tracking `
  --ticket-number <test-ticket-number> `
  --run-id RUN_SHADOW_TEST `
  --wait-seconds 60 `
  --proof-path "REHYDRATION_PACK/RUNS/RUN_SHADOW_TEST/shadow_mode_proof.json"
```

**Expected result:**
- Worker processes the event and performs reads (fetch ticket, fetch order, etc.)
- Worker attempts to apply tags or update status
- Middleware raises `RichpanelWriteDisabledError`
- Lambda invocation fails (logged in CloudWatch)
- **No tags or comments appear in Richpanel ticket history**

---

## What shadow mode allows (read-only operations)

When shadow mode is enabled, the following operations **are allowed**:

### Richpanel (read-only)
- Fetch conversation details (`GET /api/v1/conversations/<id>`)
- Fetch linked orders (`GET /api/v1/conversations/<id>/orders`)
- Fetch ticket status, tags, metadata
- Fetch customer profile
- Fetch message history

### Shopify (read-only)
- Fetch order details (`GET /admin/api/<version>/orders/<id>.json`)
- Fetch fulfillment/tracking data
- Fetch customer details
- Query order status

### ShipStation (read-only)
- Fetch shipment tracking
- Fetch carrier/delivery estimates

### Internal operations (always allowed)
- DynamoDB writes to idempotency, conversation_state, and audit tables (these are internal, not customer-facing)
- CloudWatch logging
- Routing classification (intent/department)
- Template rendering (for validation purposes)
- Draft reply generation (not sent, just validated)

---

## What shadow mode blocks (write operations)

When shadow mode is enabled, the following operations **are blocked**:

### Richpanel (writes)
- Add/remove tags
- Add comments or internal notes
- Update ticket status (open/closed/resolved)
- Assign to team/agent
- Change priority
- Update custom fields
- Any POST/PUT/PATCH/DELETE to Richpanel API

### Shopify (writes)
- Create/update orders
- Add order notes
- Update fulfillment status
- Any POST/PUT/PATCH/DELETE to Shopify Admin API

### Outbound communications
- Send customer replies (email, SMS, push)
- Send notifications to agents
- Trigger external webhooks (if configured)

### Automation
- Auto-reply execution (templates are rendered but not sent)
- Auto-close tickets
- Auto-assign to teams
- Follow-up automation triggers

---

## Use cases for shadow mode

### 1. Validate production data structures

**Scenario:** You want to verify that production Richpanel conversations have the expected `linked_order` structure before enabling order status automation.

**Procedure:**
1. Enable shadow mode in production (with PM approval)
2. Monitor CloudWatch logs for 24-48 hours
3. Review fetched order payloads (logged at INFO level)
4. Verify field presence: `order.id`, `order.fulfillment.tracking_number`, etc.
5. Disable shadow mode
6. Document findings in `docs/05_FAQ_Automation/Order_Status_Automation.md`

### 2. Test routing accuracy without customer impact

**Scenario:** You want to measure routing/classification accuracy on real production traffic before enabling automation.

**Procedure:**
1. Enable shadow mode in production (with PM approval)
2. Let the middleware classify incoming tickets (no writes, no replies)
3. Export routing decisions from DynamoDB `conversation_state` table
4. Compare middleware routing to actual agent routing (manual audit)
5. Calculate accuracy: `correct_routes / total_routes`
6. Document findings and tune routing prompts if needed
7. Disable shadow mode

### 3. Validate order lookup behavior

**Scenario:** You want to confirm that order lookup works correctly for production customers without sending replies.

**Procedure:**
1. Enable shadow mode in production (with PM approval)
2. Identify 5-10 recent order status tickets (from Richpanel UI)
3. Trigger webhook replays for those tickets (if webhook replay is available)
4. Review CloudWatch logs to confirm:
   - Order was fetched successfully
   - Tracking details were extracted
   - Template was rendered correctly
   - **No reply was sent** (blocked by `RICHPANEL_OUTBOUND_ENABLED=false`)
5. Disable shadow mode
6. Document accuracy in `qa/test_evidence/shadow_mode_validation/`

---

## Risks and mitigations

### Risk 1: Flag misconfiguration allows writes

**Mitigation:**
- Always run the "Prove zero writes" audit after enabling shadow mode
- Test with a known write operation (e.g., tag application) and confirm it fails
- Monitor CloudWatch Logs for 15-30 minutes after enabling to catch any unexpected writes

### Risk 2: Read operations cause rate limiting or cost spikes

**Mitigation:**
- Start with a short shadow mode window (1-2 hours) and monitor API usage
- Check Richpanel/Shopify API rate limits in their dashboards
- If rate limits are hit, disable shadow mode immediately
- Document API usage patterns in `docs/03_Richpanel_Integration/API_Usage_and_Rate_Limits.md`

### Risk 3: Logging exposes PII

**Mitigation:**
- Ensure all logging uses PII redaction (customer emails, phone numbers, addresses)
- Review CloudWatch Logs export policy (restrict access to authorized roles)
- Do not export raw logs to third-party tools without PII scrubbing

### Risk 4: Shadow mode left enabled indefinitely

**Mitigation:**
- Set a CloudWatch alarm for `RICHPANEL_WRITE_DISABLED=true` in production
- Require shadow mode enablement to include a planned end time (documented in Progress Log)
- Use the auto-revert workflow for dev/staging (see CI runbook)

---

## Disable shadow mode

To return to normal operation (writes enabled):

### Step 1: Re-enable runtime kill switches (SSM)

**Option A: GitHub Actions workflow (recommended)**

```powershell
gh workflow run set-runtime-flags.yml `
  --ref main `
  -f environment=<dev|staging|prod> `
  -f safe_mode=false `
  -f automation_enabled=true
```

**Option B: Manual AWS Console**

1. Navigate to: AWS Console → Systems Manager → Parameter Store
2. Update `/rp-mw/<env>/safe_mode` → `false`
3. Update `/rp-mw/<env>/automation_enabled` → `true`

### Step 2: Re-enable Lambda environment variables

**Option A: GitHub Actions workflow**

```powershell
gh workflow run set-runtime-flags.yml `
  --ref main `
  -f environment=<dev|staging|prod> `
  -f richpanel_write_disabled=false `
  -f richpanel_outbound_enabled=true `
  -f mw_allow_network_reads=true
```

**Option B: Manual AWS Console**

1. Navigate to: AWS Console → Lambda → `rp-mw-<env>-worker` → Configuration → Environment variables
2. Click **Edit**
3. Set:
   - `RICHPANEL_WRITE_DISABLED=false`
   - `RICHPANEL_OUTBOUND_ENABLED=true`
   - (Optional) Remove `SHOPIFY_WRITE_DISABLED` or set to `false`
4. Click **Save**
5. Document the change in Progress Log with timestamp

### Option 3: Auto-revert (dev-only)

For **dev** environment, use the auto-revert workflow to temporarily enable writes with automatic revert:

```powershell
# Enable outbound writes for 30 minutes (max 55 minutes)
gh workflow run set-outbound-flags.yml `
  --ref main `
  -f action=enable `
  -f auto_revert=true `
  -f revert_after_minutes=30
```

After the time window, the workflow automatically reverts to safe mode (writes disabled).

**Note:** Auto-revert is **dev-only**; never use this in staging or production.

---

## Evidence requirements

When running shadow mode validation, capture the following evidence:

### Before enabling
- [ ] PM/lead approval timestamp (for production)
- [ ] Current Lambda environment variables (screenshot or CLI output)
- [ ] Incident response plan documented (who can disable flags)

### During shadow mode
- [ ] CloudWatch Logs query results (prove zero writes)
- [ ] API usage metrics (Richpanel/Shopify dashboards)
- [ ] Sample routing/classification logs (redacted)
- [ ] Any errors or warnings logged

### After disabling
- [ ] Confirmation that flags were reverted
- [ ] Summary of findings (data structures validated, accuracy measured, etc.)
- [ ] Updated documentation (if data structures differ from expectations)
- [ ] Progress Log entry with start/end timestamps

All evidence should be stored in:

```
qa/test_evidence/shadow_mode_validation/<RUN_ID>/
  - before_flags.json
  - cloudwatch_audit.log
  - api_usage_metrics.png
  - routing_accuracy.csv
  - after_flags.json
  - summary.md
```

---

## Related documentation

- **CI and Actions Runbook:** `docs/08_Engineering/CI_and_Actions_Runbook.md` (E2E proof + dev outbound toggle)
- **Order Status Automation:** `docs/05_FAQ_Automation/Order_Status_Automation.md` (safety constraints)
- **Richpanel Integration:** `docs/03_Richpanel_Integration/Richpanel_API_Client_Integration.md` (write-disabled error)
- **Security & Privacy:** `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md` (logging redaction)
- **Operations Runbooks:** `docs/10_Operations_Runbooks_Training/` (incident response)

---

## Checklist: Production shadow mode validation (complete workflow)

Use this checklist when validating production shadow mode:

- [ ] Obtain PM/lead approval for production shadow mode (record in Progress Log)
- [ ] Document incident response plan (who can disable flags, escalation path)
- [ ] Enable shadow mode flags (see "How to enable shadow mode")
- [ ] Verify flags are set (AWS CLI or Console)
- [ ] Run "Prove zero writes" audit (CloudWatch Logs queries)
- [ ] Test hard-fail behavior (trigger write operation, confirm it fails)
- [ ] Monitor for 15-30 minutes (watch for unexpected writes or errors)
- [ ] Capture evidence (logs, metrics, sample payloads)
- [ ] Run validation use case (data structures, routing accuracy, order lookup)
- [ ] Disable shadow mode (revert flags)
- [ ] Verify flags were reverted (AWS CLI or Console)
- [ ] Document findings in Progress Log and relevant spec docs
- [ ] Store evidence in `qa/test_evidence/shadow_mode_validation/<RUN_ID>/`

**Do not skip steps.** Shadow mode in production is a high-risk operation; follow the checklist fully.
