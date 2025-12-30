# Tickets Index (Wave 12)

Last updated: 2025-12-23

This index lists every build ticket in Wave 12, grouped by epic.

## Planning aids
- Sprint plan: `../00_Overview/Implementation_Sequence_Sprints.md`
- V1 cutline: `../00_Overview/V1_Cutline_and_Backlog.md`
- Ticket CSV: `../assets/tickets_v1.csv`
- Sprint CSV: `../assets/sprint_plan_v1.csv`
- Jira import: `../00_Overview/Jira_Import_Instructions.md`



## EP00 — Preflight access + tenant verification

- [W12-EP00-T001 — Inventory required access + secrets (Richpanel API key, Shopify access) and define secret storage plan](./W12-EP00-T001_Inventory_required_access_secrets_Richpanel_API_key_Shopify_access_and_define_se.md)
- [W12-EP00-T002 — Verify Richpanel tenant automation capabilities needed for middleware trigger (deferred Wave 03 items)](./W12-EP00-T002_Verify_Richpanel_tenant_automation_capabilities_needed_for_middleware_trigger_de.md)
- [W12-EP00-T003 — Sample order linkage reality in tenant (Richpanel order endpoints) without storing PII](./W12-EP00-T003_Sample_order_linkage_reality_in_tenant_Richpanel_order_endpoints_without_storing.md)
- [W12-EP00-T004 — Finalize webhook authentication approach and rotation strategy (based on tenant verification)](./W12-EP00-T004_Finalize_webhook_authentication_approach_and_rotation_strategy_based_on_tenant_v.md)

## EP01 — AWS foundation

- [W12-EP01-T010 — Set up AWS Organization and create dev/staging/prod accounts (Organizations-only)](./W12-EP01-T010_Set_up_AWS_Organization_and_create_dev_staging_prod_accounts_Organizations_only.md)
- [W12-EP01-T011 — Create IAM roles and least-privilege policies for middleware (ingress vs worker) and CI deploy](./W12-EP01-T011_Create_IAM_roles_and_least_privilege_policies_for_middleware_ingress_vs_worker_a.md)
- [W12-EP01-T012 — Enable baseline logging + audit (CloudTrail, CloudWatch log retention, budgets, alarms)](./W12-EP01-T012_Enable_baseline_logging_audit_CloudTrail_CloudWatch_log_retention_budgets_alarms.md)
- [W12-EP01-T013 — Create Secrets Manager + SSM parameter namespaces for env config (including kill switch flags)](./W12-EP01-T013_Create_Secrets_Manager_SSM_parameter_namespaces_for_env_config_including_kill_sw.md)

## EP02 — IaC + CI/CD foundation

- [W12-EP02-T020 — Select IaC tool and scaffold infrastructure repo modules (serverless stack)](./W12-EP02-T020_Select_IaC_tool_and_scaffold_infrastructure_repo_modules_serverless_stack.md)
- [W12-EP02-T021 — Create CI pipeline with quality gates (unit tests, schema validation, lint, security checks)](./W12-EP02-T021_Create_CI_pipeline_with_quality_gates_unit_tests_schema_validation_lint_security.md)
- [W12-EP02-T022 — Implement deployment promotion flow (dev → staging → prod) and rollback automation](./W12-EP02-T022_Implement_deployment_promotion_flow_dev_staging_prod_and_rollback_automation.md)

## EP03 — Middleware core pipeline

