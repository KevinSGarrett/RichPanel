# Department Routing Spec - Updates for Reopened Tickets

**Purpose:** Additions to `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`  
**Date:** 2026-01-09  
**Status:** Supplement for handling customer replies to auto-closed tickets

---

## Overview

This document contains routing rules for tickets that customers reopen after middleware auto-close. These should be integrated into the main `Department_Routing_Spec.md`.

---

## New Routing Rules

### Reopened Ticket Routing (Post Auto-Close)

Add this section after the main intent routing matrix:

---

## Special Case: Reopened Tickets After Auto-Close

When a customer replies to a ticket that was previously auto-closed by the middleware, special routing applies.

### Detection Criteria

A ticket is considered "reopened after auto-close" when ALL of these are true:

1. Ticket has tag `mw-auto-replied` (middleware sent an automated response)
2. Ticket status was "Resolved" and is now "Open" (customer replied)
3. Time since auto-close is < 7 days (after 7 days, treat as new conversation)

### Routing Policy

**Default destination:** Email Support Team

**Rationale:**
- Customer may be dissatisfied with automated response
- Order situation may have changed since automation
- Human review is needed to ensure customer satisfaction

**Tags to apply:**
- `mw-reopened-after-auto-close` (tracking tag)
- Keep all existing tags (`mw-auto-replied`, `mw-intent-*`, etc.)

**Automation tier:** Route-only (Tier 0 for this scenario)
- Do NOT send another automated template
- Exception: If >48 hours AND order status significantly changed, MAY consider new update (future feature)

### Implementation

**Middleware logic:**
```python
# In pipeline.py or router.py
def classify_routing(payload):
    # Check for reopened-after-auto-close scenario
    if _is_reopened_after_auto_close(payload):
        return RoutingDecision(
            category="reopened_after_auto_close",
            intent="order_status_tracking",  # Original intent
            department="Email Support Team",
            tags=["mw-reopened-after-auto-close", "mw-route-only"],
            reason="customer_replied_after_auto_close",
            confidence=1.0,  # Deterministic rule
        )
    
    # ... rest of routing logic

def _is_reopened_after_auto_close(payload):
    tags = payload.get("ticket", {}).get("tags", [])
    if "mw-auto-replied" not in tags:
        return False
    
    # Check if ticket was previously resolved
    # This may require fetching ticket history from Richpanel API
    # or using a state table to track auto-closed tickets
    
    return payload.get("ticket", {}).get("was_reopened", False)
```

**Richpanel automation rule:**
- **Name:** "Middleware - Route Reopened Tickets"
- **Trigger:** "When tag `mw-reopened-after-auto-close` is added"
- **Conditions:** None (apply to all channels)
- **Actions:**
  - Assign to: Email Support Team
  - Set priority: Normal (or Medium if preferred)
  - Add tag: `requires-human-review` (optional)
- **Order:** After main middleware trigger rule, before general assignment rules
- **Skip subsequent rules:** OFF

---

## Updated Intent Routing Matrix

Add these rows to the existing intent → destination mapping table:

| Intent | Default destination | Tags to add (minimum) | Allowed automation (early rollout) | Notes |
|---|---|---|---|---|
| **Special Cases** | | | | |
| reopened_after_auto_close | Email Support Team | mw-reopened-after-auto-close, mw-route-only | Route only (no auto-reply) | Customer replied after middleware auto-closed ticket |
| multiple_reopen_after_auto_close | Email Support Team or Leadership | mw-persistent-issue | Route only + escalate | Customer reopened >2 times; may indicate template quality issue |

---

## Metrics and Monitoring

Track the following for reopened tickets:

### Key Metrics

1. **Reopen rate by template:**
   - Formula: (reopened_tickets / total_auto_closed_tickets) per template_id
   - Target: <10% for high-quality templates
   - Alert threshold: >15%

2. **Time to reopen:**
   - Distribution: <1hr, 1-6hr, 6-24hr, 1-7 days
   - Insight: Quick reopens may indicate incorrect automation

3. **Reopen reasons (manual tagging by agents):**
   - "Wrong information provided"
   - "Customer wants expedited shipping" (business rule change request)
   - "Order status changed after automation"
   - "Customer didn't understand automated response"

4. **Resolution rate after reopen:**
   - % of reopened tickets resolved by Email Support Team
   - Average handle time for reopened tickets

### Dashboards

Create CloudWatch or Richpanel dashboard with:
- Reopen rate trend (daily/weekly)
- Reopen rate by template_id
- Reopen rate by channel (email vs livechat vs social)
- Distribution of time-to-reopen

### Alerts

**P1 Alert:**
- Reopen rate exceeds 20% for any template → Pause automation for that template

**P2 Alert:**
- Reopen rate exceeds 15% globally → Review automation quality

