# Structure Report

**RUN_ID:** RUN_20260113_0433Z  
**Agent:** B  
**Date:** 2026-01-13

## Changes Overview

### New Files
- `scripts/test_e2e_smoke_encoding.py` (197 lines)
  - Unit tests for URL encoding enforcement
  - Scenario payload validation tests
  - 5 tests covering email IDs, special chars, determinism, PII-safety

- `REHYDRATION_PACK/RUNS/RUN_20260113_0433Z/B/e2e_outbound_proof.json` (196 lines)
  - PASS proof artifact for order_status scenario
  - PII-safe (fingerprints only, paths redacted)

### Modified Files

#### Backend (Middleware)
- `backend/src/richpanel_middleware/automation/pipeline.py` (+11/-28 lines)
  - Added URL encoding to `execute_routing_tags()` and `execute_order_status_reply()`
  - Import `urllib.parse` and encode conversation_id before building API paths
  - Removed stale conversation_no resolution attempts

- `backend/src/richpanel_middleware/integrations/richpanel/client.py` (+13/-3 lines)
  - Added `conversation_no: Optional[int]` field to `TicketMetadata` dataclass
  - Updated `get_ticket_metadata()` to extract and parse conversation_no from response

#### Scripts (E2E Smoke)
- `scripts/dev_e2e_smoke.py` (+341/-28 lines)
  - Added `--scenario` argument (choices: baseline, order_status)
  - Added `_order_status_scenario_payload()` builder with seeded tracking fields
  - Added `_sanitize_decimals()` for DynamoDB Decimal type handling
  - Updated `build_payload()` to flatten scenario fields to top level (not nested under "payload")
  - Added `extract_draft_replies_from_actions()` fallback for redacted storage
  - Updated `validate_idempotency_item()` to handle Decimal and add fallback fingerprinting
  - Updated `validate_routing()` to extract intent field
  - Updated `sanitize_draft_replies()` to include tracking_number and carrier
  - Added scenario-specific PASS criteria and status/tag tracking
  - Enhanced proof JSON with criteria_details, status_before/after, middleware_tags_added

- `scripts/run_ci_checks.py` (+1 line)
  - Wired `test_e2e_smoke_encoding.py` into CI checks

#### Documentation
- `docs/08_Engineering/CI_and_Actions_Runbook.md` (+26 lines)
  - Added order-status scenario command example (PowerShell-safe)
  - Documented PASS criteria and proof expectations
  - Included PII-safe requirements

- `docs/00_Project_Admin/Progress_Log.md` (+8/-1 lines)
  - Added RUN_20260113_0433Z entry with URL encoding fix summary

- `docs/_generated/doc_registry.json` (+3/-3 lines)
  - Auto-regenerated after runbook updates

- `docs/_generated/doc_registry.compact.json` (+3/-3 lines)
  - Auto-regenerated after runbook updates

## Structural Impact
- No breaking changes
- Backward compatible (scenario defaults to "baseline")
- New scenario mode is opt-in via `--scenario order_status`

## Test Coverage Impact
- Added 5 new unit tests (URL encoding + scenario payload)
- All existing tests pass (108 total)
- CI checks pass with new tests wired in

## Deployment Notes
- Deployed to dev via CDK (`npx cdk deploy RichpanelMiddleware-dev`)
- Manual Lambda code update required due to CDK asset caching
- Lambda env vars confirmed: outbound enabled for proof window
