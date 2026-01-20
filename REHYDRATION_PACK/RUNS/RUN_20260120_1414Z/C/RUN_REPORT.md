# Agent C Run Report

Run ID: `RUN_20260120_1414Z`

## Objective
Build a PII-safe intent evaluation harness for order-status routing, add read-only scaffolding for live shadow evals, and capture run artifacts.

## Commands executed
```powershell
python scripts/eval_order_status_intent.py --dataset scripts/fixtures/intent_eval/order_status_golden.jsonl --output REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/intent_eval_golden_results.json
python scripts/test_eval_order_status_intent.py
python scripts/test_richpanel_client.py
python scripts/test_live_readonly_shadow_eval.py
python scripts/run_ci_checks.py --ci
```

## Eval summary (golden set)
- Deterministic precision: 1.00
- Deterministic recall: 1.00
- LLM calls: 0 (OPENAI_ALLOW_NETWORK not enabled)

## CI snippet
```text
$ python scripts/run_ci_checks.py --ci
[OK] CI-equivalent checks passed.
```

## Notes
- Live shadow eval (`--from-richpanel`) was not executed in this run.
- Trace validation now permits GET/HEAD to match read-only behavior.

## Artifacts
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/EVAL_REPORT.md`
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/TEST_MATRIX.md`
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/intent_eval_golden_results.json`
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/order_status_golden.jsonl`
