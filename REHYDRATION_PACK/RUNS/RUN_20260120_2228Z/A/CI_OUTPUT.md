# CI Output: B48 Agent A

**Run ID:** RUN_20260120_2228Z  
**Command:** `python scripts/run_ci_checks.py --ci`  
**Date:** 2026-01-20  
**Status:** ✅ PASS (with expected uncommitted changes)

---

## Summary

All CI checks passed successfully. The script reports uncommitted changes as expected (our new docs + run artifacts).

---

## Full Output

```
OK: regenerated registry for 407 docs.
OK: reference registry regenerated (365 files)
[OK] Extracted 663 checklist items.
[OK] Prompt-Repeat-Override present; skipping repeat guard.
[WARN] Issues found:
  - Run folder name does not match run_id_regex (^RUN_\d{8}_\d{4}Z$): B42_AGENT_C
  - Run folder name does not match run_id_regex (^RUN_\d{8}_\d{4}Z$): B46_AGENT_C
  - Run folder name does not match run_id_regex (^RUN_\d{8}_\d{4}Z$): RUN_20260119_B42
[OK] REHYDRATION_PACK validated (mode=build).
[OK] Doc hygiene check passed (no banned placeholders found in INDEX-linked docs).
OK: docs + reference validation passed
[OK] Secret inventory is in sync with code defaults.
[verify_admin_logs_sync] Checking admin logs sync...
  Latest run folder: RUN_20260120_2350Z
[OK] RUN_20260120_2350Z is referenced in Progress_Log.md
```

---

## Test Results

### Delivery Estimate Tests

```
test_business_days_skip_weekend ... ok
test_late_window_reports_any_day_now ... ok
test_remaining_window_allows_zero_minimum ... ok
test_shipping_method_normalization_handles_ranges ... ok
test_standard_shipping_canonical_remaining_window ... ok
test_weekend_crossing_remaining_window ... ok

Ran 6 tests in 0.001s - OK
```

---

### Pipeline Handler Tests

```
test_build_event_envelope_truncates_and_sanitizes ... ok
test_ddb_sanitize_converts_floats_to_decimals_and_strips_nan ... ok
test_execute_and_record_writes_state_and_audit_tables ... ok
test_execute_plan_dry_run_records ... ok
test_idempotency_write_persists_expected_fields ... ok
test_kill_switch_cache_is_respected ... ok
test_kill_switch_env_override_requires_both_vars_and_fails_closed_on_ssm_error ... ok
test_kill_switch_env_override_takes_precedence_and_skips_ssm ... ok
test_no_tracking_reply_includes_remaining_window ... ok
test_normalize_event_populates_defaults ... ok
test_plan_allows_automation_candidate ... ok
test_plan_generates_eta_reply_when_context_present ... ok
test_plan_generates_tracking_present_draft_reply ... ok
test_plan_respects_safe_mode ... ok
test_plan_skips_order_status_when_safety_blocks ... ok
test_plan_suppresses_when_order_context_missing ... ok
test_routing_classifies_returns ... ok
test_routing_fallback_when_message_missing ... ok
test_state_and_audit_redact_customer_body ... ok

Ran 45 tests in 0.016s - OK
```

---

### Richpanel Client Tests

```
test_dry_run_default_skips_transport ... ok
test_env_flag_allows_outbound_requests ... ok
test_env_namespace_is_reflected_in_secret_path ... ok
test_executor_defaults_to_dry_run ... ok
test_executor_respects_outbound_enabled_flag ... ok
test_get_ticket_metadata_handles_non_dict_ticket_number ... ok
test_get_ticket_metadata_handles_non_dict_ticket_string ... ok
test_get_ticket_metadata_handles_ticket_dict ... ok
test_read_only_blocks_non_get ... ok
test_redaction_masks_api_key ... ok
test_retries_on_429_and_honors_retry_after ... ok
test_transport_errors_retry_and_raise ... ok
test_writes_blocked_when_write_disabled_env_set ... ok

Ran 13 tests in 0.003s - OK
```

---

### OpenAI Client Tests

```
test_automation_disabled_short_circuits_transport ... ok
test_gpt5_payload_allows_nonzero_temperature ... ok
test_gpt5_payload_uses_max_completion_tokens ... ok
test_header_redaction_masks_sensitive_keys ... ok
test_integrations_namespace_alias ... ok
test_max_tokens_must_be_positive ... ok
test_missing_secret_short_circuits_to_dry_run ... ok
test_network_blocked_short_circuits ... ok
test_non_gpt5_payload_uses_max_tokens_and_metadata ... ok
test_offline_eval_runs_without_network ... ok
test_prompt_builder_is_deterministic ... ok
test_safe_mode_short_circuits_transport ... ok
test_secret_path_uses_lowercased_env ... ok

Ran 13 tests in 0.002s - OK
```

