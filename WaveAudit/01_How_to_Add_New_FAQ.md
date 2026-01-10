# How to Add a New FAQ to the Automation System

**Purpose:** Step-by-step guide for adding FAQs #2-5 (and beyond) to the middleware automation framework  
**Owner:** Engineering + Support Ops  
**Status:** Procedural Guide (v1)

---

## Overview

This document provides a complete procedural checklist for adding a new FAQ to the RichPanel middleware automation system. The infrastructure is **already built** to support multiple FAQs - this guide ensures consistent, safe implementation.

**Use this guide when:**
- Adding one of the remaining 4 planned FAQs (Cancel Order, Missing Items, etc.)
- Expanding automation to cover additional high-volume intents
- Converting a Tier 1 intake template to Tier 2 automation

---

## Prerequisites

Before starting, confirm:

- [ ] FAQ is in top 10 by volume (refer to `Top_FAQs_Playbooks.md`)
- [ ] Tier level determined (Tier 1 = intake only, Tier 2 = verified auto-reply)
- [ ] Template copy drafted and approved by Support Ops
- [ ] Data sources identified (Shopify, ShipStation, Richpanel, etc.)
- [ ] Safety review completed (privacy, risk assessment)
- [ ] Stakeholder approval obtained

---

## Step-by-Step Implementation Checklist

### Phase 1: Design and Documentation

#### 1.1 Add Intent to Taxonomy

**File:** `docs/04_LLM_Design_Evaluation/Intent_Taxonomy_and_Labeling_Guide.md`

- [ ] Add new intent ID (e.g., `missing_items_in_shipment`)
- [ ] Define intent description and trigger phrases
- [ ] Add example customer messages (5-10 examples)
- [ ] Classify risk level (Tier 0/1/2/3)
- [ ] Document required entities (order number, email, photos, etc.)

**Example:**
```markdown
### `missing_items_in_shipment`

**Description:** Customer reports items missing from delivered order

**Trigger phrases:**
- "I didn't receive all my items"
- "Missing items in my order"
- "Only got 2 of 3 items"

**Tier:** 1 (intake only - requires photo evidence)
**Required entities:** order_id, missing_item_description, packing_slip_photo
```

#### 1.2 Update Department Routing Spec

**File:** `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`

- [ ] Add row to routing matrix (intent → department mapping)
- [ ] Specify destination team (e.g., Returns Admin)
- [ ] Define tags to apply (e.g., `mw-intent-missing-items`)
- [ ] Set allowed automation tier
- [ ] Document any special routing rules

**Example:**
```markdown
| missing_items_in_shipment | Returns Admin | mw-intent-missing-items | Tier 1 only | Photo/packing slip intake |
```

#### 1.3 Create Playbook Entry

**File:** `docs/05_FAQ_Automation/Top_FAQs_Playbooks.md`

- [ ] Add numbered section for the new FAQ
- [ ] List example customer phrasings
- [ ] Document required data sources
- [ ] Specify allowed templates
- [ ] Define routing destination
- [ ] List edge cases and fail-closed rules

**Example:**
```markdown
## 5) Missing Items (`missing_items_in_shipment`)

**Examples of customer phrasing:**
- "I'm missing items from my order"
- "Only received part of my order"

**Required data:**
- Deterministic match to order OR ask for order number
- Photo of received items (optional but recommended)

**Allowed automation:**
- Tier 1: `t_missing_items_intake`

**Routing:**
- Primary: **Returns Admin**
- Tags: `mw-intent-missing-items`, `mw-requires-photo`
```

---

### Phase 2: Template Creation

#### 2.1 Draft Template Copy

**File:** `docs/05_FAQ_Automation/templates/templates_v1.yaml`

- [ ] Create template ID (e.g., `t_missing_items_intake`)
- [ ] Write default channel copy
- [ ] Write livechat variant (if different)
- [ ] Define required variables
- [ ] Define optional variables
- [ ] Set tier level
- [ ] Set enabled flag

**Example:**
```yaml
- template_id: t_missing_items_intake
  tier: 1
  enabled: true
  purpose: "Collect info/photos for missing items; route to human"
  required_vars: []
  optional_vars:
    - first_name
  channels:
    default: |
      Hi{{#first_name}} {{first_name}}{{/first_name}} — sorry about that. We'll help.

      Please reply with:
      1) your order number
      2) which item(s) are missing
      3) a photo of what you received (including the packing slip if available)

      Once we have that, our team will review and take the next steps.
      — {{support_signature}}
    
    livechat: |
      Sorry about that. Please send your order # and list which items are missing. 
      If you can, attach a photo of what you received and the packing slip/label. We'll take it from there.
```

#### 2.2 Add to Templates Library

**File:** `docs/05_FAQ_Automation/Templates_Library_v1.md`

