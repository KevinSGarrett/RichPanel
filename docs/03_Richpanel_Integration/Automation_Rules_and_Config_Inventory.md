# Automation Rules and Configuration Inventory

Last updated: 2025-12-22
Last verified: 2025-12-22 — Expanded inventory with “skip subsequent rules” + “reassign” flags and documented routing-fight risks.

We inventory current Richpanel configuration from:
`RichPanel_Docs_Phase0/04_SETUP_CONFIGURATION/current-setup/`

Goals:
- Avoid automation loops and unexpected re-triggering.
- Ensure the middleware trigger runs reliably across channels.
- Ensure correct triggers (inbound-only for middleware).
- Understand existing rules so middleware does not “fight” the platform.

> This inventory will continue expanding. This update focuses on items that materially affect early rollout correctness.

---

## 1) Snapshot sources used
From your provided documentation library:
- Automations:
  - `rp.current-setup.automation.assignment-rules.list`
  - `rp.current-setup.automation.tagging-rules.list`
  - Specific rules (auto-assign, acknowledgements, chargeback auto-close, etc.)
- Tags:
  - `rp.current-setup.tags.active-list`
  - `rp.current-setup.tags.archived-list` (exists; many archived tags)
- Macros:
  - `rp.current-setup.macros.index` (+ individual macro docs)

---

## 2) High-impact behaviors observed in current setup

### 2.1 Many assignment rules do BOTH of these
- **Reassign even if conversation is already assigned = ON**
- **Skip all subsequent rules = ON**
- Trigger on “customer starts new conversation” and/or “immediately after customer sends new message”

**Implication**
- If our middleware trigger is implemented as a later **Assignment Rule**, it may never run.
- If middleware routing is applied, these rules may still re-run on later customer messages and override the routing (routing fights).

**Mitigation requirements (best-suggested)**
- Prefer placing middleware trigger in **Tagging Rules** (top of that list) with skip OFF.
- Gate legacy assignment rules behind `mw-routing-applied` (if condition supported) and/or turn “reassign” OFF for onboarded channels.

---

## 3) Inventory: key existing rules (from snapshot)

> Names below reflect snapshot docs; exact names should be confirmed in your tenant UI.

| Rule | Trigger | Key flags | What it does today | Risk with middleware |
|---|---|---|---|---|
| **[Auto Assign] Customer Support** | New conversation + new customer message | Reassign=ON; Skip=ON | Assigns to **Email Support Team** (default) | Can block middleware trigger if implemented as later Assignment Rule; can override routing on later messages |
| **[Auto Assign] Tech Support (defective keywords)** | New conversation + new customer message | Reassign=ON; Skip=ON | Keyword routes to **Technical Support Team** | Same “block + override” risks |
| **[Auto Assign] Social Media Team** | New conversation | Reassign=ON; Skip=ON | Assigns to **Social Media Team** | Can block later Assignment Rules |
| **[Auto Assign] TikTok** | New conversation | Reassign=ON; Skip=ON | Assigns to **TikTok Support** | Can block later Assignment Rules |
| **Auto Assign LiveChat** | New conversation | Reassign=ON; Skip=ON | Assigns Messenger channel to **LiveChat Support** | Can block later Assignment Rules |
| **Acknowledgment response** | New conversation | (unknown) | Sends an acknowledgment message to customer | Generally OK, but we must avoid loops (trigger on customer-only) |
| **Chargeback auto-close rules** | Subject contains chargeback patterns | N/A | **Closes** conversation automatically | Conflicts with policy (“never auto-close”) |

Additional tag-triggered rules exist (refund/return, VIP, high priority) that assign to individuals when specific tags are applied.
Those are not directly dangerous if middleware never applies those tags.

---

## 4) Required change: remove/disable chargeback auto-close patterns
We have a hard constraint:
- ✅ Middleware must **never auto-close** tickets.

However, your current Richpanel setup contains auto-close rules for chargebacks:
- subject contains “Chargeback for order” → close
- subject contains “a chargeback was opened” → close
- recurring payout chargeback subject pattern → close

**Required change for this project**
- Disable these auto-close rules and replace with:
  - apply routing tag `route-chargebacks-disputes`
  - route to the **Chargebacks / Disputes** team/queue
  - apply `mw-escalated-human`
  - (optional) internal note, but **do not close**

---

## 5) Required change: ensure middleware trigger runs for ALL inbound tickets

### 5.1 New rule: `Middleware — Inbound Trigger`
**Create a new automation rule** that:
- triggers on:
  - “A customer starts a new conversation”
  - “Immediately after a customer sends a new message”
- action:
  - “Trigger HTTP Target” (our middleware endpoint)
- flags:
  - **Skip all subsequent rules = OFF**

**Preferred placement**
- Implement this as a **Tagging Rule** (top of list).

**Fallback placement**
- If HTTP Target actions can only be used in Assignment Rules, this rule must be the **first Assignment Rule**.

### 5.2 Payload recommendation
**Plan-default:** minimal payload (robust)
- `ticket_id` + `ticket_url` + static trigger string

Optional optimization:
- include `ticket.lastMessage.text` only after confirming JSON-escaping in your tenant.

---

## 6) Routing-fight mitigation plan (legacy assignment rules)
We need the system to behave sensibly in two modes:
- Middleware ON (applies `route-*` tags and `mw-routing-applied`)
- Middleware OFF / degraded (legacy routing still provides a default)

**Recommended approach**
- Update legacy auto-assign rules so they do NOT override middleware routing:
  1) Add condition: `Tags does not contain mw-routing-applied` (or equivalent)
  2) Turn OFF “Reassign even if already assigned” for rules covering onboarded channels (optional but recommended)

If Richpanel cannot express “tag NOT present”:
- we can still mitigate by:
  - turning OFF reassign
  - treating legacy rules as “initial assignment only”

---

## 7) Open items (confirm in your tenant)
- Can a **Tagging Rule** run on “customer sends message” and trigger an HTTP Target?
- Can HTTP Targets add custom headers (`X-Middleware-Token`)?
- Does “Skip all subsequent rules” apply only within the current category?
- Does the JSON template safely escape `{{ticket.lastMessage.text}}`? (optional optimization)
