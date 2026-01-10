# Order Status Automation - Addendum (Missing Sections)

**Purpose:** Sections to add to `docs/05_FAQ_Automation/Order_Status_Automation.md`  
**Date:** 2026-01-09  
**Status:** Supplement to existing documentation

---

## Overview

This document contains missing sections identified during the Wave Audit that should be integrated into the existing `Order_Status_Automation.md` specification.

**Gaps addressed:**
1. Customer replies to auto-closed tickets
2. Personalization approach clarification
3. Richpanel reopen behavior validation

---

## Section to Add: Customer Replies After Auto-Close

**Insert after:** Section on "De-duplication (automation loop prevention)" (after current line 175)

**New Section Title:** Customer Replies to Auto-Closed Tickets

### Customer Replies to Auto-Closed Tickets

When a customer replies to a ticket that was auto-closed (resolved) by the middleware:

#### Expected Richpanel Behavior

- [ ] **MUST VERIFY:** Richpanel automatically reopens tickets when customer replies to "Resolved" status
- [ ] Status should change from "Resolved" → "Open" 
- [ ] Reply should trigger webhook to middleware (if not already suppressed)
- [ ] Previous conversation history should remain intact

#### Routing Policy for Reopened Tickets

When a ticket is reopened after auto-close:

1. **Detection:**
   - Ticket has tag `mw-auto-replied` (indicates prior automation)
   - Status changed from Resolved to Open (indicates customer replied)
   - OR: New message exists after a Resolved state

2. **Routing destination:**
   - Default: **Email Support Team**
   - Reason: Customer needs human review (automated answer may have been insufficient)

3. **Tags to apply:**
   - `mw-reopened-after-auto-close` (new tag for tracking)
   - Keep existing `mw-auto-replied` tag (for audit trail)
   - Keep existing `mw-intent-order-status` tag

4. **Do NOT auto-reply again:**
   - Check for `mw-auto-replied` tag before any automation
   - If customer is replying to a prior auto-close, route-only (no new template)
   - Exception: If >48 hours have passed AND order status changed significantly, MAY send new update (future consideration)

#### Implementation Requirements

**Middleware logic:**
```python
# Pseudocode for worker pipeline
if ticket.has_tag("mw-auto-replied") and ticket.was_reopened:
    # Customer replied after our auto-close
    plan.mode = "route_only"
    plan.routing.department = "Email Support Team"
    plan.routing.tags.append("mw-reopened-after-auto-close")
    plan.actions = [{"type": "route_only", "reason": "customer_replied_after_auto_close"}]
    # Do not send another template
```

**Richpanel automation rule:**
- **Trigger:** "When tag `mw-reopened-after-auto-close` is added"
- **Action:** "Assign to Email Support Team"
- **Priority:** High (should run early in rule chain)
- **Skip subsequent rules:** OFF (allow other rules to run if needed)

#### Observability

Track these metrics for reopened tickets:
- Count of tickets reopened within 24 hours of auto-close
- Count of tickets reopened within 48 hours
- Reopen rate by template_id (which templates cause most reopens?)
- Average time-to-reopen after auto-close

**Alerting:**
- If reopen rate exceeds 15% for any template → investigate template quality
- If reopen rate exceeds 25% globally → pause automation for review

#### Edge Cases

**Case 1: Customer says "that's wrong"**
- Detection: Sentiment analysis (future) or manual review
- Action: Route to Email Support Team with high priority
- Tag: `mw-customer-disputed-auto-reply`

**Case 2: Customer provides new information**
- Example: "Actually I need it by Friday" (after receiving ETA)
- Action: Route to Email Support Team
- Human agent can escalate shipping if needed

**Case 3: Order status changed after auto-close**
- Example: We said "arrives in 2-3 days" but tracking was created 10 minutes later
- Current: Customer sees new reply on reopen
- Future: Consider proactive notification if tracking appears within X hours of auto-close

**Case 4: Multiple reopens**
- If customer reopens >2 times after automation:
  - Add tag `mw-persistent-issue`
  - Escalate to supervisor/leadership queue (optional)
  - Never auto-reply again for this ticket

---

## Section to Add: Message Personalization Approach

**Insert after:** "Goal" section (near beginning of document)

**New Section Title:** Personalization Strategy

### Personalization Strategy

#### Template-Based Personalization (Current Approach)

The middleware uses **pre-approved templates** with **variable substitution** rather than free-form LLM-generated messages.

**How it works:**
1. LLM classifies the intent and selects a `template_id`
2. Middleware fetches required data (order details, tracking, ETA)
3. Template renderer fills variables ({{first_name}}, {{order_id}}, {{tracking_url}})
4. Final message is sent to customer

**Example:**
```
Template: "Hi{{#first_name}} {{first_name}}{{/first_name}} — here's the latest 
update for your order {{order_id}}: ..."

Rendered: "Hi Sarah — here's the latest update for your order #12345: ..."
```

#### Why Templates (Not Free-Form Generation)

