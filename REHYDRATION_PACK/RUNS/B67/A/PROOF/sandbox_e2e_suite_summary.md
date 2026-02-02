# Sandbox E2E Suite Summary — B67/A

- Timestamp: `2026-02-02T16:23:13Z`
- Sandbox run ID: `20260202154200`
- Prod read-only run ID: `RUN_20260202_1611Z`

## Scenario results (split evidence)
- `order_status_golden`: `PASS` (sandbox proof: `sandbox_order_status_golden_proof.json`)
- `not_order_status_negative_case`: `PASS` (sandbox proof: `sandbox_negative_case_proof.json`)
- `followup_after_autoclose`: `PASS` (sandbox proof: `sandbox_followup_suppression_proof.json`)
- `order_status_fallback_email_match`: `PASS_SPLIT_EVIDENCE`
  - Match evidence (prod read-only): `prod_readonly_fallback_match_report.json`
  - Outbound send/close evidence (sandbox): `sandbox_order_status_golden_proof.json`

## Notes
- Prod report is read-only (no outbound, no writes).
- Sandbox reports validate `/send-message` operator reply + close.
