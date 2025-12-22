# Richpanel AUTO Macro Pack (v1)

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
Copy/paste starter bodies for AUTO macros in Richpanel.

**Important:** Middleware templates use Mustache placeholders. Richpanel may use a different placeholder format.
- If you do not know the Richpanel placeholder name, remove the placeholder line and keep the macro static.

See also:
- `Richpanel_AUTO_Macro_Setup_Checklist.md`
- `templates/richpanel_auto_macro_mapping_v1.csv`

---

## AUTO: Chargeback/Dispute — Neutral Ack

**Source template:** `t_chargeback_neutral_ack` (Tier 0)

**Recommended macro body (static / Richpanel-friendly):**
```text
Thanks for reaching out. We’ve forwarded this to the appropriate team for review and will follow up as soon as possible.
— Customer Support
```

---

## AUTO: Fraud/Suspicious — Ack

**Source template:** `t_fraud_ack` (Tier 0)

**Recommended macro body (static / Richpanel-friendly):**
```text
Thanks for your message. We’ve escalated this for review.
— Customer Support
```

---

## AUTO: Harassment — Ack

**Source template:** `t_harassment_ack` (Tier 0)

**Recommended macro body (static / Richpanel-friendly):**
```text
Your message has been escalated for review.
— Customer Support
```

---

## AUTO: Legal Threat — Ack

**Source template:** `t_legal_threat_ack` (Tier 0)

**Recommended macro body (static / Richpanel-friendly):**
```text
Thanks for your message. We’ve escalated this to the appropriate team for review.
— Customer Support
```

---

## AUTO: Address Change Ack / Intake

**Source template:** `t_address_change_ack_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — we may be able to update that.

Please reply with:
1) your order number, and
2) the full corrected shipping address.

If the order hasn’t shipped yet, we’ll do our best to update it. If it has shipped, we’ll help with the next best steps.
— Customer Support
```

---

## AUTO: Billing Issue Intake

**Source template:** `t_billing_issue_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — we can help with billing.

Please reply with:
1) your order number (if you have one), and
2) what you’re seeing (amount + date).

If you’re sharing screenshots, please remove any full card numbers or sensitive information.
— Customer Support
```

---

## AUTO: Cancel Order Ack / Intake

**Source template:** `t_cancel_order_ack_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — we can try to help with a cancellation.

Please reply with your order number. If the order has not shipped yet, we’ll do our best to cancel it. If it has already shipped, we’ll guide you through the best next option.
— Customer Support
```

---

## AUTO: Cancel Subscription Ack / Intake

**Source template:** `t_cancel_subscription_ack_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — happy to help with your subscription.

Please reply with the email used for the subscription (and any order/subscription details you have). Our team will locate it and assist you with cancellation.
— Customer Support
```

---

## AUTO: Damaged Item — Intake

**Source template:** `t_damaged_item_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — I’m sorry it arrived that way.

Please reply with:
1) your order number
2) clear photos of the damage/defect
3) (if relevant) a short video showing the issue

Once we have this, our support team will review and help with next steps.
— Customer Support
```

---

## AUTO: Delivered-Not-Received — Intake

**Source template:** `t_delivered_not_received_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — I’m sorry you’re dealing with this.

A quick checklist that often resolves “delivered but not received”:
• Check around your delivery area (porch/side door/garage) and with household members
• Check with neighbors or your building office/package room
• If it was marked delivered within the last 24 hours, it may still arrive shortly

When you reply, please include your order number so we can investigate and help with next steps.
— Customer Support
```

---

## AUTO: Exchange Request — Intake

**Source template:** `t_exchange_request_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — we can help with an exchange.

Please reply with your order number and what you’d like to exchange (and the desired replacement item/variant), and we’ll help from there.
— Customer Support
```

---

## AUTO: Influencer/Marketing Inquiry — Route

**Source template:** `t_influencer_inquiry_route` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — thanks for your interest in collaborating.

We’ve routed your message to our partnerships team. Please share your social handle(s) and a link to your media kit if available.
— Customer Support
```

---

## AUTO: Missing Items — Intake

**Source template:** `t_missing_items_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — sorry about that. We’ll help.

Please reply with:
1) your order number
2) which item(s) are missing
3) a photo of what you received (including the packing slip if available)

Once we have that, our team will review and take the next steps.
— Customer Support
```

---

## AUTO: Order Status Ask for Order #

**Source template:** `t_order_status_ask_order_number` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — happy to help with your order status.

To pull up the right order, please reply with:
1) your order number, and
2) the email or phone number used at checkout.

Once we have that, we’ll get you the latest tracking/status right away.
— Customer Support
```

---

## AUTO: Pre‑purchase Info

**Source template:** `t_pre_purchase_info` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — thanks for reaching out!

Can you share what you’re looking for (and any must-haves)? Our team will help you choose the best option.
— Customer Support
```

---

## AUTO: Promo/Discount Info

**Source template:** `t_promo_discount_info` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — happy to help.

If a discount code isn’t applying, common causes include:
• the code is expired
• it doesn’t apply to the items in your cart
• minimum spend requirements
• it can’t be combined with another discount

Reply with the code you tried and the exact message you see, and our team will take a look.
— Customer Support
```

---

## AUTO: Refund Request — Intake

**Source template:** `t_refund_request_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — we can check on that.

Please reply with your order number and any return details you have (if applicable). Our team will review and follow up with the latest status.
— Customer Support
```

---

## AUTO: Return Request — Intake

**Source template:** `t_return_request_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — we can help with a return.

Please reply with your order number and which item(s) you’d like to return, and we’ll guide you through the next steps.
— Customer Support
```

---

## AUTO: Technical Support — Intake

**Source template:** `t_technical_support_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — we’ll help troubleshoot this.

To get started, please reply with:
1) the product/device model (if applicable)
2) what exactly is happening (and any error message)
3) what you’ve tried so far
4) your phone type (iPhone/Android) and app version (if the issue is app-related)

A specialist will review and help you as quickly as possible.
— Customer Support
```

---

## AUTO: Unknown — Ack

**Source template:** `t_unknown_ack` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Thanks for your message — we’re taking a look and will follow up.
— Customer Support
```

---

## AUTO: Wrong Item — Intake

**Source template:** `t_wrong_item_intake` (Tier 1)

**Recommended macro body (static / Richpanel-friendly):**
```text
Hi %First Name% — thanks for letting us know. We’ll fix this.

Please reply with:
1) your order number
2) a photo of the item you received (and the label on the box if possible)
3) what you were expecting to receive

A specialist will review and help with the quickest resolution.
— Customer Support
```

---
