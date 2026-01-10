# Implementation Checklist Updates - Tasks to Add

**Purpose:** New tasks to add to `PLAN_CHECKLIST.md` based on Wave Audit findings  
**Date:** 2026-01-09  
**Status:** Checklist amendments

---

## Overview

This document lists specific tasks that should be added to your project checklists to ensure all identified gaps are addressed.

**Categories:**
1. Documentation updates
2. Richpanel configuration
3. Testing and validation
4. Code implementation (if needed)

---

## Tasks to Add to PLAN_CHECKLIST.md

### Category: Documentation Updates

```markdown
## docs/05_FAQ_Automation/Order_Status_Automation.md

### Order Status Automation > Customer Reply Handling
- [ ] PLN-WA001 — Add section "Customer Replies to Auto-Closed Tickets" to Order_Status_Automation.md
  - Source: WaveAudit/02_Order_Status_Automation_Addendum.md
  - Location: After "De-duplication" section (current line 175)
  - Owner: PM + Engineering

- [ ] PLN-WA002 — Add section "Personalization Strategy" to Order_Status_Automation.md
  - Source: WaveAudit/02_Order_Status_Automation_Addendum.md
  - Location: After "Goal" section (near beginning)
  - Owner: PM + Product

- [ ] PLN-WA003 — Add section "Pre-Launch Validation Checklist" to Order_Status_Automation.md
  - Source: WaveAudit/02_Order_Status_Automation_Addendum.md
  - Location: End of document
  - Owner: QA + Engineering

## docs/01_Product_Scope_Requirements/Department_Routing_Spec.md

### Department Routing Spec > Reopened Ticket Routing
- [ ] PLN-WA004 — Add "Special Case: Reopened Tickets After Auto-Close" section
  - Source: WaveAudit/03_Department_Routing_Updates.md
  - Location: After main intent routing matrix (after line 106)
  - Owner: Engineering + PM

- [ ] PLN-WA005 — Add rows to routing matrix for reopened ticket scenarios
  - Intent: `reopened_after_auto_close`
  - Intent: `multiple_reopen_after_auto_close`
  - Owner: Engineering + PM

## docs/05_FAQ_Automation/ (New Document)

### FAQ Extensibility Guide
- [ ] PLN-WA006 — Create `How_to_Add_New_FAQ.md` procedural guide
  - Source: WaveAudit/01_How_to_Add_New_FAQ.md
  - Location: `docs/05_FAQ_Automation/How_to_Add_New_FAQ.md`
  - Owner: Engineering + PM

## docs/01_Product_Scope_Requirements/Product_Vision_and_Non_Goals.md

### Product Vision > Personalization Approach
- [ ] PLN-WA007 — Add clarification on template-based vs LLM-generated message approach
  - Source: WaveAudit/04_Message_Personalization_Strategy.md
  - Location: "Product Vision" or "Non-Goals" section
  - Owner: Product + PM

## docs/03_Richpanel_Integration/Richpanel_Config_Changes_v1.md

### Richpanel Configuration > Reopened Ticket Routing
- [ ] PLN-WA008 — Add automation rule specification for reopened ticket routing
  - Source: WaveAudit/05_Richpanel_Automation_Rules_Supplement.md
  - Location: Section 2 (Human UI execution) or new section
  - Owner: DevOps + Support Ops

## docs/05_FAQ_Automation/Human_Handoff_and_Escalation.md

### Human Handoff > Reopened Tickets
- [ ] PLN-WA009 — Add section on handling customer replies to auto-closed tickets
  - Cross-reference: WaveAudit/02_Order_Status_Automation_Addendum.md
  - Location: After "Auto-close policy" section
  - Owner: PM + Engineering
```

---

### Category: Richpanel Configuration

