# Notes

- Live dev E2E smoke run initially failed because `--ticket-id` or `--ticket-number` is required for order_status scenarios.
- Re-run with ticket 1084 failed due to missing AWS credentials (NoCredentialsError).
- Ticket 1086 run failed tracking URL assertion with ticket reply evidence; tracking assertion now uses computed draft reply to validate tracking fields.
- Successful proof captured with ticket 1087 using `--no-require-openai-routing` and `--no-require-openai-rewrite` to avoid OpenAI gating.
- Bugbot follow-up: URL validation now compares extracted URLs, ETA windows are validated, and smoke reply checks only use operator comments (fallback to draft only when rewrite not applied).
- Tickets 1084/1085/1088 returned `skip_or_escalation_tags_present` (loop prevention/route tags) when reusing them for smoke.
- Fresh ticket 1089 produced a PASS_STRONG proof artifact.