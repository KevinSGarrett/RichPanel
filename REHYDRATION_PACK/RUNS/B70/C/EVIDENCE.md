# B70 C Evidence

## Successful DEV E2E run (PII-safe)
- **Proof summary:** `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_summary.json`
- **Full proof:** `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_run7.json`
- **Created ticket artifact:** `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_created_ticket_run7.json`

## Key proof fields (from summary)
- `send_message_endpoint_used: true`
- `send_message_status_code: 200`
- `latest_comment_is_operator: true`
- `send_message_author_matches_bot_agent: true`
- `order_match_by_number: true`
- `order_match_method: order_number` (source: `shopify_lookup_probe`)
- `openai_routing_used: true`
- `openai_rewrite_used: true`
- `closed_after: true`

## Command (redacted)
```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_tracking --create-ticket --order-number <redacted> --require-openai-routing --require-openai-rewrite --require-order-match-by-number --require-outbound --require-send-message --require-send-message-used --require-operator-reply --proof-path REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_run7.json --create-ticket-proof-path REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_created_ticket_run7.json --run-id B70-C-20260204-0007 --wait-seconds 120 --profile rp-admin-dev
```

## Additional artifacts (failed attempts for traceability)
- `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof.json` (order_match_by_number failed)
- `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_run2.json` (skip/escalation tags present)
- `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_run3.json` (no outbound message delta)
- `REHYDRATION_PACK/RUNS/B70/C/PROOF/sandbox_order_status_dev_proof_run4.json` (no outbound message delta)