```markdown
## Richpanel Automation Rules

### Rule: Reopened Ticket Routing
- [ ] PLN-WA010 — Create Richpanel automation rule "Middleware — Route Reopened Tickets"
  - Trigger: Tag `mw-reopened-after-auto-close` added
  - Action: Assign to Email Support Team
  - Reference: WaveAudit/05_Richpanel_Automation_Rules_Supplement.md
  - Owner: DevOps + Support Ops

- [ ] PLN-WA011 — Add tags to Richpanel tag library
  - New tags: `mw-reopened-after-auto-close`, `requires-human-review`, `mw-persistent-issue`
  - Owner: Support Ops

- [ ] PLN-WA012 — Create saved view "Reopened After Auto-Close" in Richpanel
  - Filter: Has tag `mw-reopened-after-auto-close`
  - Sort: By reopen time (most recent first)
  - Owner: Support Ops

- [ ] PLN-WA013 — Configure rule ordering (reopened ticket rule after main trigger)
  - Ensure: Runs before general assignment rules
  - Verify: "Skip subsequent rules" is OFF
  - Owner: DevOps
```

---

### Category: Testing and Validation

```markdown
## Testing: Richpanel Reopen Behavior

### Validate Ticket Reopen Mechanics
- [ ] PLN-WA014 — Test: Richpanel "Resolved" status allows customer reply to reopen ticket
  - Environment: Staging
  - Steps: Create ticket, resolve it, send customer reply, verify status changes to Open
  - Evidence: Screenshot + log entry in Test_Evidence_Log.md
  - Owner: QA

- [ ] PLN-WA015 — Test: Reopened ticket triggers webhook to middleware
  - Verify: Middleware receives webhook with correct payload
  - Verify: Middleware detects reopen scenario (has `mw-auto-replied` tag)
  - Owner: QA + Engineering

- [ ] PLN-WA016 — Test: Reopened ticket routing rule works correctly
  - Verify: Tag `mw-reopened-after-auto-close` is added by middleware
  - Verify: Richpanel rule triggers assignment to Email Support Team
  - Verify: No second automated reply is sent
  - Owner: QA + DevOps

## Testing: Order Status Automation End-to-End

### Order Status with Tracking
- [ ] PLN-WA017 — Test: Order with tracking number receives `t_order_status_verified` template
  - Verify: Tracking number and URL included in reply
  - Verify: Ticket auto-closed (status set to Resolved)
  - Verify: Tags applied correctly
  - Owner: QA

### Order Status without Tracking (ETA Calculation)
- [ ] PLN-WA018 — Test: Order without tracking (Standard shipping, within SLA) receives ETA message
  - Verify: Business day calculation correct
  - Verify: Remaining window calculated correctly (e.g., "1-3 business days")
  - Verify: Template `t_order_eta_no_tracking_verified` used
  - Verify: Ticket auto-closed
  - Owner: QA

- [ ] PLN-WA019 — Test: Order without tracking (outside SLA window) does NOT auto-close
  - Verify: Routes to Email Support Team
  - Verify: No auto-close (ticket remains open)
  - Owner: QA

### Customer Reply After Auto-Close
- [ ] PLN-WA020 — Test: Customer replies to auto-closed ticket within 24 hours
  - Verify: Ticket reopens
  - Verify: Routed to Email Support Team
  - Verify: No second automated reply sent
  - Verify: Reopen metrics tracked correctly
  - Owner: QA

- [ ] PLN-WA021 — Test: Customer replies multiple times (>2 reopens)
  - Verify: Tag `mw-persistent-issue` added on 3rd reopen
  - Verify: Escalation rule triggers (if configured)
  - Owner: QA

## Testing: Idempotency and Deduplication

### Duplicate Message Handling
- [ ] PLN-WA022 — Test: Duplicate webhook delivery (same message_id)
  - Verify: Only one reply sent
  - Verify: Idempotency table prevents duplicate processing
  - Verify: Logs show "duplicate_event" skip reason
  - Owner: QA + Engineering

### Rate Limiting
- [ ] PLN-WA023 — Test: Multiple messages from same customer in short time
  - Verify: Rate limit cooldown prevents spam
  - Verify: Tag `mw-auto-rate-limited` applied if threshold exceeded
  - Owner: QA
```

---

### Category: Code Implementation (If Needed)

