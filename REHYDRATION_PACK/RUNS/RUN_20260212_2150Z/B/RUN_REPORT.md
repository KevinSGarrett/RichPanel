...
# RUN_REPORT

## Diffstat
- Added Shopify order tag extraction to order summary.
- Added `_parse_shopify_tags` helper for trimmed, stable dedupe.
- Updated Shopify fixtures to include tags.
- Added tests for tag parsing and enrichment.

## Commands Run
- aws sts get-caller-identity (account 878145708918).
- python -m unittest scripts.test_order_lookup (PASS; warnings logged).
- python -m unittest discover -s scripts -p "test_*.py" (PASS with AWS region set).
- python -m pytest -q scripts/test_order_lookup.py (PASS; 124 tests).
- python scripts/run_ci_checks.py --ci (PASS).

## Tests / Proof
- Unit tests passed for order lookup.
- Full scripts unittest discovery passed with AWS region configured.
- CI-equivalent checks passed.

## Files Changed
- backend/src/richpanel_middleware/commerce/order_lookup.py
- scripts/fixtures/order_lookup/shopify_order.json
- scripts/fixtures/order_lookup/shopify_order_gid.json
- scripts/test_order_lookup.py
- REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/b78/agent_b.md
- REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/RUN_REPORT.md
- REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/RUN_SUMMARY.md
- REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/STRUCTURE_REPORT.md
- REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/DOCS_IMPACT_MAP.md
- REHYDRATION_PACK/RUNS/RUN_20260212_2150Z/B/TEST_MATRIX.md

## Notes
- No Shopify writes; extraction only.
- No outbound customer contact.
