# Richpanel UI Configuration Changes (v1) — Runbook (NO UI changes by automation)

Last updated: 2026-01-05  
Last verified: 2026-01-05 — Updated to match shipped ingress (`POST /webhook` + `x-richpanel-webhook-token`), added doc-only prep vs gated UI split, and refreshed canonical secret ID paths (no values).

This document defines the **exact Richpanel configuration changes** required to support the middleware safely.

It is written so Support Ops / Admins can implement changes in the Richpanel UI without guessing, and Engineering can implement middleware expectations without relying on undocumented behavior.

**Important:** this runbook includes both (a) doc-only prep steps and (b) **human Richpanel UI steps**. The UI steps are explicitly **gated**; do not execute them until the environment is deployed and the required gates/secrets are in place.

---

## 0) Runbook split (read this first)

### 0.1 Doc-only prep (NO Richpanel UI changes)
Do these steps first. They are safe to execute without touching the Richpanel UI:
- Pull the **ingress endpoint** from CloudFormation outputs.
- Pull the **secrets namespace** from CloudFormation outputs.
- Confirm required **Secrets Manager IDs** exist (do not write values into this doc).
- Confirm operator **kill switches / gating flags** are understood (`safe_mode`, `automation_enabled`, `OPENAI_OUTBOUND_ENABLED`, `RICHPANEL_OUTBOUND_ENABLED`).
- Capture workflow evidence links (GitHub Actions run summary URLs).

### 0.2 Human UI execution (gated)
These steps require a Richpanel workspace admin and should only be executed after doc-only prep is complete:
- Create Teams + Tags
- Create/modify Automation rules (HTTP Target trigger + assignment rules)
- Create/verify the Richpanel HTTP Target that calls middleware ingress

---

## 1) Doc-only prep (NO Richpanel UI changes)

### 1.1 Choose environment + stack name
- **Environment**: `dev`, `staging`, or `prod`
- **CloudFormation stack name** (CDK default): `RichpanelMiddleware-<env>` (example: `RichpanelMiddleware-dev`)
- **Ingress route (shipped)**: `POST /webhook`
- **Ingress auth header (shipped)**: `x-richpanel-webhook-token` (case-insensitive HTTP header; set this in Richpanel)

### 1.2 PowerShell-safe: fetch ingress endpoint URL (CloudFormation output)

```powershell
$EnvName = "dev"  # dev | staging | prod
$StackName = "RichpanelMiddleware-" + $EnvName

# CloudFormation output: IngressEndpointUrl (base URL)
$IngressBase = aws cloudformation describe-stacks `
  --stack-name $StackName `
  --query "Stacks[0].Outputs[?OutputKey=='IngressEndpointUrl'].OutputValue | [0]" `
  --output text

# Richpanel HTTP Target URL (shipped route)
$IngressWebhookUrl = "$IngressBase/webhook"
$IngressWebhookUrl
```

### 1.3 PowerShell-safe: fetch secrets namespace (CloudFormation output)

```powershell
$EnvName = "dev"  # dev | staging | prod
$StackName = "RichpanelMiddleware-" + $EnvName

$SecretsNamespace = aws cloudformation describe-stacks `
  --stack-name $StackName `
  --query "Stacks[0].Outputs[?OutputKey=='SecretsNamespace'].OutputValue | [0]" `
  --output text

$SecretsNamespace
```

### 1.4 Canonical secret IDs (defaults; DO NOT put values in this doc)
These are the shipped default secret names used by middleware clients. Do not change naming unless you also update code.

- **Richpanel**
  - Webhook token (ingress shared secret): `rp-mw/<env>/richpanel/webhook_token`
  - API key (Richpanel API): `rp-mw/<env>/richpanel/api_key`
- **OpenAI**
  - API key: `rp-mw/<env>/openai/api_key`
- **Shopify (Admin API token)**
  - Canonical: `rp-mw/<env>/shopify/admin_api_token`
  - Legacy fallback (supported for compatibility): `rp-mw/<env>/shopify/access_token`
- **ShipStation**
  - API key: `rp-mw/<env>/shipstation/api_key`
  - API secret: `rp-mw/<env>/shipstation/api_secret`
  - API base URL (optional; defaults to vendor base if absent): `rp-mw/<env>/shipstation/api_base`

> `<env>` is `dev`, `staging`, or `prod`.

