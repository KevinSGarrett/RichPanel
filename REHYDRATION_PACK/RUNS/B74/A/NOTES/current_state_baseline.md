## Baseline (pre-B74 changes)

- Outbound reply path lives in `backend/src/richpanel_middleware/automation/pipeline.py` in
  `execute_order_status_reply()`.
- Reply body is generated from the order-status draft reply action and optionally
  rewritten before outbound is attempted.
- Email-channel tickets attempt `PUT /v1/tickets/{id}/send-message` and then verify the
  latest comment `is_operator=true` before closing and tagging.
- Non-email channels fall back to a middleware comment via `PUT /v1/tickets/{id}`.
- Bot author id resolution relied on env vars and a `/v1/users` lookup in dev (cached);
  prod required an env-provided author id.