- [ ] Add formatted section with template details
- [ ] Include both channel variants
- [ ] Document required/optional variables
- [ ] Add usage notes

---

### Phase 3: LLM Integration

#### 3.1 Update LLM Routing Prompt

**File:** `backend/src/richpanel_middleware/automation/llm_routing.py`

- [ ] Add intent to `VALID_INTENTS` list (if not already present)
- [ ] Update routing system prompt documentation (if needed)
- [ ] Verify intent is in schema validation

**Example:**
```python
VALID_INTENTS = {
    "order_status_tracking",
    "missing_items_in_shipment",  # NEW
    # ... other intents
}
```

#### 3.2 Update Decision Pipeline Logic

**File:** `backend/src/richpanel_middleware/automation/pipeline.py`

If Tier 2 automation (not just intake):
- [ ] Add intent to automation candidate list
- [ ] Implement data lookup logic (if needed)
- [ ] Add action builder for new template
- [ ] Implement safety gates (deterministic match requirements)

If Tier 1 intake only:
- [ ] Verify routing logic handles the new intent
- [ ] Confirm tags are applied correctly

---

### Phase 4: Testing

#### 4.1 Create Test Cases

**File:** `docs/05_FAQ_Automation/FAQ_Playbook_Test_Cases.md`

- [ ] Add test scenarios for new FAQ
- [ ] Include positive cases (expected behavior)
- [ ] Include negative cases (edge cases, fallbacks)
- [ ] Define expected routing and tags
- [ ] Specify expected template selection

**Example:**
```markdown
### Missing Items Test Cases

**TC-MI-001: Clear missing items request**
- Input: "I ordered 3 items but only got 2"
- Expected intent: `missing_items_in_shipment`
- Expected template: `t_missing_items_intake`
- Expected routing: Returns Admin
- Expected tags: `mw-intent-missing-items`

**TC-MI-002: Ambiguous - could be damaged or missing**
- Input: "Something's wrong with my order"
- Expected: Lower confidence, route to human
```

#### 4.2 Unit Testing

- [ ] Add intent classification test to LLM routing tests
- [ ] Add template rendering test
- [ ] Test routing decision logic
- [ ] Verify tag application

#### 4.3 Integration Testing

- [ ] Test end-to-end flow in dev environment
- [ ] Verify Richpanel tag triggers assignment rule
- [ ] Confirm template renders correctly in Richpanel
- [ ] Validate idempotency (duplicate messages handled)

---

### Phase 5: Richpanel Configuration

#### 5.1 Create Assignment Rule (if needed)

**File:** `docs/03_Richpanel_Integration/Richpanel_Config_Changes_v1.md`

- [ ] Define trigger: "When tag `mw-intent-missing-items` is added"
- [ ] Set action: "Assign to Returns Admin"
- [ ] Set priority/order in rule list
- [ ] Document "skip subsequent rules" setting

#### 5.2 Verify Tag Alignment

- [ ] Confirm tag name matches between middleware and Richpanel
- [ ] Test tag application in staging
- [ ] Verify no tag conflicts with existing rules

---

### Phase 6: Documentation Updates

#### 6.1 Update Checklists

**File:** `docs/00_Project_Admin/To_Do/PLAN_CHECKLIST.md`

- [ ] Add implementation tasks for the new FAQ
- [ ] Assign to appropriate epic (CHK-012 or new)
- [ ] Regenerate extracted checklist: `python scripts/regen_plan_checklist.py`

#### 6.2 Update Living Docs

**Files to update:**
- [ ] `CHANGELOG.md` - Add entry for new FAQ addition
- [ ] `docs/00_Project_Admin/Progress_Log.md` - Log completion
- [ ] `docs/00_Project_Admin/Decision_Log.md` - Document tier decision
- [ ] `REHYDRATION_PACK/02_CURRENT_STATE.md` - Update completion %

#### 6.3 Update Test Evidence

**File:** `docs/08_Testing_Quality/Test_Evidence_Log.md`

- [ ] Add test evidence entry
- [ ] Include screenshots/logs from staging tests
- [ ] Document success criteria met

---

### Phase 7: Rollout

#### 7.1 Staging Validation

- [ ] Deploy to staging environment
- [ ] Run smoke tests with real-looking test data
- [ ] Verify metrics/logs show correct behavior
- [ ] Test with Support Ops team (shadow mode)

#### 7.2 Production Deployment

- [ ] Obtain final go/no-go approval
- [ ] Deploy to production
- [ ] Monitor metrics for first 24-48 hours
- [ ] Alert Support Ops team of activation

#### 7.3 Post-Launch

- [ ] Monitor deflection rate
- [ ] Track customer satisfaction (if applicable)
- [ ] Review human override rate
- [ ] Adjust confidence thresholds if needed

