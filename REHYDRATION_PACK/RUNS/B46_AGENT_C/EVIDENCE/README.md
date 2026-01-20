# Evidence Staging

Place production run artifacts here after executing the live read-only shadow eval:

- `prod_readonly_shadow_eval_http_trace.json` (GET-only trace)
- `readonly_shadow/<timestamp>_<ticket_hash>.json` (PII-safe eval output)