**Safety benefits:**
- ✅ Prevents hallucinations (model can't invent order details)
- ✅ Ensures consistent tone and brand voice
- ✅ Makes A/B testing and iteration easier
- ✅ Reduces prompt injection risk
- ✅ Enables non-technical stakeholders to review/approve copy
- ✅ Compliance-friendly (all messages are pre-reviewed)

**Tradeoffs:**
- ⚠️ Less "unique" feeling than fully custom prose
- ⚠️ Requires template variants for different scenarios
- ⚠️ Template library maintenance overhead

#### Personalization Elements Available

Templates can include:
- **Customer name:** `{{first_name}}` (optional, gracefully omitted if missing)
- **Order-specific data:** `{{order_id}}`, `{{tracking_number}}`, `{{eta_remaining_human}}`
- **Status information:** `{{order_status}}`, `{{fulfillment_status}}`
- **Channel adaptation:** Different wording for LiveChat vs Email
- **Conditional blocks:** Only show tracking section if tracking exists

#### Future: Dynamic Personalization (Phase 2 - Not in v1)

If business requirements demand more "unique" messages:

**Potential approach:**
1. Generate message body with LLM (not just template_id)
2. Apply content policy filter (check for PII, inappropriate content, hallucinations)
3. Require human review for first N messages per template category
4. Store approved messages as "dynamic templates" for future use
5. Gradual rollout with strict quality gates

**Prerequisites for dynamic generation:**
- Robust content filtering
- Human-in-the-loop review workflow
- A/B testing framework
- Customer satisfaction tracking
- Legal/compliance approval

**Decision:** Dynamic generation is **out of scope for v1**. Revisit after order status automation proves stable for 3+ months.

---

## Section to Add: Validation Checklist

**Insert at:** End of document (new section)

**New Section Title:** Pre-Launch Validation Checklist

### Pre-Launch Validation Checklist

Before enabling order status automation in production, validate:

#### Richpanel Behavior Confirmation

- [ ] Create test ticket in staging Richpanel tenant
- [ ] Manually set ticket to "Resolved" status
- [ ] Send customer reply (from test customer account or API)
- [ ] **VERIFY:** Ticket status changes to "Open" automatically
- [ ] **VERIFY:** Conversation history is preserved
- [ ] **VERIFY:** Webhook fires for the customer reply (check middleware logs)
- [ ] Document evidence in `Test_Evidence_Log.md`

#### Reopen Routing Verification

- [ ] Create Richpanel automation rule for `mw-reopened-after-auto-close` tag
- [ ] Test rule triggers assignment to Email Support Team
- [ ] Verify rule does NOT cause routing fights with existing rules
- [ ] Test with multiple channels (email, livechat, social)

#### Template Rendering

- [ ] Test all order status templates render correctly in Richpanel
- [ ] Verify variable substitution works (first_name, order_id, etc.)
- [ ] Test with missing optional variables (template gracefully omits blocks)
- [ ] Verify channel-specific variants (livechat vs email)

#### De-duplication

- [ ] Send duplicate webhook (same message_id)
- [ ] Verify only one reply is sent
- [ ] Verify idempotency table prevents duplicate processing

#### Auto-Close Eligibility

- [ ] Test in-SLA order (should auto-close)
- [ ] Test late/out-of-window order (should NOT auto-close, route to human)
- [ ] Test ambiguous shipping method (should NOT auto-close)
- [ ] Verify `mw-auto-replied` and `mw:auto_closed` tags applied

#### Edge Case Handling

- [ ] Test customer with multiple orders (should ask for order number)
- [ ] Test order with partial fulfillment (should handle gracefully)
- [ ] Test missing tracking number (should send ETA if possible)
- [ ] Test preorder/backorder (should use preorder ETA if available)

---

## Integration Instructions

**To integrate this addendum into the main document:**

1. Open `docs/05_FAQ_Automation/Order_Status_Automation.md`

2. Insert "Personalization Strategy" section after line 15 (after "Goal" section)

3. Insert "Customer Replies to Auto-Closed Tickets" section after line 175 (after "De-duplication" section)

4. Insert "Pre-Launch Validation Checklist" section at the end of the document (new section)

5. Update "Last updated" date at the top of the document

6. Regenerate table of contents if the document has one

7. Update `CHANGELOG.md` with entry:
   ```
   - Enhanced Order_Status_Automation.md with customer reply handling and personalization strategy clarification
   ```

8. Update `docs/00_Project_Admin/Progress_Log.md` with completion note

---

## Related Updates Needed

After integrating this addendum, also update:

1. **`Department_Routing_Spec.md`**
   - Add row for `reopened_after_auto_close` pseudo-intent

2. **`Human_Handoff_and_Escalation.md`**
   - Add section on reopened ticket handling

3. **`Richpanel_Config_Changes_v1.md`**
   - Add automation rule for reopened ticket routing

4. **`PLAN_CHECKLIST.md`**
   - Add validation tasks from checklist above

5. **`Templates_Library_v1.md`**
   - Add note about template-based vs dynamic personalization approach

---

**Version:** 1.0  
**Last Updated:** 2026-01-09  
**Integration Status:** Pending merge into main document