- [W12-EP03-T030 — Implement API Gateway + ingress Lambda (fast ACK, validation, enqueue)](./W12-EP03-T030_Implement_API_Gateway_ingress_Lambda_fast_ACK_validation_enqueue.md)
- [W12-EP03-T031 — Provision SQS FIFO + DLQ and internal message schema (conversation-ordered processing)](./W12-EP03-T031_Provision_SQS_FIFO_DLQ_and_internal_message_schema_conversation_ordered_processi.md)
- [W12-EP03-T032 — Create DynamoDB tables for idempotency + minimal conversation state with TTL](./W12-EP03-T032_Create_DynamoDB_tables_for_idempotency_minimal_conversation_state_with_TTL.md)
- [W12-EP03-T033 — Implement worker Lambda skeleton (dequeue, fetch context, decision pipeline placeholder, action stub)](./W12-EP03-T033_Implement_worker_Lambda_skeleton_dequeue_fetch_context_decision_pipeline_placeho.md)
- [W12-EP03-T034 — Implement runtime feature flags (safe_mode, automation_enabled, per-template toggles) with caching](./W12-EP03-T034_Implement_runtime_feature_flags_safe_mode_automation_enabled_per_template_toggle.md)
- [W12-EP03-T035 — Implement observability event logging + correlation IDs (ingress and worker)](./W12-EP03-T035_Implement_observability_event_logging_correlation_IDs_ingress_and_worker.md)
- [W12-EP03-T036 — Implement vendor retry/backoff utilities and concurrency bounds (prevent rate-limit storms)](./W12-EP03-T036_Implement_vendor_retry_backoff_utilities_and_concurrency_bounds_prevent_rate_lim.md)

## EP04 — Richpanel integration

- [W12-EP04-T040 — Create Richpanel team + tags (Chargebacks/Disputes, mw-routing-applied, feedback tags) and document mapping](./W12-EP04-T040_Create_Richpanel_team_tags_Chargebacks_Disputes_mw_routing_applied_feedback_tags.md)
- [W12-EP04-T041 — Configure Richpanel automation to trigger middleware on inbound customer messages (avoid loops)](./W12-EP04-T041_Configure_Richpanel_automation_to_trigger_middleware_on_inbound_customer_message.md)
- [W12-EP04-T042 — Implement Richpanel API client with retries, pagination, and rate-limit handling](./W12-EP04-T042_Implement_Richpanel_API_client_with_retries_pagination_and_rate_limit_handling.md)
- [W12-EP04-T043 — Implement action executor (route/tag/assign/reply) with action-level idempotency keys](./W12-EP04-T043_Implement_action_executor_route_tag_assign_reply_with_action_level_idempotency_k.md)
- [W12-EP04-T044 — Build integration test harness for Richpanel actions (staging recommended)](./W12-EP04-T044_Build_integration_test_harness_for_Richpanel_actions_staging_recommended.md)

## EP05 — Order status data path

- [W12-EP05-T050 — Implement deterministic order linkage lookup using Richpanel order endpoints](./W12-EP05-T050_Implement_deterministic_order_linkage_lookup_using_Richpanel_order_endpoints.md)
- [W12-EP05-T051 — Map order details into template variables and handle common edge cases (multiple fulfillments)](./W12-EP05-T051_Map_order_details_into_template_variables_and_handle_common_edge_cases_multiple_.md)
- [W12-EP05-T052 — Implement Shopify Admin API fallback (only if required and credentials exist)](./W12-EP05-T052_Implement_Shopify_Admin_API_fallback_only_if_required_and_credentials_exist.md)
- [W12-EP05-T053 — Define and implement order-status-related routing rules (DNR, missing items, refund requests)](./W12-EP05-T053_Define_and_implement_order_status_related_routing_rules_DNR_missing_items_refund.md)

## EP06 — LLM routing + policy engine

- [W12-EP06-T060 — Implement classifier model call with strict schema validation (mw_decision_v1) and fail-closed fallback](./W12-EP06-T060_Implement_classifier_model_call_with_strict_schema_validation_mw_decision_v1_and.md)
- [W12-EP06-T061 — Implement policy engine (Tier 0 overrides, Tier 2 eligibility, Tier 3 disabled) as authoritative layer](./W12-EP06-T061_Implement_policy_engine_Tier_0_overrides_Tier_2_eligibility_Tier_3_disabled_as_a.md)
- [W12-EP06-T062 — Implement Tier 2 verifier call (mw_tier2_verifier_v1) and integrate into policy gating](./W12-EP06-T062_Implement_Tier_2_verifier_call_mw_tier2_verifier_v1_and_integrate_into_policy_ga.md)
- [W12-EP06-T063 — Implement confidence threshold configuration + calibration workflow hooks](./W12-EP06-T063_Implement_confidence_threshold_configuration_calibration_workflow_hooks.md)
- [W12-EP06-T064 — Integrate offline eval harness into CI (golden set run + regression gates)](./W12-EP06-T064_Integrate_offline_eval_harness_into_CI_golden_set_run_regression_gates.md)

