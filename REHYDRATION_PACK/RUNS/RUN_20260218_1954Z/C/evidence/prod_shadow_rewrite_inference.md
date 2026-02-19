Read-only shadow eval proof (prod)
- Run report: prod_shadow_report.json
- HTTP trace: prod_shadow_http_trace.json
- Ticket fetch via /v1/tickets (no /conversations calls).
- Order_status_candidate=true with draft_reply_present=true in report.
- HTTP trace shows 2 OpenAI POST /v1/chat/completions calls in same run.
- OPENAI_REPLY_REWRITE_MODEL=gpt-5.2 set in Lambda env proof.
Inference: OpenAI calls during order-status flow are attributable to rewrite, using gpt-5.2.
