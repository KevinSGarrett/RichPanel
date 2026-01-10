# Department Routing Spec (v1)

Last updated: 2025-12-29  
Status: **Active** (used by prompts + policy engine + implementation)

## Purpose
Define the canonical mapping:

`intent` → `destination team / department` (+ tags) → allowed automation tier.

This spec is used by:
- the LLM routing schema (`mw_decision_v1`)
- the policy engine (Tier 0/1/2/3 gates)
- Richpanel routing configuration (tags + assignment rules)
- QA and offline evaluation labeling

---

## Departments / teams (current + recommended)
User-provided departments:
1. Sales Team
2. Backend Team
3. Technical Support Team
4. Phone Support Team
5. TikTok Support
6. Returns Admin
7. LiveChat Support
8. Leadership Team
9. Social Media Team
10. Email Support Team

Additional recommended queue:
11. **Chargebacks / Disputes Team** (approved by you)

### Reality check: Richpanel team availability
Your Richpanel setup snapshot shows these teams in the UI picker:
- Phone Support Team
- TikTok Support
- Returns Admin
- LiveChat Support
- Leadership Team
- Social Media Team
- Email Support Team

If a destination team is not present in Richpanel (e.g., Sales/Backend/Technical Support), v1 fallback is:
- assign to **Email Support Team** (triage)  
- add a tag like `mw-needs-sales` or `mw-needs-tech-support`

This allows routing intent to remain correct even if team structure changes later.

---

## Routing strategy (recommended)
### 1) Channel-first assignment (existing Richpanel behavior)
Some tenants auto-assign based on channel (e.g., messenger → LiveChat Support).  
We should **not fight** these rules.

### 2) Intent tagging (middleware)
Middleware adds tags like `mw-intent-<intent>` that:
- provide visibility
- can trigger assignment rules (if you choose)
- help QA and analytics

### 3) Limited reassignment
If intent strongly implies a different team (e.g., `delivered_not_received` → Returns Admin), middleware may:
- add a routing tag that a dedicated assignment rule uses to reassign
- or directly set assignee/team via API (only if stable and verified)

---

## Intent → destination mapping

Legend:
- **Tier 0:** escalation; route-only recommended
- **Tier 1:** safe intake/info templates allowed
- **Tier 2:** verified replies allowed (deterministic match required)
- **Tier 3:** auto-actions (disabled in early rollout)

| Intent | Default destination | Tags to add (minimum) | Allowed automation (early rollout) | Notes |
|---|---|---|---|---|
| order_status_tracking | Email Support Team | mw-intent-order-status | Tier 1 + Tier 2 | Tier 2 only with deterministic match; may send ETA when no tracking exists (CR-001) |
| shipping_delay_not_shipped | Email Support Team | mw-intent-shipping-delay | Tier 1 + Tier 2 | No exact dates; ETA window allowed only via approved template (CR-001) |
| delivered_not_received | Returns Admin | mw-intent-dnr | Tier 1 only | Checklist + order # intake |
| missing_items_in_shipment | Returns Admin | mw-intent-missing-items | Tier 1 only | Photo/packing slip intake |
| wrong_item_received | Returns Admin | mw-intent-wrong-item | Tier 1 only | Photo intake |
| damaged_item | Returns Admin | mw-intent-damaged-item | Tier 1 only | Photo/video intake |
| cancel_order | Email Support Team | mw-intent-cancel-order | Tier 1 only | No auto-cancel (Tier 3 disabled) |
| address_change_order_edit | Email Support Team | mw-intent-address-change | Tier 1 only | No auto-edit (Tier 3 disabled) |
| cancel_subscription | Email Support Team | mw-intent-cancel-subscription | Tier 1 only | Gather subscription email/details |
| billing_issue | Email Support Team | mw-intent-billing | Tier 1 only | Warn not to share card details |
| promo_discount_issue | Sales Team (fallback Email Support Team) | mw-intent-promo, mw-needs-sales | Tier 1 only | No code generation |
| pre_purchase_question | Sales Team (fallback Email Support Team) | mw-intent-prepurchase, mw-needs-sales | Tier 1 only | Collect requirements |
| influencer_marketing_inquiry | Social Media Team | mw-intent-influencer | Tier 1 only | Route + request media kit |
| return_request | Returns Admin | mw-intent-return | Tier 1 only | Intake only |
| exchange_request | Returns Admin | mw-intent-exchange | Tier 1 only | Intake only |
| refund_request | Returns Admin | mw-intent-refund | Tier 1 only | Intake only |
| technical_support | Technical Support Team (fallback Email Support Team) | mw-intent-tech-support, mw-needs-tech-support | Tier 1 only | Structured troubleshooting intake |
| phone_support_request | Phone Support Team | mw-intent-phone-support | Route only (or Tier 1 ack) | Usually just route + provide callback instructions |
| tiktok_support_request | TikTok Support | mw-intent-tiktok | Route only (or Tier 1 ack) | Confirm channel specifics later |
| social_media_support_request | Social Media Team | mw-intent-social | Route only (or Tier 1 ack) | Keep public info minimal |
| chargeback_dispute | Chargebacks / Disputes Team | mw-intent-chargeback | Tier 0 | Route-only recommended in v1 |
| legal_threat | Leadership Team | mw-intent-legal | Tier 0 | Route-only recommended |
| harassment_threats | Leadership Team | mw-intent-harassment | Tier 0 | Route-only recommended |
| fraud_suspected | Leadership Team | mw-intent-fraud | Tier 0 | Route-only recommended |
| unknown_other | Email Support Team | mw-intent-unknown | Route only (or disabled ack) | Keep as triage bucket |

---

## Notes on “Backend Team”
If “Backend Team” is intended for:
- Shopify order edits
- app backend issues
- internal technical escalations

Then we should decide whether this is:
- a real Richpanel team (recommended for clarity), or
- an internal escalation outside Richpanel (then use tags + a secondary workflow).

Wave 06+ will cover secure integrations for internal escalations if needed.

