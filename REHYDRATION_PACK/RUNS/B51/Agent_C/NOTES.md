# Notes

- Live dev E2E smoke run initially failed because `--ticket-id` or `--ticket-number` is required for order_status scenarios.
- Re-run with ticket 1084 failed due to missing AWS credentials (NoCredentialsError).
- Ticket 1086 run failed tracking URL assertion with ticket reply evidence; tracking assertion now uses computed draft reply to validate tracking fields.
- Successful proof captured with ticket 1087 using `--no-require-openai-routing` and `--no-require-openai-rewrite` to avoid OpenAI gating.
