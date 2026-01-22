Run Summary - B51 Agent B

Changes:
- Removed conversation_id fallback for Shopify order_id extraction and added missing-order_id skip log.
- Ensured shadow-order-status lookup marks missing order_id as SKIPPED without Shopify calls.
- Added unit tests for unknown order_id handling and Shopify call suppression.

Checks:
- python -m compileall backend/src scripts (pass)
- python -m pytest -q (pass)
- python scripts/run_ci_checks.py --ci (fail: dirty worktree detected)
