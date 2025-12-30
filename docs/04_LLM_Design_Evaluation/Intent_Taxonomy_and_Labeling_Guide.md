# Intent Taxonomy and Labeling Guide (v1)

Last updated: 2025-12-22  
Last verified: 2025-12-22 — Expanded to align with `Department_Routing_Spec.md` + Top FAQs (RoughDraft).

## Purpose
This document defines the **v1 intent taxonomy** used by the routing model and the offline evaluation/labeling process.

It connects:
- customer language → **intent label**
- intent label → **destination team/queue**
- intent label → **automation tier policy** (Tier 0/1/2/3)

This taxonomy is designed to be:
- **stable** (does not change weekly)
- **operationally aligned** (maps to your actual teams)
- **model-friendly** (labels are mutually distinct enough to classify reliably)
- **expandable** (v1 can grow to v2 without breaking everything)

## Related documents
- **Golden set labeling SOP:** `Golden_Set_Labeling_SOP.md` (how we label + QA + version datasets)
- **Multi-intent priority rules:** `Multi_Intent_Priority_Matrix.md` (how we pick the primary intent when messages include multiple intents)
- **Template ID interface:** `Template_ID_Catalog.md` (IDs only; copy finalized in Wave 05)

---
## Routing targets (teams/queues)
Current department list (given):
1. Sales Team  
2. Backend Team  
3. Technical Support Team  
4. Phone Support Team  
5. TikTok Support  
6. Returns Admin  
7. LiveChat Support  
8. Leadership Team  
9. SocialMedia Team  
10. Email Support Team  

Additional routing target (approved earlier):
11. **Chargebacks / Disputes Team** (new team/channel)

---

## Intent principles (v1)

### 1) One primary intent + up to 2 secondary intents
- **Primary intent**: what determines the destination team and (if applicable) automation tier.
- **Secondary intents**: captured when the message includes multiple issues (e.g., “where is my order + change address”).

### 2) Escalations override everything
If the message indicates:
- chargeback/dispute
- legal threat
- harassment/threats
- fraud indicators

In that case, routing is Tier 0 and goes to the escalation team regardless of other content.

### 3) Prefer “policy-safe” granularity
We intentionally separate:
- **order status & tracking** (can be Tier 2 verified automation)
from:
- **returns/refunds/exchanges** (high risk; mostly Tier 1 + route)
from:
- **cancel/edit order** (Tier 3 actions later; early rollout = route + safe acknowledgement only)

---

## Automation tier policy link (reminder)
- **Tier 0 — Safety / escalation**: never auto-send substantive content beyond a neutral acknowledgment.
- **Tier 1 — Safe-assist**: may ask clarifying questions; may provide general policy info; never disclose private order details unless deterministic match.
- **Tier 2 — Verified automation**: allowed only when deterministic match exists (Richpanel↔Shopify link) and the response is template-based.
- **Tier 3 — Auto-actions**: refunds/cancellations/exchanges/reships (not in early rollout).

---

## v1 intents (expanded set aligned to Top FAQs)

### A) Order status & shipping (highest volume)
1) `order_status_tracking`
   - “Where is my order?”, “tracking?”, “status?”, “when will it arrive?”
   - Default destination: **Email Support Team**  
   - Tier policy:
     - Tier 1: ask for order # / email if missing
     - Tier 2: verified reply with tracking **only if deterministic match exists**
2) `shipping_delay_not_shipped`
   - “Label created”, “hasn’t shipped”, “stuck in pre-shipment”, “no movement”
   - Default destination: **Email Support Team**
   - Tier policy: Tier 1 + Tier 2 (only if deterministic match exists)
3) `delivered_not_received`
   - “It says delivered but I didn’t get it”
   - Default destination: **Returns Admin**
   - Tier policy: Tier 1 safe intake only; always route to human
4) `missing_items_in_shipment`
   - Package arrived, items missing
   - Default destination: **Returns Admin**
   - Tier policy: Tier 1 intake questions only (no resolution)
5) `wrong_item_received`
   - Incorrect item / wrong variant received
   - Default destination: **Returns Admin**
   - Tier policy: Tier 1 intake only
6) `damaged_item`
   - Arrived damaged / defective on arrival
   - Default destination: **Returns Admin**
   - Tier policy: Tier 1 intake only

### B) Order edits, cancellations, subscription, and billing
7) `cancel_order`
   - “Cancel my order”, “stop shipment”
   - Default destination: **Email Support Team**
   - Tier policy: Tier 1 acknowledgement + required info; **no Tier 3 auto-cancel in early rollout**
8) `address_change_order_edit`
   - “Change my address”, “edit my order”, “wrong shipping address”
   - Default destination: **Email Support Team**
   - Tier policy: Tier 1 acknowledgement + required info; Tier 3 later
