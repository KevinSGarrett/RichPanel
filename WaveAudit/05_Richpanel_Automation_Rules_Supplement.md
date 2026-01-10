# Richpanel Automation Rules - Supplement for Reopened Tickets

**Purpose:** Required Richpanel automation rules for handling customer replies to auto-closed tickets  
**Date:** 2026-01-09  
**Status:** Configuration requirements (add to `Richpanel_Config_Changes_v1.md`)

---

## Overview

This document specifies the Richpanel automation rules needed to properly handle customers who reply to tickets that were auto-closed by the middleware.

**Gap addressed:** Current documentation doesn't include rules for routing reopened tickets to Email Support Team.

---

## Required Automation Rule: Reopened Ticket Routing

### Rule Specification

**Rule Name:** `Middleware — Route Reopened Tickets`

**Rule Type:** Tagging Rule (preferred) or Assignment Rule (fallback)

**Placement:** 
- **Order:** Immediately after main `Middleware — Inbound Trigger` rule
- **Priority:** High (must run before general assignment rules)

**Trigger Conditions:**
- **When:** Tag is added to ticket
- **Which tag:** `mw-reopened-after-auto-close`
- **All channels:** Yes (email, livechat, social, TikTok, phone)

**Actions to Perform:**

1. **Assign to Team:**
   - Team: `Email Support Team`
   - Reason: Customer replied after automated closure, needs human review

2. **Add Tag (optional):**
   - Tag: `requires-human-review`
   - Purpose: Visibility for support team

3. **Set Priority (optional):**
   - Priority: `Normal` (or `Medium` if your tenant supports it)
   - Rationale: Not urgent, but should be handled within normal SLA

4. **Add Internal Note (optional):**
   - Note: "Customer replied after middleware auto-closed this ticket. Original automated response may have been insufficient. Please review order status and provide updated information."

**Rule Settings:**
- **Skip all subsequent rules:** OFF (important!)
- **Reassign even if already assigned:** ON (if ticket was assigned elsewhere, move to Email Support)
- **Active:** ON (once validated in staging)

---

## Rule Configuration Steps

### Step 1: Access Richpanel Automation Settings

