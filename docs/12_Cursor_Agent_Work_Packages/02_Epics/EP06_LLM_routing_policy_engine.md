# EP06 — LLM routing + policy engine

Last updated: 2025-12-23

## Purpose

Implement LLM routing as advisory with strict schemas and authoritative policy gates.


## Ticket list

- [W12-EP06-T060 — Implement classifier model call with strict schema validation (mw_decision_v1) and fail-closed fallback](../03_Tickets/W12-EP06-T060_Implement_classifier_model_call_with_strict_schema_validation_mw_decision_v1_and.md)
- [W12-EP06-T061 — Implement policy engine (Tier 0 overrides, Tier 2 eligibility, Tier 3 disabled) as authoritative layer](../03_Tickets/W12-EP06-T061_Implement_policy_engine_Tier_0_overrides_Tier_2_eligibility_Tier_3_disabled_as_a.md)
- [W12-EP06-T062 — Implement Tier 2 verifier call (mw_tier2_verifier_v1) and integrate into policy gating](../03_Tickets/W12-EP06-T062_Implement_Tier_2_verifier_call_mw_tier2_verifier_v1_and_integrate_into_policy_ga.md)
- [W12-EP06-T063 — Implement confidence threshold configuration + calibration workflow hooks](../03_Tickets/W12-EP06-T063_Implement_confidence_threshold_configuration_calibration_workflow_hooks.md)
- [W12-EP06-T064 — Integrate offline eval harness into CI (golden set run + regression gates)](../03_Tickets/W12-EP06-T064_Integrate_offline_eval_harness_into_CI_golden_set_run_regression_gates.md)


## Dependencies

- EP03 worker required.
- EP05 for Tier2 eligibility.
- EP07 uses outputs.