---

## Tier 2 Automation Additional Steps

If adding a **Tier 2** FAQ (verified auto-reply, not just intake):

### Additional Requirements

- [ ] **Deterministic matching logic** - Define how to verify customer identity
- [ ] **Data source integration** - Implement API calls to fetch required data
- [ ] **Verifier logic** - Add confidence gates and safety checks
- [ ] **Auto-close policy** - Decide if template is eligible for auto-close
- [ ] **Privacy review** - Ensure no PII leakage in automated replies
- [ ] **Fallback paths** - Define what happens when data is missing/ambiguous

### Additional Documentation

- [ ] Update `Decision_Pipeline_and_Gating.md` with new tier gates
- [ ] Add to auto-close whitelist (if eligible)
- [ ] Document allowed variables (what data can be disclosed)
- [ ] Add to `Human_Handoff_and_Escalation.md` for edge cases

---

## Example: Adding "Cancel Order" FAQ

Here's a worked example for adding the "Cancel Order" FAQ:

### 1. Intent Taxonomy
```markdown
### `cancel_order`
**Tier:** 1 (intake only - no auto-cancel in v1)
**Required entities:** order_id, reason (optional)
**Trigger phrases:** "cancel my order", "I want to cancel", "stop my order"
```

### 2. Routing Spec
```markdown
| cancel_order | Email Support Team | mw-intent-cancel-order | Tier 1 only | No auto-cancel (Tier 3 disabled) |
```

### 3. Template (already exists)
- Template ID: `t_cancel_order_ack_intake`
- Purpose: Acknowledge request, ask for order number, explain shipped vs not-shipped

### 4. LLM Integration
- Intent already in `VALID_INTENTS`
- Routing logic already handles it

### 5. Richpanel Rule
- Trigger: Tag `mw-intent-cancel-order` added
- Action: Assign to Email Support Team
- Add tag: `urgent` (if desired)

### 6. Test
- Test case: "I need to cancel order #12345"
- Expected: Intent classified correctly, template sent, routed to Email Support

### 7. Deploy
- Staging first, monitor for 48 hours
- Production rollout with metrics tracking

**Total Time Estimate:** 4-8 hours for Tier 1 FAQ (if template already exists)

---

## Troubleshooting

### Intent Not Classified Correctly

**Symptoms:** Messages routed to wrong department or classified as "unknown"

**Fixes:**
- Add more example phrases to intent taxonomy
- Review LLM prompt for clarity
- Check confidence thresholds
- Verify intent is in validation schema

### Template Not Rendering

**Symptoms:** Variables showing as `{{variable}}` in replies

**Fixes:**
- Verify variable names match between template and data source
- Check required_vars are provided
- Review template renderer logic
- Test with simplified template first

### Routing Fights

**Symptoms:** Ticket assigned to wrong team despite correct tags

**Fixes:**
- Check Richpanel rule ordering (middleware rule should be early)
- Verify "skip subsequent rules" settings
- Review channel-specific rules that may override
- Test with simplified rule set

### Idempotency Issues

**Symptoms:** Duplicate replies sent for same message

**Fixes:**
- Verify deduplication key logic
- Check idempotency table TTL
- Review event envelope structure
- Test with duplicate webhook deliveries

---

## FAQ System Metrics

After adding a new FAQ, track:

- **Coverage rate:** % of tickets matching the new intent
- **Automation rate:** % of matched tickets successfully automated
- **Fallback rate:** % requiring human intervention
- **Customer reply rate:** % of customers replying after auto-response
- **Override rate:** % of times agents change the routing

**Target benchmarks:**
- Coverage: >80% of expected volume
- Automation: >70% for Tier 1, >90% for Tier 2
- Customer satisfaction: No decrease vs. human-only baseline

---

## Maintenance

### Regular Reviews

- **Monthly:** Review classification accuracy and adjust thresholds
- **Quarterly:** Update templates based on customer feedback
- **Annually:** Re-evaluate FAQ priorities based on volume changes

### When to Deprecate

Consider removing or demoting a FAQ automation when:
- Volume drops below 2% of total tickets
- Customer satisfaction decreases
- Error/fallback rate exceeds 30%
- Business process changes make automation invalid

---

## Related Documents

- `Top_FAQs_Playbooks.md` - FAQ definitions and policies
- `Templates_Library_v1.md` - Template specifications
- `Department_Routing_Spec.md` - Routing rules
- `Decision_Pipeline_and_Gating.md` - Automation logic
- `FAQ_Playbook_Test_Cases.md` - Testing requirements

---

**Version:** 1.0  
**Last Updated:** 2026-01-09  
**Owner:** Engineering + Support Ops  
**Review Cycle:** Quarterly or after adding 3 new FAQs

