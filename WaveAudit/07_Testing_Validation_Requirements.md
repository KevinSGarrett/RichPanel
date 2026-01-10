# Testing and Validation Requirements - Wave Audit Findings

**Purpose:** Comprehensive testing requirements to validate alignment with core workflows  
**Date:** 2026-01-09  
**Status:** Testing specification for gaps identified in audit

---

## Overview

This document specifies all testing required to validate that the system behaves according to the core workflows described in Examples A, B, and C.

**Testing Categories:**
1. Order status automation (with tracking)
2. Order status automation (without tracking, ETA calculation)
3. Auto-close and reopen behavior
4. Ticket routing via OpenAI
5. FAQ framework extensibility
6. Idempotency and deduplication

---

## Test Suite 1: Order Status with Tracking (Example A - Path A1-A3)

### TC-OS-001: Order with Tracking Number - Happy Path

**Objective:** Verify system correctly provides tracking information and auto-closes ticket

**Prerequisites:**
- Shopify order exists with tracking number
- Order linked to Richpanel conversation
- Middleware automation enabled

**Test Steps:**
1. Create test customer "John Doe" with email john@example.com
2. Create Shopify order #123554343 with:
   - Customer: john@example.com
   - Status: Fulfilled
   - Tracking number: 1Z999AA1234567890
   - Tracking URL: https://ups.com/track/1Z999AA1234567890
   - Carrier: UPS
3. Link order to Richpanel conversation (if not auto-linked)
4. Send customer message via Richpanel: "Where is my order?"
5. Wait for middleware processing (max 60 seconds)

**Expected Results:**
- ✅ Middleware classifies intent as `order_status_tracking`
- ✅ Middleware detects tracking number exists
- ✅ Template `t_order_status_verified` is selected
- ✅ Reply includes:
  - Personalized greeting (if first_name available)
  - Order ID #123554343
  - Tracking company: UPS
  - Tracking number: 1Z999AA1234567890
  - Tracking URL: https://ups.com/track/1Z999AA1234567890
- ✅ Ticket status set to "Resolved"
- ✅ Tags applied: `mw-auto-replied`, `mw-intent-order-status`, `mw:auto_closed`
- ✅ Only ONE reply sent (idempotency verified)

**Evidence to Capture:**
- Screenshot of Richpanel conversation showing automated reply
- Middleware logs showing intent classification and template selection
- DynamoDB idempotency table entry
- CloudWatch metrics for auto-reply count

---

### TC-OS-002: Multiple Orders - Should Ask for Order Number

**Objective:** Verify system does NOT guess when customer has multiple orders

**Prerequisites:**
- Customer has 2+ orders in Shopify
- Richpanel conversation not linked to specific order

**Test Steps:**
1. Create customer with email jane@example.com
2. Create two Shopify orders:
   - Order #111111 (Standard shipping, no tracking)
   - Order #222222 (Standard shipping, no tracking)
3. Send message: "Where is my order?"

**Expected Results:**
- ✅ Intent classified as `order_status_tracking`
- ✅ System detects multiple possible orders
- ✅ Template `t_order_status_ask_order_number` sent
- ✅ Message asks for order number + email/phone
- ✅ Ticket routed to Email Support Team
- ✅ Ticket NOT auto-closed (remains open)
- ✅ Tags applied: `mw-intent-order-status`, `mw-order-lookup-needed`

---

## Test Suite 2: Order Status without Tracking (Example A - Path B1-B3)

### TC-ETA-001: Standard Shipping, Within SLA Window

**Objective:** Verify ETA calculation and auto-close for orders without tracking

**Prerequisites:**
- Shopify order with Standard shipping (3-5 business days)
- Order placed Monday
- No tracking number yet
- Customer inquires on Wednesday

**Test Steps:**
1. Create order #999888777:
   - Created: Monday, Jan 6, 2026, 10:00 AM
   - Shipping method: "Standard Shipping (3-5 business days)"
   - Status: Unfulfilled
   - Tracking: None
2. Set system time to: Wednesday, Jan 8, 2026, 2:00 PM (2 business days later)
3. Send message: "Has my order shipped yet?"

**Expected Results:**
- ✅ Intent: `order_status_tracking`
- ✅ No tracking detected
- ✅ Shipping method normalized to bucket: "Standard" (3-5 BD window)
- ✅ Business days elapsed: 2
- ✅ Remaining window calculated: 1-3 business days
- ✅ Template: `t_order_eta_no_tracking_verified`
- ✅ Reply includes:
  - "Your order should arrive in **1-3 business days**"
  - Order ID
  - Shipping bucket mentioned