### 1.5 Gating flags / operator levers (align with shipped terminology)
Middleware behavior is intentionally gated so we can deploy safely before enabling outbound side effects:

- **Kill switches (runtime, SSM Parameter Store)**
  - `safe_mode`: when `true`, forces route-only and disables automation.
  - `automation_enabled`: when `false`, disables automated replies/side effects.
- **Outbound network gates (Lambda env vars)**
  - `OPENAI_OUTBOUND_ENABLED`: must be `true` to allow OpenAI outbound calls.
  - `RICHPANEL_OUTBOUND_ENABLED`: must be `true` to allow Richpanel API outbound calls.

> Recommended early rollout posture: keep `safe_mode=true` and `automation_enabled=false` until ingress and routing are verified. Only enable outbound flags intentionally (one vendor at a time) once wiring and monitoring are confirmed.

### 1.6 Where to find workflow evidence (Actions run summary)
Capture evidence links after you run automation workflows (seed secrets / deploy / CI):

- **GitHub UI**: open the relevant GitHub Actions run → copy the run URL → attach to ticket/PR notes.
- **PowerShell-safe via `gh` (URLs only; no secrets):**

```powershell
# Example: get the most recent run URL for a workflow file (adjust name as needed).
$Workflow = "seed-secrets.yml"  # or deploy-dev.yml, deploy-staging.yml, etc.
$RunId = gh run list --workflow $Workflow --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run view $RunId --json url,conclusion --jq '.url'
```

---

## 2) Human UI execution (gated) — Richpanel admin steps

### 2.1 Guiding principles (v1)
1) **Inbound-only triggers**: middleware should run only on customer messages (not agent replies).
2) **No auto-close**: middleware will never close; Richpanel should not auto-close customer issues in v1 unless explicitly approved (spam/system-notifs only).
3) **Tag-driven routing**: middleware applies `route-*` tags; Richpanel assignment rules map tags → Teams.
4) **Durable-first**: HTTP Target handler must persist/enqueue and ACK fast. Do not assume Richpanel retries.
5) **Minimum PII**: HTTP Target payload includes only what is needed; logs must redact.
6) **Avoid rule conflicts**: your workspace contains multiple rules with “Skip all subsequent rules” and “Reassign even if already assigned”. Our trigger and routing design must not be blocked or overridden by these.

---

### 2.2 Configuration change summary (what to change)

| Area | Change | Why | Owner |
|---|---|---|---|
| Teams | Create **Chargebacks / Disputes** Team | High-risk workflow needs dedicated queue | Support Ops |
| Tags | Create `route-*` tags (11) + `mw-*` control tags | Safe routing + reconciliation visibility | Support Ops + Eng |
| Automations | Add `Middleware — Inbound Trigger` rule (HTTP Target) | Guarantees middleware receives inbound events | Support Ops |
| Automations | Add assignment rules: `route-*` tag → assign to Team | Keeps routing logic visible and adjustable in Richpanel | Support Ops |
| Automations | Disable/replace current **chargeback auto-close** rules | Conflicts with “auto-close only for whitelisted, deflection-safe templates” + chargeback queue requirement | Support Ops |
| Automations | De-conflict legacy auto-assign rules | Prevent “routing fights” overriding middleware routing | Support Ops |
| API Keys | Create per-environment API keys (dev/stage/prod) | Isolation + blast-radius control | Eng |
| Saved Views | Optional: views per `route-*` tag | Visibility + auditing | Support Ops |

---

### 2.3 Teams (target state)

### 2.1 Create: Chargebacks / Disputes
- **Name:** `Chargebacks / Disputes`
- **Purpose:** handle disputes/chargebacks and payment processor notifications
- **Policy:** Tier 0 — *never auto-reply; auto-close only for whitelisted, deflection-safe templates*; human-only
- **Membership:** restricted to staff who handle payment disputes

---

### 2.4 Tags (target state)

### 3.1 Naming conventions
- `route-*` = routing destination decision (set by middleware)
- `mw-*` = middleware control / bookkeeping

Do **not** overload existing “topic tags” (e.g., `refund-request`) for routing; this reduces accidental triggers from legacy rules.

### 3.2 Required routing tags (v1)
Create these tags exactly (hyphenated; lowercase):

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

### 3.3 Required middleware control tags (v1)
Create these tags:

- `mw-processed` — middleware successfully ingested/handled the inbound event (or at least enqueued it durably)
- `mw-routing-applied` — middleware applied a routing decision (route tag set)
- `mw-auto-replied` — middleware sent an automated customer-facing reply
- `mw-escalated-human` — middleware forced a human handoff (Tier 0 / Tier 1 handoff)

> Note: idempotency is enforced in middleware via DynamoDB; tags are primarily for visibility and reconciliation sweeps.

---

### 2.5 Automation rules (target state)

### 4.1 New: Middleware inbound trigger rule (required)
Create a rule:

- **Name:** `Middleware — Inbound Trigger`
- **Trigger:**
  - “A customer starts a new conversation”
  - “Immediately after a customer sends a new message”
- **Action:** “Trigger HTTP Target” (middleware endpoint)
- **Toggles:**
  - **Skip all subsequent rules = OFF** (must be OFF)

#### 4.1.1 Preferred placement (best-suggested)
Place this rule in **Tagging Rules** (or whichever automation category supports HTTP Targets + customer message triggers) and move it to the **top of that category’s list**.

Why:
- your Assignment Rules often use “Skip all subsequent rules”, which can block later Assignment Rules.
- placing the trigger in Tagging Rules reduces the chance it is blocked by Assignment Rules.

#### 4.1.2 Fallback placement
If HTTP Target actions are only available in Assignment Rules:
- place it as the **first Assignment Rule**.

#### 4.1.3 Worst-case fallback
If ordering cannot be controlled reliably:
- add HTTP Target actions to the major channel-specific rules (LiveChat / Email / Social / TikTok)
- rely on middleware idempotency to safely dedupe duplicates

### 4.2 Assignment rules: routing tag → team (required)
Create a rule per routing tag:

- **Trigger:** “When a tag is added” (or equivalent)
- **Condition:** tag equals `route-…`
- **Action:** assign the conversation to the corresponding Team
- **Toggles:** if available, enable “skip subsequent rules when matched” to avoid multiple assignments.

Mapping:

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

### 4.3 De-conflict legacy assignment rules (required to prevent routing fights)
Several existing rules appear to:
- trigger on every new customer message
- reassign even if already assigned
- skip subsequent rules

If left unchanged, they can override middleware routing on later messages.

**Recommended mitigation (best-practice)**
For each “legacy auto-assign” rule that covers channels onboarded to middleware routing:
1) Add condition guard: **Tags does not contain `mw-routing-applied`** (or equivalent)
2) Disable **Reassign even if already assigned** (recommended)

**High-priority legacy rules to update**
- `[Auto Assign] Customer Support` (assigns to Email Support Team)
- `[Auto Assign] Tech Support (defective keywords)`
- `[Auto Assign] Social Media Team`
- `Auto Assign LiveChat`
- `[Auto Assign] TikTok`

If Richpanel cannot express “tag NOT present”:
- at minimum, turn OFF “reassign even if already assigned” so the rule cannot override later.

### 4.4 Disable/replace chargeback auto-close rules (required)
From the current snapshot, these rules auto-close based on subject matching:
- `Chargeback - Auto Close`
- `Auto close- Chargeback`
- `Payout/Recurring/Chargeback - Auto Close`

**v1 change:** Disable these rules, or replace the “close conversation” action with:
- apply `route-chargebacks-disputes`
- apply `mw-escalated-human`

**Do not** auto-close chargebacks in v1.

---

### 2.6 HTTP Target (Richpanel → Middleware)

#### 2.6.1 Destination (shipped)
POST to the deployed API Gateway **ingress webhook route**:
- URL: `<IngressEndpointUrl>/webhook`

> Use the doc-only prep step to retrieve `IngressEndpointUrl` from CloudFormation, then append `/webhook`.

#### 2.6.2 Required security header (anti-spoof) (shipped)
Add a static shared-secret header in Richpanel HTTP Target configuration:
- `x-richpanel-webhook-token: <secret per environment>`

Store the secret in AWS Secrets Manager; rotate if leaked.

#### 2.6.3 Payload strategy (v1)
**Recommended (v1): minimal payload**

Rationale:
- safest against JSON template escaping issues
- minimizes PII exposure

```json
{ "ticket_id": "{{ticket.id}}", "ticket_url": "{{ticket.url}}", "trigger": "customer_message" }
```

**Optional optimization (only after verification): include latest message text**