**P3 Alert:**
- >5 reopens in 1 hour → Possible automation loop or system issue

---

## Escalation Paths

### Standard Escalation

Most reopened tickets route to Email Support Team with normal priority.

### High-Priority Escalation

Escalate to Leadership Team or Senior Support when:
- Customer has reopened >2 times after auto-close
- Negative sentiment detected (future: sentiment analysis)
- High-value customer (if customer tier data available)
- Order value >$500 (configurable threshold)

**Tags for escalation:**
- `mw-persistent-issue`
- `escalate-to-leadership` (optional, if Leadership queue exists)

---

## Edge Cases

### Case 1: Customer replies immediately (<5 minutes)

**Scenario:** Middleware sends auto-close, customer replies "that's not helpful" within 5 minutes

**Handling:**
- Standard reopen routing (Email Support Team)
- Consider: If <5 min AND negative keywords detected → higher priority
- Future: Train model to detect "insufficient answer" signals

### Case 2: Order status changed after auto-close

**Scenario:** 
- Monday 10am: Middleware says "order will arrive in 2-3 days" (no tracking)
- Monday 2pm: Order ships, tracking number created
- Monday 3pm: Customer replies "where's my tracking?"

**Current handling:**
- Routes to Email Support Team
- Agent provides tracking number manually

**Future improvement:**
- Detect that tracking is now available
- Send proactive update with tracking link (before customer replies)
- Or: Allow second automated reply if order status changed significantly

### Case 3: Customer replies with new question

**Scenario:** Customer replies "Thanks! Also, can I change my address?"

**Handling:**
- Reopen routing applies (Email Support Team)
- Address change is Tier 1 (intake only), so human handling is correct
- Agent collects new address and processes request

### Case 4: Multiple orders, different issues

**Scenario:** Customer has 2 orders. Middleware auto-closed ticket for Order A. Customer replies asking about Order B.

**Handling:**
- Standard reopen routing
- Agent handles both orders in single conversation
- May require fetching both order details

---

## Testing Requirements

Before enabling reopened ticket routing in production:

### Test Cases

**TC-REOPEN-001: Standard reopen**
- Setup: Auto-close ticket with `t_order_eta_no_tracking_verified`
- Action: Customer replies "when exactly will it arrive?"
- Expected:
  - Ticket reopens (status: Resolved → Open)
  - Tag `mw-reopened-after-auto-close` added
  - Assigned to Email Support Team
  - No second automated reply sent

**TC-REOPEN-002: Multiple reopens**
- Setup: Auto-close ticket
- Action: Customer reopens, agent responds, customer reopens again (3rd time)
- Expected:
  - Tag `mw-persistent-issue` added on 3rd reopen
  - Escalated appropriately

**TC-REOPEN-003: Late reopen (>7 days)**
- Setup: Auto-close ticket on Jan 1
- Action: Customer replies on Jan 10
- Expected:
  - Treat as new inquiry (not "reopened after auto-close")
  - May send new automation if eligible
  - Do NOT add `mw-reopened-after-auto-close` tag

**TC-REOPEN-004: Reopen with new order**
- Setup: Auto-closed for Order A
- Action: Customer asks about Order B in reply
- Expected:
  - Routes to Email Support Team
  - Agent can access both order details

**TC-REOPEN-005: Agent manually reopens**
- Setup: Agent manually changes ticket from Resolved to Open (not customer reply)
- Expected:
  - Do NOT apply reopen routing
  - Maintain current assignment

---

## Configuration Checklist

- [ ] Add `mw-reopened-after-auto-close` tag to Richpanel tag library
- [ ] Create automation rule "Middleware - Route Reopened Tickets"
- [ ] Set rule order (after main trigger, before general rules)
- [ ] Verify Email Support Team exists and can receive assignments
- [ ] Test rule in staging environment
- [ ] Create dashboard for reopen metrics
- [ ] Set up alerts for high reopen rates
- [ ] Document in operations handbook
- [ ] Train Email Support Team on handling reopened tickets
- [ ] Add to QA test suite

---

## Integration Instructions

**To integrate into main Department_Routing_Spec.md:**

1. Open `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`

2. Add "Special Case: Reopened Tickets After Auto-Close" section after the main intent→department table (after line 106)

3. Add two new rows to the routing matrix for special cases

4. Update "Last updated" date

5. Add changelog entry

6. Update related docs:
   - `Richpanel_Config_Changes_v1.md` - Add automation rule
   - `Order_Status_Automation.md` - Cross-reference this routing policy
   - `Human_Handoff_and_Escalation.md` - Add section on reopen handling

---

**Version:** 1.0  
**Last Updated:** 2026-01-09  
**Integration Status:** Pending merge

