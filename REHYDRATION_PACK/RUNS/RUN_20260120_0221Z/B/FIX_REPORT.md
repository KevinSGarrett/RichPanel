# Fix Report — RUN_20260120_0221Z (Agent B)

## Summary
Adjusted order_status automation to enforce real closure + follow-up routing, updated dev E2E harness to validate those behaviors with sandbox proofs, and aligned tests/runbook.

## Code Changes
- `backend/src/richpanel_middleware/automation/pipeline.py`
  - Reordered close payloads; removed tag injection in close payloads.
  - Verified closure post-update; log each candidate attempt.
  - Avoid duplicate customer comments by stripping comment on retry after first 2xx.
  - Apply reply tags only after a successful close update to prevent false loop tags.
  - Follow-up routes to support even when order_status action missing.
  - Removed follow-up escalation for loop-prevention case.
- `scripts/dev_e2e_smoke.py`
  - Enforced closure requirement in PASS_STRONG criteria.
  - Added `--send-followup`/`--json-out` aliases.
  - Seeded valid order_id for sandbox tickets.
  - Added follow-up wait for loop-prevention + closed status.
  - Tracked follow-up routing requirements in criteria.
- `scripts/test_pipeline_handlers.py`
  - Updated expectations for follow-up routing tags; improved executor simulation.
  - Added coverage for comment de-duplication and tag ordering.
- `scripts/test_e2e_smoke_encoding.py`
  - Updated classification test coverage for debug fallback paths.
  - Added coverage for `_wait_for_ticket_ready`.
- `docs/08_Engineering/CI_and_Actions_Runbook.md`
  - Documented PASS_STRONG closure requirement and follow-up routing evidence.

## Proof Artifacts
- `REHYDRATION_PACK/RUNS/RUN_20260120_0221Z/B/order_status_no_tracking_short_window.json`
- `REHYDRATION_PACK/RUNS/RUN_20260120_0221Z/B/order_status_tracking.json`

## Notes
- Outbound writes were enabled in **dev** (`RICHPANEL_OUTBOUND_ENABLED=true`). No prod keys used.