If the tenant’s JSON template escapes values correctly (test with quotes + newlines):
```json
{ "ticket_id": "{{ticket.id}}", "ticket_url": "{{ticket.url}}", "message": "{{ticket.lastMessage.text}}", "trigger": "customer_message" }
```

**Never** inline base64 attachments.

---

### 2.7 Rollout stages (recommended)

#### Stage 0 — Shadow (no customer impact)
- Middleware ingests events + logs predictions
- No tags applied (or apply `mw-shadow` only)

#### Stage 1 — Tag-only
- Middleware applies `route-*` + `mw-routing-applied`
- Richpanel legacy assignment rules are guarded (or reviewed) to prevent routing fights
- Ops reviews routing accuracy via views

#### Stage 2 — Full routing
- Enable assignment rules: `route-*` → Team
- Middleware allowed to send Tier 1/2 auto-replies (FAQ order status only)

#### Stage 3 — Optimization
- Calibrate confidence thresholds
- Expand FAQ automation set carefully

---

### 2.8 Acceptance checklist (definition of done for config)

#### 2.8.1 Security & stability
- [ ] HTTP Target rejects spoof requests (middleware returns 401 if missing/incorrect `x-richpanel-webhook-token`)
- [ ] Middleware ACKs in < 500ms p95 (ingress path)
- [ ] Duplicate deliveries do not cause duplicate tags or replies

#### 2.8.2 Trigger reliability
- [ ] `Middleware — Inbound Trigger` exists and has **Skip all subsequent rules = OFF**
- [ ] Preferred: trigger lives in **Tagging Rules** (or equivalent) and is at the top of that category
- [ ] Fallback: if in Assignment Rules, it is the first rule

#### 2.8.3 Routing correctness
- [ ] Adding `route-*` tag triggers correct team assignment
- [ ] Legacy rules do not override middleware routing (no routing fights)
- [ ] Chargeback subjects route to Chargebacks / Disputes team (and do not auto-close)

#### 2.8.4 Visibility
- [ ] Saved views exist for `route-*` tags (optional but recommended)
- [ ] `mw-*` tags present for debugging in a sample ticket

---

## 3) UI execution checklist (human follow-along; no secrets)

### 3.1 Preflight (must be true before touching Richpanel UI)
- [ ] You know the target **environment** (`dev` / `staging` / `prod`).
- [ ] CloudFormation stack `RichpanelMiddleware-<env>` exists.
- [ ] You retrieved `<IngressEndpointUrl>/webhook` from CloudFormation outputs.
- [ ] You retrieved `SecretsNamespace` from CloudFormation outputs.
- [ ] Secrets exist (IDs only; do not paste values):
  - [ ] `rp-mw/<env>/richpanel/webhook_token`
  - [ ] `rp-mw/<env>/richpanel/api_key`
  - [ ] `rp-mw/<env>/openai/api_key` (only required before enabling OpenAI outbound)
  - [ ] `rp-mw/<env>/shopify/admin_api_token` (optional; only if Shopify fallback is used)
  - [ ] `rp-mw/<env>/shipstation/api_key` / `api_secret` (optional; only if ShipStation is used)

### 3.2 Richpanel UI changes (execute in order; stop if anything is unclear)
- [ ] Create Team: `Chargebacks / Disputes`
- [ ] Create required tags:
  - [ ] All `route-*` tags (11)
  - [ ] All `mw-*` tags
- [ ] Create automation rule: `Middleware — Inbound Trigger`
  - [ ] Customer message triggers only
  - [ ] Action: HTTP Target → `<IngressEndpointUrl>/webhook`
  - [ ] Header: `x-richpanel-webhook-token: <value from Secrets Manager rp-mw/<env>/richpanel/webhook_token>`
  - [ ] **Skip all subsequent rules = OFF**
- [ ] Create assignment rules: `route-*` → Team mapping
- [ ] Guard/de-conflict legacy auto-assign rules to prevent “routing fights”
- [ ] Disable/replace chargeback auto-close rules (do not auto-close in v1)

### 3.3 Post-change verification (minimal)
- [ ] Send a test customer message; verify the HTTP Target fires.
- [ ] Verify middleware ingress returns `200 accepted` (CloudWatch logs for `rp-mw-<env>-ingress` show `ingress.accepted`).
- [ ] Verify the conversation receives `mw-processed` and (in Stage 1+) `mw-routing-applied` / `route-*` tags as expected.
