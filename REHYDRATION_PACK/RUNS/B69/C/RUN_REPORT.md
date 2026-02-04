## B69 Agent C Diagnosis

### Why deterministic order-status rate was 0.0 in B68
- `scripts/prod_shadow_order_status_report.py` uses the **OpenAI order-status intent** result to set `classified_order_status`. When OpenAI is gated (deterministic runs), the intent result is `None`, so all tickets are marked `classified_order_status=False`.
- The deterministic router output (`routing.intent`) is computed but **never used** to classify order-status in the report when the LLM is gated.
- The deterministic router also only inspects a limited set of top-level message fields, while many prod payloads store customer text under nested `ticket`, `comments`, or `messages`, which further reduces deterministic signal.

### Fix direction
- Use deterministic routing intent as the fallback classifier when LLM intent is not called.
- Expand deterministic message extraction and keyword rules to recognize order-status language and order numbers from real payload shapes.

### B69 evidence (local)
- Labeled dataset + eval summary stored in `REHYDRATION_PACK/RUNS/B69/C/PROOF/intent_eval_*`.
- Deterministic baseline hits 10/10 order-status and 10/10 non-order-status on the synthetic set.

### B69 prod shadow status
- Prod shadow runs completed in 25-ticket batches (deterministic + OpenAI).
- Summary: `REHYDRATION_PACK/RUNS/B69/C/PROOF/prod_shadow_report_200_summary.md`.
  - Deterministic order_status_rate: 0.34
  - OpenAI order_status_rate: 0.45 (ticket bucket verified >40% order-status rate)