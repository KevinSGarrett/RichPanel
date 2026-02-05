# Prod OpenAI Shadow Eval Summary (200 tickets)

- ticket_count: 200
- order_status_rate: 0.435

## Top 5 non-order-status intents
- unknown_other: 85
- cancel_order: 10
- order_status_tracking: 6
- technical_support: 4
- cancel_subscription: 3

## Match rate (order_number vs email)
- order_number: 0.724
- email: 0.276
- order_status_count: 87
- matched_by_order_number: 63
- matched_by_email: 24

## Rate-limit metrics
- retries: 0
- 429_count: 0

## Does this align with expectation (~30-40%)?
- yes - order_status_rate=0.435 aligns with the confirmed >40% expectation for this ticket set
