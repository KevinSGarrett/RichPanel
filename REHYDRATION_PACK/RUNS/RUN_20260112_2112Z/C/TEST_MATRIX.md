# Test Matrix

**Run ID:** `RUN_20260112_2112Z`  
**Agent:** C  
**Date:** 2026-01-12

List the tests you ran (or explicitly note none).

| Test name | Command / method | Pass/Fail | Evidence path/link |
|---|---|---|---|
| CI-equivalent suite | `AWS_REGION=us-east-2 AWS_DEFAULT_REGION=us-east-2 python scripts/run_ci_checks.py --ci` | pass | snippet in `RUN_REPORT.md` |

## Notes
- New tests added: tracking dict number/id, orders list candidate, shipment dict, fulfillment list coverage (in `scripts/test_order_lookup.py`).