- ✅ Ticket auto-closed (Resolved)
- ✅ Tags: `mw-auto-replied`, `mw:auto_closed`, `mw:deflected`

**Evidence:**
- Delivery estimate calculation in logs: `{"elapsed_business_days": 2, "remaining_min_days": 1, "remaining_max_days": 3}`
- Template render output
- Ticket status change to Resolved

---

### TC-ETA-002: Standard Shipping, LATE (Outside SLA)

**Objective:** Verify system does NOT auto-close when order is late

**Prerequisites:**
- Order placed Monday
- Standard shipping (3-5 BD)
- Customer inquires on following Tuesday (6 business days later)

**Test Steps:**
1. Create order #888777666:
   - Created: Monday, Jan 6, 2026
   - Shipping method: "Standard"
   - No tracking
2. Set system time to: Tuesday, Jan 14, 2026 (6 business days elapsed)
3. Send message: "Where is my order? It's been over a week!"

**Expected Results:**
- ✅ Intent: `order_status_tracking`
- ✅ Business days elapsed: 6
- ✅ SLA window: 3-5 days (order is LATE)
- ✅ Template: `t_shipping_delay_verified` (NOT the auto-close ETA template)
- ✅ Reply acknowledges order not shipped yet
- ✅ Ticket NOT auto-closed (remains Open)
- ✅ Routed to Email Support Team for human review
- ✅ Tags: `mw-intent-shipping-delay`, `mw-route-only`

**Evidence:**
- Delivery estimate shows `"is_late": true`
- Ticket status remains Open
- Assignment to Email Support Team confirmed

---

### TC-ETA-003: Business Day Calculation Edge Cases

**Objective:** Verify business day math excludes weekends

**Test Cases:**

| Order Date | Inquiry Date | Shipping | Expected Elapsed BD | Expected Remaining |
|---|---|---|---|---|
| Friday Jan 3 | Monday Jan 6 | Standard (3-5) | 1 | 2-4 BD |
| Friday Jan 3 | Tuesday Jan 7 | Standard (3-5) | 2 | 1-3 BD |
| Monday Jan 6 | Friday Jan 10 | Priority (1) | 4 | LATE (route to human) |
| Wednesday Jan 8 | Monday Jan 13 | Standard (3-5) | 3 | 0-2 BD |

**For each:**
1. Create order with specified date/method
2. Send inquiry on specified date
3. Verify business day calculation matches expected
4. Verify remaining window matches expected
5. Verify template selection correct (ETA vs delay)

---

## Test Suite 3: Auto-Close and Reopen Behavior (Example A/B - Step 4)

### TC-REOPEN-001: Customer Replies to Auto-Closed Ticket

**Objective:** Verify customer reply reopens ticket and routes to Email Support Team

**Prerequisites:**
- Order status auto-reply sent
- Ticket auto-closed (Resolved status)
- Tag `mw-auto-replied` present

**Test Steps:**
1. Complete TC-ETA-001 (auto-close ticket with ETA message)
2. Verify ticket status is "Resolved"
3. Wait 5 minutes
4. Send customer reply: "Actually, I need it by Friday. Can you expedite shipping?"
5. Wait for webhook processing

**Expected Results:**
- ✅ Richpanel automatically changes ticket status from Resolved to Open
- ✅ Webhook fires to middleware
- ✅ Middleware detects reopened-after-auto-close scenario:
  - Has tag `mw-auto-replied`
  - Status changed from Resolved to Open
- ✅ Middleware adds tag `mw-reopened-after-auto-close`
- ✅ Middleware sets mode to "route_only" (no second automated reply)
- ✅ Richpanel automation rule triggers:
  - Ticket assigned to Email Support Team
- ✅ No second automated template sent
- ✅ Conversation history preserved (original auto-reply + customer reply both visible)

**Evidence:**
- Screenshot showing ticket reopened
- Middleware logs: `worker.reopened_after_auto_close` event
- No second auto-reply in conversation
- Assignment to Email Support Team confirmed

---

### TC-REOPEN-002: Multiple Reopens (Persistent Issue)

**Objective:** Verify escalation after customer reopens >2 times

**Test Steps:**
1. Auto-close ticket (first time)
2. Customer replies → ticket reopens → agent responds → agent resolves
3. Customer replies again → ticket reopens (2nd time) → agent responds → agent resolves
4. Customer replies third time → ticket reopens (3rd time)

**Expected Results:**
- ✅ After 3rd reopen:
  - Tag `mw-persistent-issue` added
  - Escalation rule triggers (if configured)
  - High priority set (optional)

---

### TC-REOPEN-003: Reply After >7 Days (Not a Reopen)

