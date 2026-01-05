# Richpanel Configuration Runbook (v1)

**Last updated:** 2026-01-04  
**Status:** Reflects shipped middleware behavior (webhook path, headers, secret IDs)

**Purpose:** Explicit, step-by-step runbook for configuring Richpanel to work with the middleware. This is **documentation only** — do not modify the Richpanel UI until Section B is explicitly approved.

---

## Guiding Principles (v1)
1. **Inbound-only triggers**: middleware runs only on customer messages (not agent replies)
2. **No auto-close**: middleware never closes conversations; Richpanel should not auto-close customer issues in v1 unless explicitly approved (spam/system-notifs only)
3. **Tag-driven routing**: middleware applies `route-*` tags; Richpanel assignment rules map tags → Teams
4. **Durable-first**: HTTP Target handler must persist/enqueue and ACK fast; do not assume Richpanel retries
5. **Minimum PII**: HTTP Target payload includes only what is needed; logs must redact
6. **Staging-first validation**: always validate in staging before touching production

---

## Section A: Doc-Only Prep (Safe, No UI Changes)

This section helps you gather information and prepare for the UI configuration. **No changes are made to Richpanel.**

### A.1 Fetch CloudFormation outputs (PowerShell)

Run these commands to get the middleware endpoint URL for each environment:

**Dev environment:**
```powershell
$devStackName = "rp-mw-dev"
$devOutputs = aws cloudformation describe-stacks --stack-name $devStackName --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
$devEndpoint = ($devOutputs | Where-Object { $_.OutputKey -eq "IngressEndpointUrl" }).OutputValue
Write-Host "Dev webhook URL: $devEndpoint/webhook"
```

**Staging environment:**
```powershell
$stagingStackName = "rp-mw-staging"
$stagingOutputs = aws cloudformation describe-stacks --stack-name $stagingStackName --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
$stagingEndpoint = ($stagingOutputs | Where-Object { $_.OutputKey -eq "IngressEndpointUrl" }).OutputValue
Write-Host "Staging webhook URL: $stagingEndpoint/webhook"
```

**Prod environment:**
```powershell
$prodStackName = "rp-mw-prod"
$prodOutputs = aws cloudformation describe-stacks --stack-name $prodStackName --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
$prodEndpoint = ($prodOutputs | Where-Object { $_.OutputKey -eq "IngressEndpointUrl" }).OutputValue
Write-Host "Prod webhook URL: $prodEndpoint/webhook"
```

### A.2 Verify secrets exist (PowerShell)

Check that the required secrets exist in AWS Secrets Manager:

```powershell
# Check webhook token secrets
$envs = @("dev", "stage", "prod")
foreach ($env in $envs) {
    $webhookSecretId = "rp-mw/$env/richpanel/webhook_token"
    $apiKeySecretId = "rp-mw/$env/richpanel/api_key"
    
    Write-Host "Checking $env environment..."
    
    try {
        aws secretsmanager describe-secret --secret-id $webhookSecretId --query "Name" --output text
        Write-Host "  ✓ Webhook token exists: $webhookSecretId"
    } catch {
        Write-Host "  ✗ Missing: $webhookSecretId" -ForegroundColor Red
    }
    
    try {
        aws secretsmanager describe-secret --secret-id $apiKeySecretId --query "Name" --output text
        Write-Host "  ✓ API key exists: $apiKeySecretId"
    } catch {
        Write-Host "  ✗ Missing: $apiKeySecretId" -ForegroundColor Red
    }
}
```

**IMPORTANT:** Do NOT print secret values. Only verify that the secret IDs exist.

### A.3 Canonical secret IDs (reference)

The middleware expects these exact secret IDs in AWS Secrets Manager:

| Environment | Webhook Token Secret ID | API Key Secret ID |
|---|---|---|
| Dev | `rp-mw/dev/richpanel/webhook_token` | `rp-mw/dev/richpanel/api_key` |
| Staging | `rp-mw/stage/richpanel/webhook_token` | `rp-mw/stage/richpanel/api_key` |
| Prod | `rp-mw/prod/richpanel/webhook_token` | `rp-mw/prod/richpanel/api_key` |

### A.4 Required tags (reference)

Before configuring Richpanel, you'll need to create these tags in the UI:

**Routing tags (11):**
1. `route-sales-team`
2. `route-backend-team`
3. `route-technical-support-team`
4. `route-phone-support-team`
5. `route-tiktok-support`
6. `route-returns-admin`
7. `route-livechat-support`
8. `route-leadership-team`
9. `route-socialmedia-team`
10. `route-email-support-team`
11. `route-chargebacks-disputes`

**Middleware control tags (4):**
- `mw-processed` — middleware successfully ingested/handled the inbound event
- `mw-routing-applied` — middleware applied a routing decision (route tag set)
- `mw-auto-replied` — middleware sent an automated customer-facing reply
- `mw-escalated-human` — middleware forced a human handoff (Tier 0 / Tier 1)

### A.5 Required team (reference)

You'll need to create this team in Richpanel:

- **Name:** `Chargebacks / Disputes`
- **Purpose:** Handle disputes/chargebacks and payment processor notifications
- **Policy:** Tier 0 — never auto-reply; auto-close only for whitelisted, deflection-safe templates; human-only
- **Membership:** Restricted to staff who handle payment disputes

---

## Section B: Human UI Steps (Gated — Requires Approval)

**STOP:** Do not proceed with this section until:
1. Section A is complete
2. You have explicit approval to modify Richpanel UI
3. You are working in **STAGING first** (not production)

### B.1 Create tags in Richpanel UI

In the Richpanel UI (staging workspace):
1. Navigate to Settings → Tags
2. Create all 11 `route-*` tags (see A.4)
3. Create all 4 `mw-*` tags (see A.4)

**Naming rules:**
- Use exact names (lowercase, hyphenated)
- Do NOT overload existing topic tags (e.g., `refund-request`) for routing

### B.2 Create team in Richpanel UI

In the Richpanel UI (staging workspace):
1. Navigate to Settings → Teams
2. Create `Chargebacks / Disputes` team (see A.5)
3. Add appropriate members

### B.3 Configure HTTP Target webhook

In the Richpanel UI (staging workspace):
1. Navigate to Settings → Integrations → Webhooks (or HTTP Targets)
2. Create new webhook:
   - **URL:** `POST <IngressEndpointUrl>/webhook` (from A.1)
   - **Header name:** `x-richpanel-webhook-token`
   - **Header value:** Retrieve from AWS Secrets Manager:
     ```powershell
     aws secretsmanager get-secret-value --secret-id "rp-mw/stage/richpanel/webhook_token" --query SecretString --output text
     ```
   - **Payload (minimal):**
     ```json
     { "ticket_id": "{{ticket.id}}", "ticket_url": "{{ticket.url}}", "trigger": "customer_message" }
     ```

**IMPORTANT:** Do NOT paste the webhook token value into any documentation, logs, or screenshots.

### B.4 Create automation rule: Middleware inbound trigger

In the Richpanel UI (staging workspace):
1. Navigate to Automations → Tagging Rules (preferred) or Assignment Rules (fallback)
2. Create new rule:
   - **Name:** `Middleware — Inbound Trigger`
   - **Trigger:**
     - "A customer starts a new conversation" OR
     - "Immediately after a customer sends a new message"
   - **Action:** "Trigger HTTP Target" → select the webhook created in B.3
   - **Toggles:**
     - **Skip all subsequent rules = OFF** (must be OFF)
3. Move this rule to the **top** of the Tagging Rules list

**Why Tagging Rules?** Assignment Rules often use "Skip all subsequent rules", which can block later rules. Placing the trigger in Tagging Rules reduces this risk.

### B.5 Create assignment rules: routing tag → team

In the Richpanel UI (staging workspace):
1. Navigate to Automations → Assignment Rules
2. For each routing tag (see A.4), create a rule:
   - **Trigger:** "When a tag is added"
   - **Condition:** tag equals `route-<team-name>`
   - **Action:** Assign conversation to corresponding team
   - **Toggles:** Enable "skip subsequent rules when matched" (if available)

**Mapping:**

| Tag | Assign to team |
|---|---|
| `route-sales-team` | Sales Team |
| `route-backend-team` | Backend Team |
| `route-technical-support-team` | Technical Support Team |
| `route-phone-support-team` | Phone Support Team |
| `route-tiktok-support` | TikTok Support |
| `route-returns-admin` | Returns Admin |
| `route-livechat-support` | LiveChat Support |
| `route-leadership-team` | Leadership Team |
| `route-socialmedia-team` | SocialMedia Team |
| `route-email-support-team` | Email Support Team |
| `route-chargebacks-disputes` | Chargebacks / Disputes |