```markdown
## Backend Implementation

### Reopened Ticket Detection
- [ ] PLN-WA024 — Implement reopened ticket detection logic in worker
  - Function: `_is_reopened_after_auto_close(payload)`
  - Location: `backend/src/richpanel_middleware/automation/pipeline.py`
  - Logic: Check for `mw-auto-replied` tag + ticket was_reopened flag
  - Owner: Engineering

- [ ] PLN-WA025 — Update plan_actions() to handle reopened tickets
  - If reopened: Set mode to "route_only", add tag `mw-reopened-after-auto-close`
  - If reopened: Do NOT send automated template
  - Owner: Engineering

### Metrics and Observability
- [ ] PLN-WA026 — Add CloudWatch metric: `reopened_tickets_count`
  - Dimensions: template_id, channel, time_to_reopen_bucket
  - Owner: Engineering

- [ ] PLN-WA027 — Add logging for reopened ticket scenarios
  - Log event: `worker.reopened_after_auto_close`
  - Fields: event_id, conversation_id, original_template_id, time_since_auto_close
  - Owner: Engineering

### Template Personalization
- [ ] PLN-WA028 — Verify template renderer handles optional variables correctly
  - Test: `{{#first_name}}...{{/first_name}}` block omitted if variable missing
  - Test: Required variables throw error if missing
  - Owner: Engineering

- [ ] PLN-WA029 — Add template rendering tests for all order status templates
  - Test: `t_order_status_verified`
  - Test: `t_order_eta_no_tracking_verified`
  - Test: `t_shipping_delay_verified`
  - Test: `t_order_status_ask_order_number`
  - Owner: Engineering
```

---

### Category: Monitoring and Alerting

```markdown
## Alerting Configuration

### Reopen Rate Alerts
- [ ] PLN-WA030 — Create P1 alert: Template reopen rate >20%
  - Trigger: Any template_id with reopen rate >20% over 24 hours
  - Action: Pause automation for that template, notify Engineering + Product
  - Platform: CloudWatch Alarms or Richpanel alerting
  - Owner: DevOps

- [ ] PLN-WA031 — Create P2 alert: Global reopen rate >15%
  - Trigger: Overall reopen rate >15% for 2+ consecutive hours
  - Action: Notify Support Ops + Product
  - Owner: DevOps

- [ ] PLN-WA032 — Create P3 alert: Persistent reopens spike
  - Trigger: >5 tickets with `mw-persistent-issue` tag in 1 hour
  - Action: Notify Support leadership
  - Owner: DevOps

## Dashboard Creation

### Reopened Tickets Dashboard
- [ ] PLN-WA033 — Create CloudWatch or Richpanel dashboard for reopen metrics
  - Widget: Reopen rate trend (line graph)
  - Widget: Reopens by template_id (bar chart)
  - Widget: Time-to-reopen distribution (histogram)
  - Widget: Reopens by channel (pie chart)
  - Owner: DevOps + Support Ops
```

---

### Category: Training and Documentation

```markdown
## Support Team Training

### Email Support Team Training
- [ ] PLN-WA034 — Train Email Support Team on handling reopened tickets
  - Topics: What reopened tickets are, how to respond, quality review tags
  - Reference: WaveAudit/05_Richpanel_Automation_Rules_Supplement.md (Training section)
  - Owner: Support Ops

- [ ] PLN-WA035 — Update operations handbook with reopened ticket procedures
  - Document: `docs/10_Operations_Runbooks_Training/Operations_Handbook.md`
  - Section: Add "Handling Reopened Tickets" section
  - Owner: Support Ops + PM

### Stakeholder Communication
- [ ] PLN-WA036 — Share personalization strategy decision with stakeholders
  - Document: WaveAudit/04_Message_Personalization_Strategy.md
  - Audience: Product, Business, Support Ops, Leadership
  - Format: Summary email or presentation
  - Owner: Product + PM

## Change Log Updates

### Update Living Documents
- [ ] PLN-WA037 — Update `CHANGELOG.md` with Wave Audit findings and resolutions
  - Entry: "Wave Audit completed - Added reopened ticket handling, FAQ extensibility guide, personalization strategy clarification"
  - Owner: PM

- [ ] PLN-WA038 — Update `docs/00_Project_Admin/Progress_Log.md`
  - Entry: Document completion of Wave Audit action items
  - Owner: PM

- [ ] PLN-WA039 — Update `REHYDRATION_PACK/02_CURRENT_STATE.md`
  - Add: Reopened ticket handling status
  - Add: FAQ extensibility framework status
  - Owner: PM
```

---

## Integration Instructions

### How to Add These to PLAN_CHECKLIST.md

**Option 1: Manual Integration**

1. Open `docs/00_Project_Admin/To_Do/PLAN_CHECKLIST.md`
2. Add a new section: "Wave Audit Remediation Tasks"
3. Copy relevant tasks from above
4. Assign task IDs (PLN-WA001 through PLN-WA039)
5. Run: `python scripts/regen_plan_checklist.py`

**Option 2: Create Source Document**

1. Create new doc: `docs/00_Project_Admin/WaveAudit_Action_Items.md`
2. Add all tasks above as markdown checkboxes
3. The regen script will auto-extract them
4. Run: `python scripts/regen_plan_checklist.py`

**Option 3: Add to Existing Plan Docs**

Distribute tasks to relevant existing plan documents:
- Add WA001-WA003, WA009 → `docs/05_FAQ_Automation/Order_Status_Automation.md`
- Add WA004-WA005 → `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`
- Add WA014-WA023 → `docs/08_Testing_Quality/Integration_Test_Plan.md`
- Add WA030-WA033 → `docs/08_Observability_Analytics/Alerts_and_Notifications.md`

Then regenerate checklist.

---

## Priority Grouping

### P0 - Must Complete Before Production Launch

- PLN-WA006 (FAQ guide)
- PLN-WA010 (Richpanel reopen rule)
- PLN-WA014 (Test reopen behavior)
- PLN-WA016 (Test reopen routing)
- PLN-WA024-WA025 (Code: reopen detection)

### P1 - Complete Within 2 Weeks

- PLN-WA001-WA005 (Documentation updates)
- PLN-WA007 (Personalization strategy doc)
- PLN-WA017-WA021 (E2E testing)
- PLN-WA030-WA032 (Alerts)

### P2 - Complete Within 1 Month

- PLN-WA008-WA009 (Additional docs)
- PLN-WA011-WA013 (Richpanel UI config)
- PLN-WA033 (Dashboard)
- PLN-WA034-WA035 (Training)

### P3 - Ongoing / Continuous

- PLN-WA036 (Stakeholder communication)
- PLN-WA037-WA039 (Change log updates)

---

## Task Assignment Recommendations

| Task Group | Recommended Owner | Time Estimate |
|---|---|---|
| Documentation (WA001-WA009) | PM + Engineering | 16-24 hours |
| Richpanel Config (WA010-WA013) | DevOps + Support Ops | 4-8 hours |
| Testing (WA014-WA023) | QA + Engineering | 16-20 hours |
| Code Implementation (WA024-WA029) | Engineering | 8-12 hours |
| Monitoring (WA030-WA033) | DevOps | 4-6 hours |
| Training (WA034-WA036) | Support Ops + PM | 4-6 hours |
| Change Log (WA037-WA039) | PM | 1-2 hours |

**Total Estimated Effort:** 53-79 hours (approximately 1.5-2 weeks with 1-2 engineers)

---

## Success Criteria

These tasks are complete when:

- [ ] All P0 tasks are checked off
- [ ] Staging environment tests pass for reopen scenarios
- [ ] Documentation is merged into main branch
- [ ] Richpanel automation rule is active and tested
- [ ] Email Support Team is trained
- [ ] Alerts and dashboards are configured
- [ ] Change log is updated

**Final Validation:** Run full E2E test suite including reopened ticket scenarios and confirm all pass.

---

**Version:** 1.0  
**Last Updated:** 2026-01-09  
**Status:** Ready for integration into project checklists

