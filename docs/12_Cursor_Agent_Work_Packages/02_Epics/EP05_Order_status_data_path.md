# EP05 — Order status data path

Last updated: 2025-12-23

## Purpose

Implement deterministic order lookup and tracking disclosure gates using Richpanel (and optional Shopify fallback).


## Ticket list

- [W12-EP05-T050 — Implement deterministic order linkage lookup using Richpanel order endpoints](../03_Tickets/W12-EP05-T050_Implement_deterministic_order_linkage_lookup_using_Richpanel_order_endpoints.md)
- [W12-EP05-T051 — Map order details into template variables and handle common edge cases (multiple fulfillments)](../03_Tickets/W12-EP05-T051_Map_order_details_into_template_variables_and_handle_common_edge_cases_multiple_.md)
- [W12-EP05-T052 — Implement Shopify Admin API fallback (only if required and credentials exist)](../03_Tickets/W12-EP05-T052_Implement_Shopify_Admin_API_fallback_only_if_required_and_credentials_exist.md)
- [W12-EP05-T053 — Define and implement order-status-related routing rules (DNR, missing items, refund requests)](../03_Tickets/W12-EP05-T053_Define_and_implement_order_status_related_routing_rules_DNR_missing_items_refund.md)


## Dependencies

- EP04 client required.
- Tier 2 gating depends on EP06.