9) `cancel_subscription`
   - “Cancel my subscription”, “pause/skip subscription”, “stop future shipments”
   - Default destination: **Email Support Team**
   - Tier policy: Tier 1 intake + route (no auto actions in early rollout)
10) `billing_issue`
   - “Charged twice”, “payment failed”, “incorrect charge”
   - Default destination: **Email Support Team**
   - Tier policy: Tier 1 intake + route (no automation beyond intake)

### C) Sales, promos, and marketing
11) `promo_discount_issue`
   - “Discount code not working”, “promo”, “coupon”
   - Default destination: **Sales Team** (or Email Support if Sales queue is not staffed)
   - Tier policy: Tier 1 allowed (general guidance), but avoid commitments
12) `pre_purchase_question`
   - Pre-sale questions: pricing, product compatibility, “which model should I buy?”
   - Default destination: **Sales Team**
   - Tier policy: Tier 1 allowed (general info only); avoid over-promising
13) `influencer_marketing_inquiry`
   - “Influencer inquiry”, partnerships, collaborations
   - Default destination: **SocialMedia Team** (or Leadership if your org prefers)
   - Tier policy: route-only (no automation)

### D) Returns / refunds / exchanges
14) `return_request`
   - “I want to return”, “refund”, “return label”
   - Default destination: **Returns Admin**
   - Tier policy: Tier 1 intake only (no auto-approve)
15) `exchange_request`
   - “Exchange”, “swap for different size/model”
   - Default destination: **Returns Admin**
   - Tier policy: Tier 1 intake only
16) `refund_request`
   - “Refund me”, “I want my money back”
   - Default destination: **Returns Admin**
   - Tier policy: Tier 1 intake only

### E) Technical support
17) `technical_support`
   - Product/app troubleshooting, setup issues, “not misting”, connectivity, app errors
   - Default destination: **Technical Support Team**
   - Tier policy: Tier 1 troubleshooting questions + route (no guaranteed fix promises)

### F) Channel-first intents (source channel implies destination)
18) `phone_support_request`
   - Customer explicitly asks for a call or phone support
   - Default destination: **Phone Support Team**
19) `tiktok_support_request`
   - TikTok channel support request
   - Default destination: **TikTok Support**
20) `social_media_support_request`
   - Instagram/FB/other social channel support request
   - Default destination: **SocialMedia Team**

### G) High risk / escalations (Tier 0)
21) `chargeback_dispute`
   - “Chargeback”, “dispute”, “bank reversed”, “I filed a claim”
   - Default destination: **Chargebacks / Disputes Team**
   - Tier policy: Tier 0 (no automation beyond neutral acknowledgment)
22) `legal_threat`
   - “Lawyer”, “lawsuit”, “legal action”, “reporting to AG”
   - Default destination: **Leadership Team**
   - Tier policy: Tier 0
23) `harassment_threats`
   - Threats, harassment, hate, doxxing attempts
   - Default destination: **Leadership Team**
   - Tier policy: Tier 0
24) `fraud_suspected`
   - Fraud indicators (identity mismatch claims, “not my order”, suspicious patterns)
   - Default destination: **Leadership Team** (or Backend Team depending on org)
   - Tier policy: Tier 0

### H) Unknown / fallback
25) `unknown_other`
   - Not enough signal / unclear
   - Default destination depends on channel:
     - LiveChat → LiveChat Support
     - Email → Email Support Team
     - TikTok/Social → corresponding channel teams
   - Tier policy: route-only

---

## Labeling rules (for dataset creation)

### Rule 1 — Choose the primary intent that determines the *right team*
- If the message contains two intents but one clearly demands a specialist team (e.g., technical support), that becomes primary.
- If one intent is time-sensitive (address change / cancel order), that becomes primary.

### Rule 2 — Escalations override
If any Tier 0 escalation is present, label primary as that escalation intent.

### Rule 3 — Multi-issue messages
If two issues are both strong, label:
- primary intent = the one that requires the most urgent handling
- secondary intent(s) = the other(s)

### Rule 4 — Ambiguity
If you cannot determine intent from the first message:
- label `unknown_other`
- note what clarifying question would resolve it

---

## Mapping to route tags (v1)
We will tag conversations with:
- `mw-intent-<primary_intent>`
- `mw-routing-applied`
Optional:
- `mw-secondary-<intent>` for up to 2 secondaries
- `mw-needs-triage` when confidence is low

---

## Notes (alignment)
This taxonomy is the **source of truth** for:
- `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`
- `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`
- `docs/04_LLM_Design_Evaluation/Offline_Evaluation_Framework.md`

If you change intent names, update **all three** and bump schema version.
