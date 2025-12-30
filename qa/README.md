# QA (Tests + Evaluations) — Phase 0 Scaffold

This folder will contain:
- unit + integration tests
- contract tests (webhook schema, API contract)
- offline evaluation harness for routing + automation decisions

## Suggested layout
- `tests_unit/` — fast unit tests
- `tests_integration/` — integration tests (with stubs/mocks where needed)
- `tests_contract/` — schema/contract tests for Richpanel payloads
- `tests_e2e/` — end-to-end tests (may require staging env)
- `evals/` — offline eval harness + datasets + metrics
- `fixtures/` — sanitized sample payloads
- `reports/` — lightweight summaries (store heavy reports in `/artifacts/`)

## Key docs
- Testing strategy: `docs/08_Testing_Quality/`
- Eval plan: `docs/04_LLM_Design_Evaluation/`

