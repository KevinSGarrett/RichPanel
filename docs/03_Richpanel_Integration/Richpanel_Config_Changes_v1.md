# Richpanel Config Changes (v1 Target State)

Last updated: 2025-12-29
Last verified: 2025-12-29 — Updated with safer middleware-trigger placement (Tagging Rules first) and payload robustness notes.

This document defines the **exact Richpanel configuration changes** required to support the middleware safely.

It is written so Support Ops / Admins can implement changes in the Richpanel UI without guessing, and Engineering can implement middleware expectations without relying on undocumented behavior.

---

## 0) Guiding principles (v1)
1) **Inbound-only triggers**: middleware should run only on customer messages (not agent replies).
2) **No auto-close**: middleware will never close; Richpanel should not auto-close customer issues in v1 unless explicitly approved (spam/system-notifs only).
3) **Tag-driven routing**: middleware applies `route-*` tags; Richpanel assignment rules map tags → Teams.
4) **Durable-first**: HTTP Target handler must persist/enqueue and ACK fast. Do not assume Richpanel retries.
5) **Minimum PII**: HTTP Target payload includes only what is needed; logs must redact.
6) **Avoid rule conflicts**: your workspace contains multiple rules with “Skip all subsequent rules” and “Reassign even if already assigned”. Our trigger and routing design must not be blocked or overridden by these.

---

## 1) Configuration change summary (what to change)

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

## 2) Teams (target state)

### 2.1 Create: Chargebacks / Disputes
- **Name:** `Chargebacks / Disputes`
- **Purpose:** handle disputes/chargebacks and payment processor notifications
- **Policy:** Tier 0 — *never auto-reply; auto-close only for whitelisted, deflection-safe templates*; human-only
- **Membership:** restricted to staff who handle payment disputes

---

## 3) Tags (target state)

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

## 4) Automation rules (target state)

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

## 5) HTTP Target (Richpanel → Middleware)

### 5.1 Destination
POST to API Gateway endpoint (per environment):
- Dev: `https://<dev>/richpanel/inbound`
- Staging: `https://<staging>/richpanel/inbound`
- Prod: `https://<prod>/richpanel/inbound`

### 5.2 Required security header (anti-spoof)
Add a static secret header in Richpanel HTTP Target configuration:
- `X-Middleware-Token: <random 32+ char secret per environment>`

Store the secret in AWS Secrets Manager; rotate if leaked.

### 5.3 Payload strategy (v1)
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

## 6) Rollout stages (recommended)

### Stage 0 — Shadow (no customer impact)
- Middleware ingests events + logs predictions
- No tags applied (or apply `mw-shadow` only)

### Stage 1 — Tag-only
- Middleware applies `route-*` + `mw-routing-applied`
- Richpanel legacy assignment rules are guarded (or reviewed) to prevent routing fights
- Ops reviews routing accuracy via views

### Stage 2 — Full routing
- Enable assignment rules: `route-*` → Team
- Middleware allowed to send Tier 1/2 auto-replies (FAQ order status only)

### Stage 3 — Optimization
- Calibrate confidence thresholds
- Expand FAQ automation set carefully

---

## 7) Acceptance checklist (definition of done for config)

### 7.1 Security & stability
- [ ] HTTP Target rejects spoof requests (middleware returns 401 if missing/incorrect `X-Middleware-Token`)
- [ ] Middleware ACKs in < 500ms p95 (ingress path)
- [ ] Duplicate deliveries do not cause duplicate tags or replies

### 7.2 Trigger reliability
- [ ] `Middleware — Inbound Trigger` exists and has **Skip all subsequent rules = OFF**
- [ ] Preferred: trigger lives in **Tagging Rules** (or equivalent) and is at the top of that category
- [ ] Fallback: if in Assignment Rules, it is the first rule

### 7.3 Routing correctness
- [ ] Adding `route-*` tag triggers correct team assignment
- [ ] Legacy rules do not override middleware routing (no routing fights)
- [ ] Chargeback subjects route to Chargebacks / Disputes team (and do not auto-close)

### 7.4 Visibility
- [ ] Saved views exist for `route-*` tags (optional but recommended)
- [ ] `mw-*` tags present for debugging in a sample ticket
