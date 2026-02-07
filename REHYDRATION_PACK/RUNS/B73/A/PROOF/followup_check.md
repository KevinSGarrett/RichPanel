# Follow-up routing safety check (DEV)

- ticket_number: 1260 (dev sandbox email)
- scenario: order_status with follow-up simulation
- run_id: 20260206155921
- result: PASS (PASS_STRONG)

## First customer email (automation + operator reply)
- operator reply confirmed: true
- last_message_source_after: operator
- outbound_endpoint_used: /send-message
- send_message_status_code: 200
- tags_added: mw-auto-replied, mw-order-status-answered, mw-outbound-path-send-message, mw-reply-sent

## Second customer reply (follow-up)
- followup_performed: true
- followup_reply_sent: false (message_count_delta=0)
- followup_routed_support: true
- followup_skip_tags_added: mw-skip-followup-after-auto-reply
