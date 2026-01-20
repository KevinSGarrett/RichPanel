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

# Disable ALL outbound communications (email, SMS, push notifications)
RICHPANEL_OUTBOUND_ENABLED=false
```

### Verification checklist

Before enabling shadow mode in production:

- [ ] Confirm SSM parameters are set: `safe_mode=true`, `automation_enabled=false` (via workflow or SSM console)
- [ ] Confirm Lambda env vars are set: `MW_ALLOW_NETWORK_READS=true`, `RICHPANEL_WRITE_DISABLED=true`, `RICHPANEL_OUTBOUND_ENABLED=false`
- [ ] (Optional) Confirm `SHOPIFY_WRITE_DISABLED=true` is set
- [ ] Review CloudWatch logs to confirm no write operations are attempted
- [ ] Run the "Prove zero writes" audit (see below)

### Live read-only shadow eval script (local)

- Script: `scripts/live_readonly_shadow_eval.py`
- Required secrets (AWS Secrets Manager): `rp-mw/prod/richpanel/api_key`, `rp-mw/prod/shopify/admin_api_token`
- Required env vars (the script enforces/fails-closed):
  - `MW_ALLOW_NETWORK_READS=true`
  - `RICHPANEL_OUTBOUND_ENABLED=true` (required for real GETs; still read-only)
  - `RICHPANEL_WRITE_DISABLED=true`
- Note: This is **local script** configuration. Production worker shadow mode should still keep `RICHPANEL_OUTBOUND_ENABLED=false`.
- Optional overrides:
  - `RICHPANEL_API_KEY_OVERRIDE` (set to `PROD_RICHPANEL_API_KEY` for prod runs)
  - `SHOPIFY_SHOP_DOMAIN` (or `--shop-domain` flag) to target the correct store
  - `RICHPANEL_API_KEY_SECRET_ID` can be overridden with `--richpanel-secret-id`
- Run locally (PowerShell example, requires AWS creds with secrets access):

```powershell
$env:RICHPANEL_API_KEY_OVERRIDE = $env:PROD_RICHPANEL_API_KEY
$env:MW_ALLOW_NETWORK_READS = "true"
$env:RICHPANEL_OUTBOUND_ENABLED = "true"
$env:RICHPANEL_WRITE_DISABLED = "true"

python scripts/live_readonly_shadow_eval.py `
  --ticket-id <ticket-or-conversation-id> `
  --richpanel-secret-id rp-mw/prod/richpanel/api_key `
  --shop-domain <myshop.myshopify.com>
```

What it does:
- Requires the read-only env flags above (fails closed if missing or incorrect)
- Reads ticket + conversation, performs order lookup (Shopify fallback) with `allow_network` gated to reads only
- Builds a dry-run action plan and prints a PII-safe preview of the planned response (no posts/tags)
- Writes a PII-safe artifact to `artifacts/readonly_shadow/<timestamp>_<ticket_hash>.json` containing: redacted ticket id, redacted customer identifiers, routing/intent, whether tracking was found, and ETA window (if no tracking)
- Captures a redacted HTTP trace to `artifacts/prod_readonly_shadow_eval_http_trace.json` and fails if any non-GET calls are observed

Success evidence for PRs:
- Command used (including flags)
- Path to the generated artifact JSON
- Path to the HTTP trace JSON (should contain only GET requests)
- Cross-reference Shopify data expectations in `docs/SHOPIFY_STRATEGY/` for store-specific nuances

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