**Objective:** Verify old tickets are treated as new inquiries, not reopens

**Test Steps:**
1. Auto-close ticket on Jan 6
2. Wait until Jan 15 (9 days later)
3. Customer sends new message about same order

**Expected Results:**
- ✅ NOT classified as "reopened after auto-close"
- ✅ Treated as new inquiry
- ✅ May send automated reply if conditions met (normal automation flow)
- ✅ Tag `mw-reopened-after-auto-close` NOT added

---

## Test Suite 4: Ticket Routing via OpenAI (Example B)

### TC-ROUTE-001: Refund Request Routes to Correct Department

**Objective:** Verify OpenAI classifies intent and routes to Returns Admin

**Test Steps:**
1. Send message: "I need a refund for my order"
2. Wait for processing

**Expected Results:**
- ✅ LLM classifies intent as `refund_request`
- ✅ Routing decision: Returns Admin
- ✅ Tags applied: `mw-intent-refund`, `mw-routing-applied`
- ✅ Template: `t_refund_request_intake` (Tier 1 intake)
- ✅ Ticket routed to Returns Admin team
- ✅ Ticket NOT auto-closed (intake only)

---

### TC-ROUTE-002: Multi-Intent Message Routing

**Objective:** Verify routing priority when multiple intents detected

**Test Steps:**
1. Send message: "I need a refund and also want to know my order status"

**Expected Results:**
- ✅ LLM detects multiple intents
- ✅ Primary intent selected based on priority rules (refund likely primary)
- ✅ Routes to Returns Admin (refund handling takes precedence)
- ✅ Secondary intent tagged but not primary driver

---

### TC-ROUTE-003: Chargeback/Dispute (Tier 0 Escalation)

**Objective:** Verify high-risk intents never auto-reply

**Test Steps:**
1. Send message: "I'm filing a chargeback with my credit card company"

**Expected Results:**
- ✅ Intent: `chargeback_dispute`
- ✅ Tier 0 classification (escalation)
- ✅ NO automated template sent (route-only)
- ✅ Assigned to: Chargebacks / Disputes Team (or Leadership)
- ✅ Tags: `mw-intent-chargeback`, `mw-tier-0-escalation`
- ✅ Priority: High

---

## Test Suite 5: FAQ Framework Extensibility (Example C)

### TC-FAQ-001: Add New FAQ - Cancel Order (Walkthrough)

**Objective:** Validate that "How to Add New FAQ" guide works correctly

**Prerequisites:**
- "Cancel Order" template already exists (`t_cancel_order_ack_intake`)
- Intent already in taxonomy (`cancel_order`)

**Test Steps (Following WaveAudit/01_How_to_Add_New_FAQ.md):**

1. **Verify intent exists:**
   - Check `Intent_Taxonomy_and_Labeling_Guide.md` for `cancel_order`
   - ✅ Intent defined: YES

2. **Verify routing mapping:**
   - Check `Department_Routing_Spec.md` for cancel_order row
   - ✅ Mapped to: Email Support Team

3. **Verify template exists:**
   - Check `Templates_Library_v1.md` for `t_cancel_order_ack_intake`
   - ✅ Template exists: YES

4. **Test classification:**
   - Send message: "I want to cancel my order"
   - ✅ Intent classified as `cancel_order`
   - ✅ Template `t_cancel_order_ack_intake` sent
   - ✅ Routed to Email Support Team

5. **Verify NO auto-cancel action:**
   - ✅ Tier 1 only (intake message)
   - ✅ Asks for order number
   - ✅ Does NOT automatically cancel order (Tier 3 disabled)

**Evidence:**
- Intent classification correct
- Template rendered correctly
- Routing correct
- No auto-cancel action taken (safety preserved)

---

## Test Suite 6: Idempotency and Deduplication

### TC-DEDUP-001: Duplicate Webhook Delivery

**Objective:** Verify only one reply sent even if webhook delivered twice

**Test Steps:**
1. Send customer message: "Where is my order?"
2. Immediately send identical webhook payload again (simulate duplicate)
3. Wait for processing

**Expected Results:**
- ✅ First message processed normally
- ✅ Second message detected as duplicate
- ✅ Idempotency table entry exists
- ✅ Only ONE auto-reply sent to customer
- ✅ Logs show: `worker.duplicate_event` for second message
- ✅ No error, graceful skip

---

### TC-DEDUP-002: Rate Limiting (Multiple Messages Same Customer)

**Objective:** Verify cooldown prevents spam replies

**Test Steps:**
1. Send message: "Where is my order?" (auto-reply sent)
2. Wait 2 minutes
3. Send message: "Where is my order now?" (same ticket)
4. Wait 2 minutes
5. Send message: "Hello?" (same ticket)

