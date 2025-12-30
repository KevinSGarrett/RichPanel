# Template ID Catalog (interface contract)

Last updated: 2025-12-29  
Owner: Wave 04 (interface) + Wave 05 (copy)

## Purpose
The LLM may only select from these `template_id` values.

- The LLM **does not** write customer-facing copy.
- The middleware renders copy from:
  - `docs/05_FAQ_Automation/templates/templates_v1.yaml`
  - `docs/05_FAQ_Automation/Templates_Library_v1.md`

This file is the stable “interface contract” used by:
- prompt outputs (`mw_decision_v1`)
- policy engine allowlists/denylists
- regression tests

---

## `template_id` values (v1)

### Tier 2 — Verified
These can only be sent when deterministic match is true.

- `t_order_status_verified`
- `t_shipping_delay_verified`
- `t_order_eta_no_tracking_verified`

### Tier 1 — Intake / Info
Safe to send without disclosing order-specific details.

- `t_order_status_ask_order_number`
- `t_delivered_not_received_intake`
- `t_missing_items_intake`
- `t_wrong_item_intake`
- `t_damaged_item_intake`
- `t_cancel_order_ack_intake`
- `t_address_change_ack_intake`
- `t_cancel_subscription_ack_intake`
- `t_billing_issue_intake`
- `t_return_request_intake`
- `t_exchange_request_intake`
- `t_refund_request_intake`
- `t_technical_support_intake`
- `t_promo_discount_info`
- `t_pre_purchase_info`
- `t_influencer_inquiry_route`

### Tier 0 — Escalation acknowledgements (disabled by default)
Recommended route-only in early rollout.

- `t_chargeback_neutral_ack`
- `t_legal_threat_ack`
- `t_harassment_ack`
- `t_fraud_ack`

### Disabled / generic
- `t_unknown_ack` (disabled by default; route-only recommended)

### Null value
- `null` / `None` — means “do not send an auto-reply” (route only).

---

## Change management
Any change to the allowed set of template IDs is a breaking change and requires:
- schema update (`mw_decision_v1.schema.json`)
- template library update (copy)
- regression tests update
- Decision Log entry

Copy-only changes (text edits) do not require schema changes, but still require:
- template YAML update
- Decision Log entry
