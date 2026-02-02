# B66 Sandbox Order Status E2E Golden Path

- Status: `PASS_STRONG`
- Run ID: `B66-SANDBOX-20260201-0006`
- Environment: `dev` (Richpanel sandbox)
- Timestamp: `2026-02-02T04:24:12.167998+00:00`

## Summary of proof
- Order-status intent detected: `order_status_tracking`
- Shopify order match by number: `true`
- Outbound reply used `/send-message` (operator-visible): `true`
- Ticket auto-closed: `true`
- Follow-up routed to support, no second auto-reply: `true`

## Commands (PII-safe)
```powershell
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status --require-openai-routing --require-openai-rewrite --require-order-match-by-number --require-outbound --require-send-message --require-send-message-used --require-operator-reply --followup --ticket-id <redacted> --order-number <redacted> --proof-path REHYDRATION_PACK\RUNS\B66\A\PROOF\order_status_sandbox_e2e_golden_path.json --run-id B66-SANDBOX-20260201-0004 --profile rp-admin-kevin
```

## Proof highlights (from JSON)
- Intent: `order_status_tracking`
- `/send-message` evidence: `mw-outbound-path-send-message` tag present
- Operator reply: `latest_comment_is_operator=true`
- Ticket status: `closed`
- Follow-up: `reply_sent=false`, `routed_to_support=true`
- Idempotency: `mw-skip-followup-after-auto-reply` tag present
- Extracted order number: `redacted:4a496557aaa0`
- Operator author id fingerprint: `847bae851598`
- Send-message comment id fingerprint: `7ba1f4fed3ff`

## Additional proof artifacts
- `REHYDRATION_PACK/RUNS/B66/A/PROOF/ticket_message_operator_proof.json`
- `REHYDRATION_PACK/RUNS/B66/A/PROOF/followup_real_reply_proof.json`
- `REHYDRATION_PACK/RUNS/B66/A/PROOF/gmail_delivery_proof.json` (status: `found`, subject query = `B66 Followup Thread`)

## Remaining gaps
- None.