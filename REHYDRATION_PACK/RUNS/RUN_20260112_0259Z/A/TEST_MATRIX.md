# Test Matrix

**Run ID:** `RUN_20260112_0259Z`  
**Agent:** A  
**Date:** 2026-01-12

## Tests run

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent checks (first pass) | `python scripts/run_ci_checks.py --ci` | fail | Admin logs sync failed (expected; Progress_Log not yet updated) |
| CI-equivalent checks (second pass) | `python scripts/run_ci_checks.py --ci` | pass | All validation passed; uncommitted changes detected (expected) |
| Doc registry regeneration | `python scripts/regen_doc_registry.py` (via CI script) | pass | 401 docs indexed |
| Reference registry regeneration | `python scripts/regen_reference_registry.py` (via CI script) | pass | 365 reference files indexed |
| Plan checklist extraction | `python scripts/regen_plan_checklist.py` (via CI script) | pass | 601 checklist items extracted |
| Rehydration pack validation | `python scripts/verify_rehydration_pack.py` (via CI script) | pass | mode=build, all required files present |
| Doc hygiene check | `python scripts/verify_doc_hygiene.py` (via CI script) | pass | No banned placeholders in INDEX-linked docs |
| Secret inventory sync | `python scripts/verify_secret_inventory_sync.py` (via CI script) | pass | Secret inventory in sync with code defaults |
| Admin logs sync | `python scripts/verify_admin_logs_sync.py` (via CI script) | pass | RUN_20260112_0259Z referenced in Progress_Log.md |
| Pipeline handler tests | `python scripts/test_pipeline_handlers.py` (via CI script) | pass | 25 tests passed |
| Richpanel client tests | `python scripts/test_richpanel_client.py` (via CI script) | pass | 8 tests passed |
| OpenAI client tests | `python scripts/test_openai_client.py` (via CI script) | pass | 9 tests passed |
| Shopify client tests | `python scripts/test_shopify_client.py` (via CI script) | pass | 8 tests passed |
| ShipStation client tests | `python scripts/test_shipstation_client.py` (via CI script) | pass | 8 tests passed |
| Order lookup tests | `python scripts/test_order_lookup.py` (via CI script) | pass | 3 tests passed |
| LLM reply rewriter tests | `python scripts/test_llm_reply_rewriter.py` (via CI script) | pass | 7 tests passed (run twice in CI) |
| LLM routing tests | `python scripts/test_llm_routing.py` (via CI script) | pass | 15 tests passed |
| Worker flag wiring tests | `python scripts/test_worker_handler_flag_wiring.py` (via CI script) | pass | 2 tests passed |
| Protected delete check | `python scripts/check_protected_deletes.py --ci` (via CI script) | pass | No unapproved protected deletes/renames |

## Notes
- **First CI pass failed** because `Progress_Log.md` did not yet reference RUN_20260112_0259Z (expected; updated Progress_Log and reran)
- **Second CI pass succeeded** with all validation + unit tests passing
- **Uncommitted changes detected** in second pass (expected; need to commit regenerated files + new template + updated docs)
- **Total unit tests:** 83 tests across 9 test suites, all passed
- **No E2E smoke test required:** Documentation-only changes do not touch outbound/automation logic
