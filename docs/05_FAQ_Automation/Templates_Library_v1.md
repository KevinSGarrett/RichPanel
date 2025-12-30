# Templates Library (v1)

Last updated: 2025-12-29  
Owner: PM (documentation) / Support Ops (approval)

## Source of truth
- `docs/05_FAQ_Automation/templates/templates_v1.yaml`

## Notes
- The middleware must **render templates**; the LLM outputs `template_id` only.
- LiveChat variants are kept short; Email uses `default` unless an `email` variant is added.


---

### `t_order_status_verified`

- **Tier:** 2
- **Enabled v1:** True

- **Purpose:** Provide verified order status and (if available) tracking details for a deterministically-matched order.

- **Required vars:** `order_id, order_status`

- **Optional vars:** `first_name, fulfillment_status, tracking_url, tracking_number, tracking_company, status_url`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — thanks for reaching out.

Here’s the latest update for your order {{order_id}}:
• Status: {{order_status}}{{#fulfillment_status}} ({{fulfillment_status}}){{/fulfillment_status}}

{{#status_url}}
Order status link:
• {{status_url}}
{{/status_url}}

{{#tracking_url}}
Tracking:
• {{#tracking_company}}{{tracking_company}}{{/tracking_company}}{{#tracking_number}} — {{tracking_number}}{{/tracking_number}}
• {{tracking_url}}
{{/tracking_url}}

If anything looks off, just reply here and our team will jump in to help.
— {{support_signature}}
```


**Channel: livechat**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}}! Order {{order_id}} is currently: {{order_status}}.
{{#tracking_url}}Tracking: {{tracking_url}}{{/tracking_url}}
Reply here if you need help.
```


---

### `t_shipping_delay_verified`

- **Tier:** 2
- **Enabled v1:** True

- **Purpose:** Acknowledge shipping delay / not shipped yet, stating only verified order facts and routing to a specialist.

- **Required vars:** `order_id, order_status, fulfillment_status`

- **Optional vars:** `first_name, order_created_at, support_hours_note`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — thanks for checking in.

I’m seeing order {{order_id}} is currently marked as {{order_status}}{{#fulfillment_status}} ({{fulfillment_status}}){{/fulfillment_status}}, and it has not been marked as shipped yet.

A support specialist will review this and follow up. If you have any extra context (needed-by date, address issues, etc.), reply here and we’ll take it from there.
— {{support_signature}}
```


**Channel: livechat**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}}! Order {{order_id}} is currently {{order_status}}{{#fulfillment_status}} ({{fulfillment_status}}){{/fulfillment_status}} and isn’t marked as shipped yet. If you have a needed-by date or address concern, reply here and we’ll help.
```


---


### `t_order_eta_no_tracking_verified`

- **Tier:** 2
- **Enabled v1:** True

- **Purpose:** Provide a conservative delivery window when no tracking exists yet (derived from verified order date + shipping bucket). Auto-close eligible when within SLA.

- **Required vars:** `order_id, shipping_bucket, eta_remaining_human`

- **Optional vars:** `first_name, order_created_date_human`

**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — thanks for checking in.

I’m not seeing a tracking number for order {{order_id}} yet. Tracking is sent once your package is boxed and shipped.

Based on your {{shipping_bucket}} shipping and the date your order was placed{{#order_created_date_human}} ({{order_created_date_human}}){{/order_created_date_human}}, your order is expected to arrive in {{eta_remaining_human}}.

I’m going to mark this as resolved for now. If you have any questions or if the order doesn’t arrive by the end of that window, reply to this message and we’ll jump back in.

— {{support_signature}}
```

**Channel: livechat**

```text
Thanks{{#first_name}} {{first_name}}{{/first_name}}. I’m not seeing tracking for order {{order_id}} yet. Based on {{shipping_bucket}} shipping, it should arrive in {{eta_remaining_human}}. I’ll mark this resolved for now — reply here anytime to reopen.
```

### `t_order_status_ask_order_number`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Ask for order number + email/phone so a human or system can securely locate the right order.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — happy to help with your order status.

To pull up the right order, please reply with:
1) your order number, and
2) the email or phone number used at checkout.

Once we have that, we’ll get you the latest tracking/status right away.
— {{support_signature}}
```


**Channel: livechat**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}}! To check your order status, please send your order # and the email or phone used at checkout.
```


---

### `t_delivered_not_received_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Provide a short DNR checklist and request order number for investigation; always route to human.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — I’m sorry you’re dealing with this.

A quick checklist that often resolves “delivered but not received”:
• Check around your delivery area (porch/side door/garage) and with household members
• Check with neighbors or your building office/package room
• If it was marked delivered within the last 24 hours, it may still arrive shortly

When you reply, please include your order number so we can investigate and help with next steps.
— {{support_signature}}
```


**Channel: livechat**

```text
Sorry about that — I can help. Please send your order # and confirm your shipping address/city. Also, have you checked neighbors/mailroom/front desk? We’ll investigate and follow up.
```


---

### `t_missing_items_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Collect info/photos for missing items; always route to human.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — sorry about that. We’ll help.

Please reply with:
1) your order number
2) which item(s) are missing
3) a photo of what you received (including the packing slip if available)

Once we have that, our team will review and take the next steps.
— {{support_signature}}
```


**Channel: livechat**

```text
Sorry about that. Please send your order # and list which items are missing. If you can, attach a photo of what you received and the packing slip/label. We’ll take it from there.
```


---

### `t_wrong_item_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Collect photos/details for wrong item; always route to human.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — thanks for letting us know. We’ll fix this.

Please reply with:
1) your order number
2) a photo of the item you received (and the label on the box if possible)
3) what you were expecting to receive

A specialist will review and help with the quickest resolution.
— {{support_signature}}
```


**Channel: livechat**

```text
Thanks — please send your order #, what you expected vs what you received, and (if possible) a photo of the item/packing slip. We’ll help with next steps.
```


---

### `t_damaged_item_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Collect photos/video for damaged/defective item; always route to human.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — I’m sorry it arrived that way.

Please reply with:
1) your order number
2) clear photos of the damage/defect
3) (if relevant) a short video showing the issue

Once we have this, our support team will review and help with next steps.
— {{support_signature}}
```


**Channel: livechat**

```text
Sorry your item arrived damaged. Please send your order # and a photo of the damage + packaging. We’ll review and follow up with next steps.
```


---

### `t_cancel_order_ack_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Acknowledge cancellation request, request order number, avoid promising cancellation.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — we can try to help with a cancellation.

Please reply with your order number. If the order has not shipped yet, we’ll do our best to cancel it. If it has already shipped, we’ll guide you through the best next option.
— {{support_signature}}
```


**Channel: livechat**

```text
I can help with a cancellation request. Please send your order #. If it hasn’t shipped yet, we may be able to cancel; if it already shipped, we’ll share the best next step.
```


---

### `t_address_change_ack_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Acknowledge address change request; ask for order number and full corrected address.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — we may be able to update that.

Please reply with:
1) your order number, and
2) the full corrected shipping address.

If the order hasn’t shipped yet, we’ll do our best to update it. If it has shipped, we’ll help with the next best steps.
— {{support_signature}}
```


**Channel: livechat**

```text
Got it — please send your order # and the full corrected shipping address. If it hasn’t shipped yet, we’ll try to update it; otherwise we’ll advise next steps.
```


---

### `t_cancel_subscription_ack_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Acknowledge subscription cancellation request; ask for subscription email/details.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — happy to help with your subscription.

Please reply with the email used for the subscription (and any order/subscription details you have). Our team will locate it and assist you with cancellation.
— {{support_signature}}
```


**Channel: livechat**

```text
Please share the email associated with the subscription (and any order/subscription number if you have it). We’ll get this routed and help you cancel.
```


---

### `t_billing_issue_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Collect minimal billing info; warn customer not to share full card numbers.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — we can help with billing.

Please reply with:
1) your order number (if you have one), and
2) what you’re seeing (amount + date).

