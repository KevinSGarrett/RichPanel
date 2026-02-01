## Router precedence tests (B65/B)

### Added unit case (expected outcome)
- `I want a return — but also where is my order #1180306?` -> `order_status_tracking`
- `I want a return for order #1180306.` -> `return_request` (no shipping/tracking language)

### Redacted B64/C sample checks (order-status precedence)
Source: `REHYDRATION_PACK/RUNS/B64/C/PROOF/prod_shadow_manual_review.json`
- Excerpt: `Van you please provide information on order <redacted> placed Jan 11. There's no information except that its unfulfilled?`  
  Evidence run (synthetic order number inserted):  
  `Can you please provide information on order #1180306 placed Jan 11. There is no information except that its unfulfilled?`

Evidence output:
```text
{'name': 'b64c_unfulfilled_order', 'source': 'B64/C manual review redacted unfulfilled excerpt', 'message': 'Can you please provide information on order #1180306 placed Jan 11. There is no information except that its unfulfilled?', 'extracted_order_number': '1180306', 'routing_intent': 'order_status_tracking', 'routing_reason': 'order number present with shipping or tracking language'}
```
