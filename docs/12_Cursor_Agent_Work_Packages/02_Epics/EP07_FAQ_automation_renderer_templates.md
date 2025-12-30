# EP07 — FAQ automation renderer + templates

Last updated: 2025-12-23

## Purpose

Implement template-based automation where the model chooses a template_id but cannot write customer-facing text.


## Ticket list

- [W12-EP07-T070 — Implement template renderer (YAML templates + brand constants) with safe placeholder handling](../03_Tickets/W12-EP07-T070_Implement_template_renderer_YAML_templates_brand_constants_with_safe_placeholder.md)
- [W12-EP07-T071 — Enforce template catalog: allowed template_ids, per-channel enablement, per-template feature flags](../03_Tickets/W12-EP07-T071_Enforce_template_catalog_allowed_template_ids_per_channel_enablement_per_templat.md)
- [W12-EP07-T072 — Implement Tier 1 safe-assist automation playbooks (DNR, missing items intake, refunds intake) + routing tags](../03_Tickets/W12-EP07-T072_Implement_Tier_1_safe_assist_automation_playbooks_DNR_missing_items_intake_refun.md)
- [W12-EP07-T073 — Implement Tier 2 verified order status auto-reply (tracking link/number) with deterministic match + verifier approval](../03_Tickets/W12-EP07-T073_Implement_Tier_2_verified_order_status_auto_reply_tracking_link_number_with_dete.md)
- [W12-EP07-T074 — Enforce 'auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception)' invariant across all automation paths](../03_Tickets/W12-EP07-T074_Enforce_never_auto_close_invariant_across_all_automation_paths.md)
- [W12-EP07-T075 — Create Richpanel 'AUTO:' macros aligned to template IDs (ops task) and document governance](../03_Tickets/W12-EP07-T075_Create_Richpanel_AUTO_macros_aligned_to_template_IDs_ops_task_and_document_gover.md)


## Dependencies

- EP06 + EP05 required for Tier2.
- EP04 action executor required.