**Expected Results:**
- ✅ First message: Auto-reply sent
- ✅ Second message (within cooldown): No auto-reply, tag `mw-auto-rate-limited`
- ✅ Third message (within cooldown): No auto-reply
- ✅ After cooldown expires (10+ minutes): May send new reply if conditions met

---

## Test Suite 7: Personalization and Templates

### TC-PERS-001: Template with All Variables Present

**Objective:** Verify template renders correctly with full data

**Test Data:**
- first_name: "Sarah"
- order_id: "#12345"
- tracking_number: "1Z999..."
- tracking_url: "https://..."
- tracking_company: "UPS"

**Expected Output:**
```
Hi Sarah — thanks for reaching out.

Here's the latest update for your order #12345:
• Status: Fulfilled

Tracking:
• UPS — 1Z999...
• https://...
```

---

### TC-PERS-002: Template with Missing Optional Variable

**Objective:** Verify template gracefully omits optional blocks

**Test Data:**
- first_name: NOT PROVIDED (missing)
- order_id: "#12345"
- tracking_number: "1Z999..."

**Expected Output:**
```
Thanks for reaching out.

Here's the latest update for your order #12345:
• Status: Fulfilled

Tracking:
• 1Z999...
• https://...
```

**Note:** "Hi Sarah" block omitted because first_name was missing.

---

### TC-PERS-003: Channel Variants (LiveChat vs Email)

**Objective:** Verify different template variants used for different channels

**Test Steps:**
1. Send order status query via Email channel
2. Send identical query via LiveChat channel

**Expected Results:**
- ✅ Email: Longer, more detailed template
- ✅ LiveChat: Shorter, more concise template
- ✅ Same information included, different presentation

---

## Test Execution Plan

### Phase 1: Core Order Status (Week 1)
- TC-OS-001, TC-OS-002
- TC-ETA-001, TC-ETA-002, TC-ETA-003
- TC-PERS-001, TC-PERS-002

**Gate:** All Phase 1 tests must pass before Phase 2

### Phase 2: Reopen Behavior (Week 2)
- TC-REOPEN-001, TC-REOPEN-002, TC-REOPEN-003
- Requires Richpanel automation rule configured
- Requires middleware reopen detection implemented

**Gate:** All Phase 2 tests must pass before Phase 3

### Phase 3: Routing and Extensibility (Week 2-3)
- TC-ROUTE-001, TC-ROUTE-002, TC-ROUTE-003
- TC-FAQ-001
- TC-DEDUP-001, TC-DEDUP-002

**Gate:** All Phase 3 tests must pass before production go-live

### Phase 4: Production Smoke Test (Pre-Launch)
- Run subset of critical tests in production (with test orders)
- Verify end-to-end flow works
- Verify no regression from staging

---

## Evidence Documentation

For each test, capture:

1. **Test Evidence Log Entry:**
   - Test ID
   - Date executed
   - Environment (dev/staging/prod)
   - Result (Pass/Fail)
   - Evidence link

2. **Screenshots:**
   - Richpanel conversation showing automated reply
   - Ticket status changes
   - Tags applied

3. **Log Excerpts:**
   - Middleware classification decision
   - Template selection
   - Routing decision

4. **Metrics:**
   - CloudWatch metrics showing event processed
   - DynamoDB idempotency entry

**Storage Location:** `qa/test_evidence/wave_audit/`

**Log Entry Format:**
```markdown
### TC-OS-001 - Order Status with Tracking

**Date:** 2026-01-10  
**Environment:** Staging  
**Tester:** QA Team  
**Result:** ✅ PASS

**Evidence:**
- Screenshot: `qa/test_evidence/wave_audit/tc-os-001-conversation.png`
- Logs: `qa/test_evidence/wave_audit/tc-os-001-logs.txt`
- Metrics: CloudWatch dashboard link

**Notes:** All expected behaviors confirmed. Tracking number displayed correctly, ticket auto-closed.
```

---

## Success Criteria

Testing is complete when:

- [ ] All P0 tests pass (OS-001, ETA-001, REOPEN-001, ROUTE-001)
- [ ] All P1 tests pass (remaining test suite)
- [ ] Test evidence documented in `Test_Evidence_Log.md`
- [ ] No P0/P1 bugs open
- [ ] Stakeholder sign-off obtained

**Production Go-Live Gate:** All tests must pass in staging before enabling automation in production.

---

**Version:** 1.0  
**Last Updated:** 2026-01-09  
**Status:** Ready for QA execution  
**Owner:** QA + Engineering

