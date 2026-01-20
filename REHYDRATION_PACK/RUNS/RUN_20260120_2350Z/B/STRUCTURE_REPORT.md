# Structure Report — RUN_20260120_2350Z (Agent B)
1) backend/src/richpanel_middleware/automation/llm_routing.py — capture response_id + llm_called metadata.
2) backend/src/richpanel_middleware/automation/llm_reply_rewriter.py — record response_id + call metadata for rewrites.
3) backend/src/richpanel_middleware/automation/pipeline.py — persist rewrite evidence in outbound replies.
4) backend/src/lambda_handlers/worker/handler.py — store openai_rewrite evidence in state/audit tables.
5) scripts/dev_e2e_smoke.py — add openai proof block + require-openai flags.
6) scripts/test_e2e_smoke_encoding.py — new OpenAI evidence + PII guard tests.
7) docs/08_Engineering/CI_and_Actions_Runbook.md — OpenAI evidence requirements documented.
8) REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/ — run artifacts and proof JSONs.
9) REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_tracking_proof.json — OpenAI evidence sample.
10) REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_no_tracking_proof.json — OpenAI evidence sample.