If you’re sharing screenshots, please remove any full card numbers or sensitive information.
— {{support_signature}}
```


**Channel: livechat**

```text
Happy to help. Please share your order # and a brief description of the billing issue (do not include full card details). We’ll investigate and follow up.
```


---

### `t_return_request_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Collect return request info; route to Returns Admin.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — we can help with a return.

Please reply with your order number and which item(s) you’d like to return, and we’ll guide you through the next steps.
— {{support_signature}}
```


**Channel: livechat**

```text
To start a return, please share your order #, the items you’d like to return, and the reason. We’ll reply with next steps.
```


---

### `t_exchange_request_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Collect exchange request info; route to Returns Admin.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — we can help with an exchange.

Please reply with your order number and what you’d like to exchange (and the desired replacement item/variant), and we’ll help from there.
— {{support_signature}}
```


**Channel: livechat**

```text
To start an exchange, please share your order #, the item you want to exchange, and what you’d like instead (size/color/etc.). We’ll reply with next steps.
```


---

### `t_refund_request_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Collect refund status request info; route to Returns Admin or billing team.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — we can check on that.

Please reply with your order number and any return details you have (if applicable). Our team will review and follow up with the latest status.
— {{support_signature}}
```


**Channel: livechat**

```text
To help with a refund request, please share your order # and a short reason for the refund. We’ll review and follow up.
```


---

### `t_technical_support_intake`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Collect troubleshooting intake info for product/app issues; route to Technical Support (or fallback tags).

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — we’ll help troubleshoot this.

To get started, please reply with:
1) the product/device model (if applicable)
2) what exactly is happening (and any error message)
3) what you’ve tried so far
4) your phone type (iPhone/Android) and app version (if the issue is app-related)

A specialist will review and help you as quickly as possible.
— {{support_signature}}
```


