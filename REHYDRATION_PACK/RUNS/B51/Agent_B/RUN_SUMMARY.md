Run Summary - B51 Agent B

Changes:
- Removed conversation_id fallback for Shopify order_id extraction and added missing-order_id skip log.
- Removed unused conversation_id parameter from order_id extraction and baseline usage.
- Ensured shadow-order-status lookup marks missing order_id as SKIPPED without Shopify calls.
- Added unit tests for unknown order_id handling, nested order fields, and Shopify call suppression.
- Executed backend order-id tests under scripts coverage to satisfy Codecov.
- Simplified test sys.path setup to keep coverage deterministic.
- Ensured scripts test runner main executes the coverage test class.

Checks:
- python -m compileall backend/src scripts (pass)
- python -m pytest -q (pass)
- python scripts/run_ci_checks.py --ci (pass)
