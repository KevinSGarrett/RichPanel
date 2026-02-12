# TEST_MATRIX

- python -m unittest scripts.test_order_lookup (PASS)
- python -m unittest discover -s scripts -p "test_*.py" (PASS with AWS region set)
- python -m pytest -q scripts/test_order_lookup.py (PASS)
- python scripts/run_ci_checks.py --ci (FAIL: generated files changed after regen)
- Warnings observed: shopify.match_diagnostics, shipstation.missing_credentials
- No customer contact executed.
- No Shopify writes executed.
- Tests are deterministic for tag parsing.
- Fixtures updated with tags.
- Follow-up CI pass required after docs completion.
