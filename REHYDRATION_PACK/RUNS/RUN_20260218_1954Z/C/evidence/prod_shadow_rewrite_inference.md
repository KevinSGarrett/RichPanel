Read-only shadow eval proof (prod)
- Run report: prod_shadow_report.json
- HTTP trace: prod_shadow_http_trace.json
- Evidence in report: order_status_candidate=true, draft_reply_present=true, routing primary_source=deterministic.
- HTTP trace shows 2 OpenAI POST /v1/chat/completions calls in the same run.
- Rewrite model env set to OPENAI_REPLY_REWRITE_MODEL=gpt-5.2 (see Lambda env proof).
Inference: OpenAI calls during deterministic routing are attributable to rewrite, using gpt-5.2.
