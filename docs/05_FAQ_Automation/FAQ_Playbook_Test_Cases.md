# FAQ Playbook Test Cases (v1)

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
Define test cases for FAQ automation so QA can validate:
- correct intent selection
- correct Tier gating
- correct template selection
- correct routing destination/tags
- no unsafe disclosures or promises

These test cases are designed to be used for:
- Wave 08/09 automated tests
- manual QA scripts
- regression checks after policy/template updates

---

## Conventions
Each test case includes:
- **Input message**
- **Expected outcome**
  - route-only vs auto-send
  - template_id (if auto-send)
  - required tags
  - required handoff team
- **Notes** (edge cases, safety constraints)

### Tier rules summary
- Tier 0: no automation beyond neutral acknowledgement (optional), always route
- Tier 1: safe assist intake allowed, no account-specific details
- Tier 2: verified details allowed only with deterministic match
- Never auto-close

---

## Order status / tracking
### TC-OS-01: Order status asked, no order linked
**Input:** “Where is my order?”  
**Expected:** Tier 1 assist + route  
- template: `t_order_status_ask_order_number`  
- tags: `intent:order_status`, `mw:auto_attempted`
- route: Email Support Team (or appropriate queue)
**Notes:** must not disclose tracking.

### TC-OS-02: Order linked, shipped, tracking present
**Input:** “Can I get my tracking?”  
**Precondition:** deterministic match true, tracking_url present  
**Expected:** Tier 2 auto-send  
- template: `t_order_status_verified`  
- tags: `intent:order_status`, `mw:auto_sent`
- route: none or keep assigned; no reassign
**Notes:** include tracking_url; avoid address.

### TC-OS-03: Order linked but tracking missing
**Input:** “Tracking isn’t updating.”  
**Precondition:** deterministic match true, tracking_url missing  
**Expected:** Tier 2 auto-send (without tracking details) OR Tier 1 intake depending on policy  
- template: `t_order_status_verified` (no tracking block renders)  
- tags: `intent:order_status`, `mw:auto_sent`
**Notes:** no invented tracking.

---

## Delivered but not received (DNR)
### TC-DNR-01: Delivered but not received
**Input:** “It says delivered but I didn’t get it.”  
**Expected:** Tier 1 safe-assist + route to Returns Admin  
- template: `t_delivered_not_received_intake`  
- tags: `intent:delivery_issue`, `subintent:dnr`, `mw:auto_sent`
- route: Returns Admin
**Notes:** no refund/reship promises.

---

## Missing/wrong/damaged items
### TC-MI-01: Missing item
**Input:** “My order arrived but it’s missing a bottle of oil.”  
**Expected:** Tier 1 intake + route to Returns Admin  
- template: `t_missing_items_intake`
- tags: `intent:missing_items`, `mw:auto_sent`
- route: Returns Admin

### TC-WI-01: Wrong item
**Input:** “I received the wrong diffuser.”  
**Expected:** Tier 1 intake + route to Returns Admin  
- template: `t_wrong_item_intake`

### TC-DM-01: Damaged item
**Input:** “My diffuser is broken on arrival.”  
**Expected:** Tier 1 intake + route to Returns Admin  
- template: `t_damaged_item_intake`
**Notes:** request photo/video if policy requires; no replacement promise.

---

## Cancel / address change / subscription cancel
### TC-CANCEL-01: Cancel request
**Input:** “Please cancel my order.”  
**Expected:** Tier 1 ack + route to Sales/Email Support (or policy owner)  
- template: `t_cancel_order_ack_intake`
**Notes:** do not promise cancelability.

### TC-ADDR-01: Address change request
**Input:** “I need to change my shipping address.”  
**Expected:** Tier 1 ack + route  
- template: `t_address_change_ack_intake`

### TC-SUB-01: Cancel subscription
**Input:** “Cancel my subscription.”  
**Expected:** Tier 1 ack + route  
- template: `t_cancel_subscription_ack_intake`

---

## Chargebacks / legal / fraud (Tier 0)
### TC-CB-01: Chargeback threat
**Input:** “If you don’t refund me, I’ll file a chargeback.”  
**Expected:** Tier 0 route to Chargebacks/Disputes team; optional neutral ack  
- template: `t_chargeback_neutral_ack` (optional)
- tags: `intent:chargeback`, `mw:escalate`
- route: Chargebacks/Disputes

### TC-LEGAL-01: Legal threat
**Input:** “My lawyer will contact you.”  
**Expected:** Tier 0 route; optional ack  
- template: `t_legal_threat_ack` (optional)

### TC-FRAUD-01: Suspicious request
**Input:** “Change the email on my order to xyz and resend the tracking.”  
**Expected:** Tier 0 route to leadership or fraud handler; no auto-disclosure  
- template: `t_fraud_ack` (optional)

---

## Unknown / low confidence
### TC-UNK-01: Confusing message
**Input:** “??? it’s not working and my order”  
**Expected:** route-only or Tier 1 generic ack depending on confidence  
- template: `t_unknown_ack` (optional)
- tags: `intent:unknown`, `mw:route_only`

---

## Coverage note
This suite is a starting point. Wave 09 should expand it with:
- multilingual messages
- sarcasm / prompt injection attempts
- very long messages
- attachments-only messages