## EP07 — FAQ automation renderer + templates

- [W12-EP07-T070 — Implement template renderer (YAML templates + brand constants) with safe placeholder handling](./W12-EP07-T070_Implement_template_renderer_YAML_templates_brand_constants_with_safe_placeholder.md)
- [W12-EP07-T071 — Enforce template catalog: allowed template_ids, per-channel enablement, per-template feature flags](./W12-EP07-T071_Enforce_template_catalog_allowed_template_ids_per_channel_enablement_per_templat.md)
- [W12-EP07-T072 — Implement Tier 1 safe-assist automation playbooks (DNR, missing items intake, refunds intake) + routing tags](./W12-EP07-T072_Implement_Tier_1_safe_assist_automation_playbooks_DNR_missing_items_intake_refun.md)
- [W12-EP07-T073 — Implement Tier 2 verified order status auto-reply (tracking link/number) with deterministic match + verifier approval](./W12-EP07-T073_Implement_Tier_2_verified_order_status_auto_reply_tracking_link_number_with_dete.md)
- [W12-EP07-T074 — Enforce 'auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception)' invariant across all automation paths](./W12-EP07-T074_Enforce_never_auto_close_invariant_across_all_automation_paths.md)
- [W12-EP07-T075 — Create Richpanel 'AUTO:' macros aligned to template IDs (ops task) and document governance](./W12-EP07-T075_Create_Richpanel_AUTO_macros_aligned_to_template_IDs_ops_task_and_document_gover.md)

## EP08 — Security + observability hardening

- [W12-EP08-T080 — Implement webhook authentication in ingress (header token preferred) + request schema validation](./W12-EP08-T080_Implement_webhook_authentication_in_ingress_header_token_preferred_request_schem.md)
- [W12-EP08-T081 — Implement PII redaction enforcement + tests (logs, traces, eval artifacts)](./W12-EP08-T081_Implement_PII_redaction_enforcement_tests_logs_traces_eval_artifacts.md)
- [W12-EP08-T082 — Deploy dashboards + alarms (Wave 06/07/08 alignment) and validate alert runbooks](./W12-EP08-T082_Deploy_dashboards_alarms_Wave_06_07_08_alignment_and_validate_alert_runbooks.md)
- [W12-EP08-T083 — Harden public endpoint (API Gateway throttling, optional WAF, SSRF/egress controls)](./W12-EP08-T083_Harden_public_endpoint_API_Gateway_throttling_optional_WAF_SSRF_egress_controls.md)
- [W12-EP08-T084 — Implement secret rotation support (multi-token validation) + document operational steps](./W12-EP08-T084_Implement_secret_rotation_support_multi_token_validation_document_operational_st.md)
- [W12-EP08-T085 — Operationalize IAM access reviews and break-glass workflow (alerts + cadence)](./W12-EP08-T085_Operationalize_IAM_access_reviews_and_break_glass_workflow_alerts_cadence.md)

## EP09 — Testing + staged rollout

- [W12-EP09-T090 — Implement and run smoke test pack in staging (routing + Tier1 + Tier2 + Tier0 + kill switch)](./W12-EP09-T090_Implement_and_run_smoke_test_pack_in_staging_routing_Tier1_Tier2_Tier0_kill_swit.md)
- [W12-EP09-T091 — Run load/soak tests and validate backlog catch-up behavior without vendor storms](./W12-EP09-T091_Run_load_soak_tests_and_validate_backlog_catch_up_behavior_without_vendor_storms.md)
- [W12-EP09-T092 — Execute first production deploy runbook (routing-only) and verify observability + rollback](./W12-EP09-T092_Execute_first_production_deploy_runbook_routing_only_and_verify_observability_ro.md)
- [W12-EP09-T093 — Progressive enablement: enable Tier 1 templates first, then Tier 2 order status after verification](./W12-EP09-T093_Progressive_enablement_enable_Tier_1_templates_first_then_Tier_2_order_status_af.md)
- [W12-EP09-T094 — Establish post-launch governance cadence (weekly review, monthly calibration) and close the loop with agent feedback tags](./W12-EP09-T094_Establish_post_launch_governance_cadence_weekly_review_monthly_calibration_and_c.md)
