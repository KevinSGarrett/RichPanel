# Agent C Run Report

Run ID: `RUN_20260120_1414Z`

## Objective
Build a PII-safe intent evaluation harness for order-status routing, add read-only scaffolding for live shadow evals, and capture run artifacts.

## Commands executed
```powershell
python scripts/eval_order_status_intent.py --dataset scripts/fixtures/intent_eval/order_status_golden.jsonl --output REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/intent_eval_golden_results.json
python scripts/test_eval_order_status_intent.py
python scripts/test_richpanel_client.py
python scripts/run_ci_checks.py --ci
```

## Eval summary (golden set)
- Deterministic precision: 1.00
- Deterministic recall: 1.00
- LLM calls: 0 (OPENAI_ALLOW_NETWORK not enabled)

## CI snippet
```text
[FAIL] Generated files changed after regen. Commit the regenerated outputs.
Uncommitted changes:
M docs/_generated/doc_outline.json
M docs/_generated/doc_registry.compact.json
M docs/_generated/doc_registry.json
M docs/_generated/heading_index.json
?? REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/
```

## Notes
- Live shadow eval (`--from-richpanel`) was not executed in this run.
- CI failure is due to the repo needing a clean git status in `--ci` mode after regen.

## Artifacts
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/EVAL_REPORT.md`
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/TEST_MATRIX.md`
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/intent_eval_golden_results.json`
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/order_status_golden.jsonl`
