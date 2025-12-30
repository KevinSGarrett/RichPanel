# EP08 — Security + observability hardening

Last updated: 2025-12-23

## Purpose

Harden security and observability so production operation is safe and diagnosable.


## Ticket list

- [W12-EP08-T080 — Implement webhook authentication in ingress (header token preferred) + request schema validation](../03_Tickets/W12-EP08-T080_Implement_webhook_authentication_in_ingress_header_token_preferred_request_schem.md)
- [W12-EP08-T081 — Implement PII redaction enforcement + tests (logs, traces, eval artifacts)](../03_Tickets/W12-EP08-T081_Implement_PII_redaction_enforcement_tests_logs_traces_eval_artifacts.md)
- [W12-EP08-T082 — Deploy dashboards + alarms (Wave 06/07/08 alignment) and validate alert runbooks](../03_Tickets/W12-EP08-T082_Deploy_dashboards_alarms_Wave_06_07_08_alignment_and_validate_alert_runbooks.md)
- [W12-EP08-T083 — Harden public endpoint (API Gateway throttling, optional WAF, SSRF/egress controls)](../03_Tickets/W12-EP08-T083_Harden_public_endpoint_API_Gateway_throttling_optional_WAF_SSRF_egress_controls.md)
- [W12-EP08-T084 — Implement secret rotation support (multi-token validation) + document operational steps](../03_Tickets/W12-EP08-T084_Implement_secret_rotation_support_multi_token_validation_document_operational_st.md)
- [W12-EP08-T085 — Operationalize IAM access reviews and break-glass workflow (alerts + cadence)](../03_Tickets/W12-EP08-T085_Operationalize_IAM_access_reviews_and_break_glass_workflow_alerts_cadence.md)


## Dependencies

- EP03/04/06/07 inputs.
- Must be in place before enabling automation.