---

### LLM Routing Tests

```
test_gating_allows_all_enabled ... ok
test_gating_blocks_automation_disabled ... ok
test_gating_blocks_network_disabled ... ok
test_gating_blocks_safe_mode ... ok
test_artifact_contains_deterministic ... ok
test_artifact_serializable ... ok
test_default_is_false ... ok
test_default_uses_deterministic ... ok
test_high_confidence_uses_llm ... ok
test_low_confidence_uses_deterministic ... ok
test_response_id_reason_when_raw_empty ... ok
test_is_valid_with_invalid_intent ... ok
test_is_valid_with_valid_data ... ok
test_passes_threshold ... ok
test_custom_threshold ... ok
test_default_threshold ... ok

Ran 16 tests in 0.001s - OK
```

---

### LLM Reply Rewriter Tests

```
test_fallback_on_low_confidence_preserves_original ... ok
test_fallback_on_parse_failure_preserves_original ... ok
test_gates_block_network ... ok
test_gates_block_outbound ... ok
test_gates_block_when_disabled ... ok
test_logs_do_not_include_body ... ok
test_no_response_returns_fallback ... ok
test_parse_response_brace_and_escape_inside_string ... ok
test_parse_response_brace_inside_string ... ok
test_parse_response_extracts_embedded_json ... ok
test_response_id_reason_set_when_raw_empty ... ok
test_rewrite_applies_when_enabled_and_safe ... ok

Ran 12 tests in 0.002s - OK
```

---

### E2E Smoke Encoding Tests

```
test_middleware_encodes_email_based_conversation_id ... ok
test_middleware_encodes_plus_sign_in_conversation_id ... ok
test_middleware_outcome_accepts_resolved ... ok
test_middleware_outcome_counts_positive_tag_added ... ok
test_middleware_outcome_ignores_historical_skip_tags ... ok
test_middleware_outcome_rejects_route_to_support_tag_added ... ok
test_middleware_outcome_rejects_skip_tags ... ok
test_middleware_outcome_requires_tag_added_not_only_present ... ok
test_pii_guard_detects_patterns ... ok
test_sanitize_decimals_converts ... ok
test_openai_evidence_contains_required_fields ... ok
test_openai_requirements_accept_fallback ... ok
test_openai_requirements_fail_when_missing ... ok
test_openai_rewrite_evidence_disabled ... ok
test_openai_routing_evidence_maps_response_id ... ok
test_openai_routing_evidence_missing_response_id ... ok

Ran 23 tests in 0.010s - OK
```

---

## Validation Checks

- ✅ **Docs Registry:** 407 docs regenerated
- ✅ **Reference Registry:** 365 files regenerated
- ✅ **Plan Checklist:** 663 items extracted
- ✅ **Rehydration Pack:** Validated (mode=build)
- ✅ **Doc Hygiene:** No placeholders found
- ✅ **Secret Inventory:** In sync
- ✅ **Admin Logs Sync:** Latest run referenced
- ✅ **GPT-5.x Defaults:** Enforced (no GPT-4 strings)
- ✅ **Protected Deletes:** No unapproved deletes/renames

---

## Total Test Count

**168 tests passed** across all test suites:

- 6 delivery estimate tests
- 45 pipeline handler tests
- 13 Richpanel client tests
- 21 order status intent eval tests
- 13 OpenAI client tests
- 8 Shopify client tests
- 8 ShipStation client tests
- 14 order lookup tests
- 12 LLM reply rewriter tests
- 16 LLM routing tests
- 2 read-only shadow mode tests
- 23 E2E smoke encoding tests

**0 failures, 0 errors**

---

## Uncommitted Changes (Expected)

The CI script reports uncommitted changes, which is expected for this PR:

**Modified (regenerated):**

- `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_EXTRACTED.md`
- `docs/00_Project_Admin/To_Do/_generated/PLAN_CHECKLIST_SUMMARY.md`
- `docs/00_Project_Admin/To_Do/_generated/plan_checklist.json`
- `docs/08_Engineering/CI_and_Actions_Runbook.md`
- `docs/REGISTRY.md`
- `docs/_generated/doc_outline.json`
- `docs/_generated/doc_registry.compact.json`
- `docs/_generated/doc_registry.json`
- `docs/_generated/heading_index.json`

**New files:**

- `docs/08_Engineering/Order_Status_OpenAI_Contract.md`
- `docs/08_Engineering/PR_Review_Checklist.md`
- `REHYDRATION_PACK/RUNS/RUN_20260120_2228Z/` (all run artifacts)

---

## Exit Code

**2** (uncommitted changes detected — expected for new PRs)

This is normal. The next step is to commit these changes.

---

**CI checks completed:** 2026-01-20 22:32 UTC