**Channel: livechat**

```text
Sorry you’re running into trouble. What product/device are you using, and what’s happening? If you can, include a screenshot/video and what troubleshooting you’ve tried.
```


---

### `t_promo_discount_info`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Provide general promo troubleshooting; do not generate new codes.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — happy to help.

If a discount code isn’t applying, common causes include:
• the code is expired
• it doesn’t apply to the items in your cart
• minimum spend requirements
• it can’t be combined with another discount

Reply with the code you tried and the exact message you see, and our team will take a look.
— {{support_signature}}
```


**Channel: livechat**

```text
Happy to help with discounts. Which item are you looking at, and do you have a promo code you’re trying to apply?
```


---

### `t_pre_purchase_info`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Acknowledge pre-purchase questions and gather requirements for Sales/Support.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — thanks for reaching out!

Can you share what you’re looking for (and any must-haves)? Our team will help you choose the best option.
— {{support_signature}}
```


**Channel: livechat**

```text
Happy to help before you order. What product are you considering and what questions do you have (size, compatibility, shipping, etc.)?
```


---

### `t_influencer_inquiry_route`

- **Tier:** 1
- **Enabled v1:** True

- **Purpose:** Acknowledge influencer inquiry and request media kit; route to Social Media.

- **Required vars:** _(none)_

- **Optional vars:** `first_name`


**Channel: default**

```text
Hi{{#first_name}} {{first_name}}{{/first_name}} — thanks for your interest in collaborating.

We’ve routed your message to our partnerships team. Please share your social handle(s) and a link to your media kit if available.
— {{support_signature}}
```


**Channel: livechat**

```text
Thanks for reaching out! Please share your social handle(s), platform, and a link to your profile. If you have a media kit, feel free to attach it — we’ll route this to the right team.
```


---

### `t_chargeback_neutral_ack`

- **Tier:** 0
- **Enabled v1:** False

- **Purpose:** Neutral acknowledgement for chargeback/dispute; recommended route-only in early rollout.

- **Required vars:** _(none)_

- **Optional vars:** _(none)_


**Channel: default**

```text
Thanks for reaching out. We’ve forwarded this to the appropriate team for review and will follow up as soon as possible.
— {{support_signature}}
```


---

### `t_legal_threat_ack`

- **Tier:** 0
- **Enabled v1:** False

- **Purpose:** Neutral acknowledgement for legal threats; recommended route-only in early rollout.

- **Required vars:** _(none)_

- **Optional vars:** _(none)_


**Channel: default**

```text
Thanks for your message. We’ve escalated this to the appropriate team for review.
— {{support_signature}}
```


---

### `t_harassment_ack`

- **Tier:** 0
- **Enabled v1:** False

- **Purpose:** Neutral acknowledgement for harassment; recommended route-only in early rollout.

- **Required vars:** _(none)_

- **Optional vars:** _(none)_


**Channel: default**

```text
Your message has been escalated for review.
— {{support_signature}}
```


---

### `t_fraud_ack`

- **Tier:** 0
- **Enabled v1:** False

- **Purpose:** Neutral acknowledgement for suspected fraud; recommended route-only in early rollout.

- **Required vars:** _(none)_

- **Optional vars:** _(none)_


**Channel: default**

```text
Thanks for your message. We’ve escalated this for review.
— {{support_signature}}
```


---

### `t_unknown_ack`

- **Tier:** 1
- **Enabled v1:** False

- **Purpose:** Generic acknowledgement; keep disabled unless needed.

- **Required vars:** _(none)_

- **Optional vars:** _(none)_


**Channel: default**

```text
Thanks for your message — we’re taking a look and will follow up.
— {{support_signature}}
```