1. Log into Richpanel admin panel
2. Navigate to: Settings → Automation → Tagging Rules (or Assignment Rules if Tagging Rules don't support the needed actions)
3. Click "Create New Rule"

### Step 2: Configure Trigger

**Trigger Type:** "When tag is added"

**Configuration:**
```
Trigger: Tag added
Tag name: mw-reopened-after-auto-close
All channels: ✓ Email ✓ LiveChat ✓ Social ✓ TikTok ✓ Phone
```

**Conditions (optional):**
- No additional conditions needed
- Apply to all tickets regardless of status, channel, or other attributes

### Step 3: Configure Actions

**Action 1: Assign to Team**
```
Action: Assign to team
Team: Email Support Team
```

**Action 2: Add Tag (optional but recommended)**
```
Action: Add tag
Tag: requires-human-review
```

**Action 3: Set Priority (optional)**
```
Action: Set priority
Priority: Normal (or Medium)
```

**Action 4: Add Internal Note (optional)**
```
Action: Add internal note
Note: "🔄 Customer replied after middleware auto-closed this ticket. 
Review order status and provide updated information as needed."
```

### Step 4: Set Rule Options

**Rule Order:**
- Drag rule to position immediately AFTER `Middleware — Inbound Trigger`
- Should be BEFORE general channel-based assignment rules

**Rule Settings:**
- ☐ Skip all subsequent rules (MUST BE OFF)
- ☑ Reassign even if already assigned (should be ON)
- ☑ Active (after staging validation)

### Step 5: Test in Staging

Before activating in production:

1. Create test ticket in staging
2. Add tag `mw-auto-replied` manually
3. Manually set status to "Resolved"
4. Send customer reply (via API or test email)
5. Verify:
   - Ticket reopens (status → Open)
   - Tag `mw-reopened-after-auto-close` is added by middleware
   - Rule triggers assignment to Email Support Team
   - Optional tags/notes are added

### Step 6: Activate in Production

- [ ] Staging tests pass
- [ ] Email Support Team notified of new routing
- [ ] Dashboard/reporting updated to track reopened tickets
- [ ] Activate rule in production
- [ ] Monitor for 48 hours, adjust if needed

---

## Supporting Rule: Prevent Duplicate Auto-Replies

**Rule Name:** `Middleware — Suppress Auto-Reply on Reopen`

**Purpose:** Ensure middleware doesn't send another automated template when customer replies to a closed ticket

**Implementation:** This is primarily handled in **middleware code** (not Richpanel automation), but can be reinforced with a Richpanel rule if needed.

**Middleware Logic:**
```python
# In pipeline.py
def plan_actions(envelope, safe_mode, automation_enabled):
    payload = envelope.payload
    
    # Check if ticket has already been auto-replied
    if _ticket_has_tag(payload, "mw-auto-replied"):
        # Check if this is a reopen scenario
        if _is_customer_reply_after_resolved(payload):
            # Route-only, no automation
            return ActionPlan(
                mode="route_only",
                automation_enabled=False,
                reason="customer_reopened_after_auto_close"
            )
    
    # ... rest of normal logic
```

**Richpanel Rule (optional reinforcement):**
- Trigger: Ticket updated AND has tag `mw-auto-replied`
- Condition: Status changed from Resolved to Open
- Action: Add tag `mw-reopen-detected` (middleware uses this as additional signal)

---

## Supporting Rule: Multiple Reopen Escalation

**Rule Name:** `Middleware — Escalate Persistent Reopens`

**Purpose:** If customer reopens the same ticket >2 times, escalate to leadership or senior support

**Trigger:**
- When tag `mw-persistent-issue` is added

**Actions:**
- Assign to: Leadership Team (or Senior Support queue)
- Set priority: High
- Add tag: `escalated`
- Send notification to: support-escalations@company.com

**Implementation Notes:**
- Middleware adds `mw-persistent-issue` tag after detecting 3rd reopen
- Requires middleware to track reopen count (can use state table or count messages after resolve events)

---

## Metrics Dashboard

Create Richpanel or CloudWatch dashboard to monitor:

### Key Metrics

1. **Reopened Tickets Count**
   - Filter: Tickets with tag `mw-reopened-after-auto-close`
   - Grouping: By day, by template_id, by channel
   - Target: <10% of auto-closed tickets

2. **Time to Reopen**
   - Calculate: Time between "Resolved" status and "Open" status
   - Buckets: <1hr, 1-6hr, 6-24hr, 1-7 days
   - Insight: Fast reopens may indicate poor automation quality

3. **Reopen by Template**
   - Which templates cause most reopens?
   - Alert if any template >15% reopen rate

4. **Agent Handle Time for Reopened Tickets**
   - Are reopened tickets harder/longer to resolve?
   - Compare to non-reopened baseline

### Sample Dashboard Widgets

**Widget 1: Reopen Rate Trend**
- Chart type: Line graph
- X-axis: Date (daily or weekly)
- Y-axis: Reopen rate %
- Formula: (reopened tickets / total auto-closed) * 100

**Widget 2: Reopens by Template**
- Chart type: Bar chart
- X-axis: Template ID
- Y-axis: Count of reopens
- Sort: Descending by count

**Widget 3: Time-to-Reopen Distribution**
- Chart type: Histogram
- Buckets: <1hr, 1-6hr, 6-24hr, 1-7days, >7days
- Shows: How quickly customers are replying after auto-close

---

## Alert Configuration

### Alert 1: High Reopen Rate (P1)

**Condition:** Reopen rate for ANY template exceeds 20%

**Calculation:**
```sql
SELECT template_id, 
       (COUNT(*) WHERE has_tag('mw-reopened-after-auto-close')) / 
       (COUNT(*) WHERE has_tag('mw-auto-replied')) * 100 AS reopen_rate
FROM tickets
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY template_id
HAVING reopen_rate > 20
```

**Action:**
- Pause automation for that template (set kill switch)
- Notify: Engineering + Support Ops + Product
- Review template quality

### Alert 2: Global Reopen Rate Spike (P2)

**Condition:** Overall reopen rate exceeds 15% for 2+ consecutive hours

**Action:**
- Notify: Support Ops + Product
- Review recent template changes
- Check for system issues (Shopify API down, incorrect tracking data, etc.)

### Alert 3: Persistent Reopens (P2)

**Condition:** >5 tickets tagged with `mw-persistent-issue` in 1 hour

**Action:**
- Notify: Support leadership
- Investigate common patterns (same product, same shipping method, etc.)
- May indicate systemic issue (fulfillment problem, tracking provider down, etc.)

---

## Richpanel Configuration Checklist

**Pre-Deployment:**
- [ ] Verify Email Support Team exists in Richpanel
- [ ] Confirm team has capacity for reopened ticket volume
- [ ] Add `mw-reopened-after-auto-close` tag to tag library
- [ ] Add `requires-human-review` tag (optional)
- [ ] Add `mw-persistent-issue` tag to tag library
- [ ] Create saved view: "Reopened After Auto-Close" (filter by tag)

**Rule Creation:**
- [ ] Create `Middleware — Route Reopened Tickets` rule
- [ ] Set rule order (after main trigger, before general assignment)
- [ ] Configure trigger: Tag `mw-reopened-after-auto-close` added
- [ ] Configure action: Assign to Email Support Team
- [ ] Set "Skip subsequent rules" to OFF
- [ ] Set "Reassign if already assigned" to ON

**Testing (Staging):**
- [ ] Create test ticket with `mw-auto-replied` tag
- [ ] Manually resolve ticket
- [ ] Send customer reply (test email or API)
- [ ] Verify ticket reopens
- [ ] Verify tag `mw-reopened-after-auto-close` added
- [ ] Verify assignment to Email Support Team
- [ ] Verify no duplicate auto-reply sent

**Monitoring:**
- [ ] Create dashboard for reopen metrics
- [ ] Set up P1 alert (reopen rate >20% for any template)
- [ ] Set up P2 alert (global reopen rate >15%)
- [ ] Set up P3 alert (persistent reopens >5/hour)

**Documentation:**
- [ ] Add to operations handbook
- [ ] Train Email Support Team on handling reopened tickets
- [ ] Update QA test cases
- [ ] Add to incident response runbook

**Production Deployment:**
- [ ] Verify staging tests passed
- [ ] Activate rule in production
- [ ] Monitor for first 48 hours
- [ ] Adjust as needed based on metrics

---

## Training: Email Support Team

### What to Expect

**New Routing:**
- Tickets with tag `mw-reopened-after-auto-close` will be assigned to your team
- These are customers who replied after middleware auto-closed their ticket
- Usually order status inquiries where automated answer was insufficient

### How to Handle

1. **Review ticket history:**
   - See what automated message was sent
   - Check what customer replied with

2. **Check current order status:**
   - Order may have updated since automation (new tracking, etc.)
   - Provide current, accurate information

3. **Provide human touch:**
   - Acknowledge their reply
   - Give updated information
   - Offer to help with any additional questions

4. **Tag for quality review (optional):**
   - If automated message was clearly wrong: Add tag `automation-error`
   - If customer just needed more detail: No special tag
   - If customer is upset: Add tag `escalate` if needed

### Example Scenarios

**Scenario 1: Tracking appeared after automation**
- Middleware said: "Should arrive in 2-3 days" (no tracking yet)
- Customer replied: "Do you have tracking now?"
- Agent response: "Yes! Tracking just became available: [link]. Should arrive by [date]."

**Scenario 2: Customer needs expedited shipping**
- Middleware said: "Should arrive in 3-5 days"
- Customer replied: "I need it by Friday!"
- Agent response: "Let me check if we can upgrade shipping. [investigates options]"

**Scenario 3: Automated message was confusing**
- Middleware used technical jargon
- Customer replied: "What does 'fulfilled' mean?"
- Agent response: Clarifies in plain language

---

## Integration with Existing Documentation

**Add to `Richpanel_Config_Changes_v1.md`:**
- Section 2.8: Add reopened ticket routing rule to acceptance checklist
- Section 3: Add rule creation steps to UI execution checklist

**Add to `Order_Status_Automation.md`:**
- Cross-reference this rule in "Customer Replies After Auto-Close" section

**Add to `Department_Routing_Spec.md`:**
- Add `reopened_after_auto_close` to special cases table

**Add to `PLAN_CHECKLIST.md`:**
- Add tasks for creating and testing this rule

---

**Version:** 1.0  
**Last Updated:** 2026-01-09  
**Deployment Status:** Pending staging validation  
**Owner:** DevOps + Support Ops