### B.6 De-conflict legacy assignment rules

In the Richpanel UI (staging workspace):
1. Review existing assignment rules that might conflict with middleware routing:
   - `[Auto Assign] Customer Support`
   - `[Auto Assign] Tech Support (defective keywords)`
   - `[Auto Assign] Social Media Team`
   - `Auto Assign LiveChat`
   - `[Auto Assign] TikTok`

2. For each rule, add a condition guard:
   - **Condition:** Tags does not contain `mw-routing-applied`
   - **Alternative (if Richpanel doesn't support "tag NOT present"):** Turn OFF "reassign even if already assigned"

### B.7 Disable/replace chargeback auto-close rules

In the Richpanel UI (staging workspace):
1. Locate these rules:
   - `Chargeback - Auto Close`
   - `Auto close- Chargeback`
   - `Payout/Recurring/Chargeback - Auto Close`

2. Either:
   - **Option A (preferred):** Disable the rules entirely
   - **Option B:** Replace "close conversation" action with:
     - Apply tag `route-chargebacks-disputes`
     - Apply tag `mw-escalated-human`

**Do NOT auto-close chargebacks in v1.**

---

## Section C: Validation / Evidence (Staging First)

**CRITICAL:** Complete ALL validation steps in staging before touching production.

### C.1 Pre-deployment validation checklist

**Before** triggering a test customer message in Richpanel:

- [ ] CloudFormation stack deployed successfully (staging)
- [ ] Secrets exist in AWS Secrets Manager:
  - [ ] `rp-mw/stage/richpanel/webhook_token`
  - [ ] `rp-mw/stage/richpanel/api_key`
- [ ] Webhook configured in Richpanel (staging) with correct URL and header
- [ ] `Middleware — Inbound Trigger` rule exists and is enabled
- [ ] All 11 `route-*` tags created
- [ ] All 4 `mw-*` tags created
- [ ] `Chargebacks / Disputes` team created

### C.2 Functional validation (staging)

**Test 1: Webhook delivery**
1. In Richpanel staging, create a test customer message (or use a test channel)
2. Verify:
   - [ ] Middleware receives the webhook (check CloudWatch Logs for ingress function)
   - [ ] Webhook contains expected fields: `ticket_id`, `ticket_url`, `trigger`
   - [ ] Middleware ACKs with HTTP 200 in < 500ms

**Test 2: Tag application**
1. Create another test customer message
2. Verify:
   - [ ] Middleware applies `mw-processed` tag
   - [ ] Middleware applies `mw-routing-applied` tag
   - [ ] Middleware applies correct `route-*` tag based on message classification

**Test 3: Team assignment**
1. Verify:
   - [ ] Conversation is assigned to the correct team (based on `route-*` tag)
   - [ ] No routing fights (legacy rules don't override middleware routing)

**Test 4: Security (anti-spoof)**
1. Send a test webhook to the middleware endpoint **without** the `x-richpanel-webhook-token` header
2. Verify:
   - [ ] Middleware returns HTTP 401 Unauthorized

**Test 5: Idempotency**
1. Send the same webhook payload twice (simulate duplicate delivery)
2. Verify:
   - [ ] Tags are applied only once
   - [ ] No duplicate processing or replies

### C.3 Evidence capture (staging)

Capture the following evidence for each validation test:

1. **CloudWatch Logs screenshot/export:**
   - Ingress function logs showing successful webhook receipt
   - Log entries showing tag application
   - No errors or warnings

2. **Richpanel UI screenshot:**
   - Test conversation showing applied tags (`mw-*`, `route-*`)
   - Conversation assigned to correct team
   - No duplicate tags

3. **CloudWatch Metrics screenshot:**
   - Ingress function p95 latency < 500ms
   - No errors in past 24 hours

4. **GitHub Actions run URL (if applicable):**
   ```powershell
   # Find recent workflow runs
   gh run list --repo <your-org>/<your-repo> --workflow "Deploy Middleware" --limit 5
   ```

### C.4 Staging sign-off checklist

**Do NOT proceed to production until ALL of these are checked:**

- [ ] All validation tests (C.2) passed in staging
- [ ] Evidence captured and reviewed (C.3)
- [ ] No errors in CloudWatch Logs (past 24 hours)
- [ ] No errors in CloudWatch Metrics (past 24 hours)
- [ ] Team lead / PM has approved staging results
- [ ] Runbook reviewed and approved for production

### C.5 Production rollout (only after staging sign-off)

Repeat Section B (B.1-B.7) in the **production** Richpanel workspace, using production URLs and secrets:

- Webhook URL: `<prod-IngressEndpointUrl>/webhook`
- Webhook token: `rp-mw/prod/richpanel/webhook_token`

Then repeat Section C (C.1-C.3) for production validation.

### C.6 Rollback plan

If issues are detected in production:

1. **Immediate:** Disable `Middleware — Inbound Trigger` rule in Richpanel UI
2. **Verify:** Confirm middleware stops receiving webhooks
3. **Investigate:** Review CloudWatch Logs and metrics
4. **Fix:** Deploy hotfix (if needed)
5. **Re-enable:** Only after fix is validated in staging

---

## Reference: Shipped Middleware Behavior

This section documents the **actual** middleware behavior as deployed:

### Webhook endpoint
- **Path:** `POST <IngressEndpointUrl>/webhook`
- **NOT:** `/richpanel/inbound` (old path; no longer used)

### Authentication header
- **Header name:** `x-richpanel-webhook-token`
- **NOT:** `X-Middleware-Token` (old header; no longer used)

### Secret IDs
- **Webhook token:** `rp-mw/<env>/richpanel/webhook_token`
- **API key:** `rp-mw/<env>/richpanel/api_key`
- **Environments:** `dev`, `stage`, `prod`

### Payload expectations
Middleware expects **minimal payload** (v1):
```json
{
  "ticket_id": "{{ticket.id}}",
  "ticket_url": "{{ticket.url}}",
  "trigger": "customer_message"
}
```

**Do NOT include:**
- Base64 attachments
- Full conversation history
- Customer PII beyond what's necessary

---

## Appendix: PowerShell Helpers

### Find GitHub Actions run URLs

If using GitHub Actions for deployment:

```powershell
# List recent workflow runs
gh run list --repo <your-org>/<your-repo> --workflow "Deploy Middleware" --limit 10

# Get details for a specific run
gh run view <run-id> --web
```

### Verify CloudFormation stack status

```powershell
# Check stack status
aws cloudformation describe-stacks --stack-name rp-mw-staging --query "Stacks[0].StackStatus" --output text

# List all outputs
aws cloudformation describe-stacks --stack-name rp-mw-staging --query "Stacks[0].Outputs" --output table
```

### Check CloudWatch Logs (recent errors)

```powershell
# Get log group name
$logGroup = "/aws/lambda/rp-mw-staging-ingress"

# Get recent log streams
aws logs describe-log-streams --log-group-name $logGroup --order-by LastEventTime --descending --max-items 5

# Tail recent logs (last 1 hour)
$startTime = [int][double]::Parse((Get-Date).AddHours(-1).ToString("o")) * 1000
aws logs filter-log-events --log-group-name $logGroup --start-time $startTime --filter-pattern "ERROR"
```

---

## Acceptance Criteria (Definition of Done)

### Security & stability
- [ ] HTTP Target rejects spoof requests (middleware returns 401 if missing/incorrect `x-richpanel-webhook-token`)
- [ ] Middleware ACKs in < 500ms p95 (ingress path)
- [ ] Duplicate deliveries do not cause duplicate tags or replies
- [ ] Secrets stored in AWS Secrets Manager (never in code/logs/docs)

### Trigger reliability
- [ ] `Middleware — Inbound Trigger` exists and has **Skip all subsequent rules = OFF**
- [ ] Preferred: trigger lives in **Tagging Rules** (or equivalent) and is at the top of that category
- [ ] Fallback: if in Assignment Rules, it is the first rule

### Routing correctness
- [ ] Adding `route-*` tag triggers correct team assignment
- [ ] Legacy rules do not override middleware routing (no routing fights)
- [ ] Chargeback subjects route to Chargebacks / Disputes team (and do not auto-close)

### Staging-first validation
- [ ] All tests passed in staging before production rollout
- [ ] Evidence captured and reviewed
- [ ] Team lead / PM sign-off obtained
