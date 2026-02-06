# DEV E2E smoke proof (order_status)

- timestamp_utc: 2026-02-06T21:59:50.358843+00:00
- env: dev
- region: us-east-2
- ticket_number: 1260 (dev sandbox email)
- scenario: order_status (variant: order_status_tracking)
- result: PASS (PASS_STRONG)

## Operator reply evidence (/send-message)
- ticket_channel: email
- outbound_endpoint_used: /send-message
- send_message_path_confirmed: true
- send_message_used: true (status_code=200)
- latest_comment_is_operator: true
- last_message_source_after: operator
- operator_reply_confirmed: true
- tags_added: mw-auto-replied, mw-order-status-answered, mw-outbound-path-send-message, mw-reply-sent
