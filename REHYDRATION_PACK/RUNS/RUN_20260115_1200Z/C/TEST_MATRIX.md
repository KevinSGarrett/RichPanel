# Test Matrix — RUN_20260115_1200Z (C)

- `python scripts/run_ci_checks.py --ci` (PASS; includes all validation scripts plus unit/integration suites across backend and scripts).
- No additional manual tests were required.
- Coverage exercised:
  - OpenAI client/unit tests (flag off/on, raw excerpt path, retry warning path).
  - Pipeline/worker/routing/reply rewrite suites.
  - Shopify/ShipStation/Richpanel client retries/redaction.
  - Order lookup enrichment scenarios.
  - Doc/registry and prompt freshness checks.
- GitHub Actions `validate` passed; Codecov/patch passed; Bugbot passed for PR #111.
