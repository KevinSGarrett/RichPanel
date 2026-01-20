# Order-Status Intent Eval Report

Run ID: `RUN_20260120_1414Z`

## Command lines
- `python scripts/eval_order_status_intent.py --dataset scripts/fixtures/intent_eval/order_status_golden.jsonl --output REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/intent_eval_golden_results.json`

## Golden set results (deterministic baseline)
Confusion matrix (order_status positive):
- TP: 10
- FP: 0
- FN: 0
- TN: 10

Precision: 1.00  
Recall: 1.00

## OpenAI routing path
- LLM calls: 0 (OPENAI_ALLOW_NETWORK not enabled in this run)
- Metrics: not available

## Artifacts
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/intent_eval_golden_results.json`
- `REHYDRATION_PACK/RUNS/RUN_20260120_1414Z/C/order_status_golden.jsonl`
