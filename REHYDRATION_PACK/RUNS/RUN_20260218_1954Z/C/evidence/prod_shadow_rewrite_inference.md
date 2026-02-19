Read-only shadow eval proof (prod)
- Run report: prod_shadow_report.json
- HTTP trace: prod_shadow_http_trace.json
- Ticket fetch via /v1/tickets (no /conversations calls).
- Report includes explicit fields:
  - rewrite_model_used=gpt-5.2-2025-12-11
  - reply_proof.greeting_present=true
  - reply_proof.key_details_present=true
  - reply_proof.holly_signature_present=true
