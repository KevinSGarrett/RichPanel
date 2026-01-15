# Test Matrix — RUN_20260115_1200Z (C)

- `python scripts/run_ci_checks.py --ci` (PASS locally; includes all validation scripts plus unit/integration suites across backend and scripts).
- No additional manual tests were required; rerun will be triggered after run artifacts are completed if needed.
- Coverage exercised:
  - OpenAI client/unit tests (flag on/off excerpt behavior).
  - Pipeline/worker/routing/reply rewrite suites.
  - Shopify/ShipStation/Richpanel client retries/redaction.
  - Order lookup enrichment scenarios.
  - Doc/registry and prompt freshness checks.
- GitHub Actions `validate` failed due to missing RUN artifacts (now addressed); rerun expected to pass once checks restart.
