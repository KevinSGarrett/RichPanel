# Evidence — B64/Agent_A

## Scope and safety
- Sandbox/dev only; no production writes.
- Outbound replies limited to sandbox inboxes; identifiers redacted in artifacts.
- Proof JSON is PII-safe (guarded by `dev_e2e_smoke.py`).

## Proof command
```powershell
cd C:\RichPanel_GIT
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --profile rp-admin-kevin --scenario order_status_tracking --create-ticket --create-ticket-proof-path REHYDRATION_PACK/RUNS/B64/Agent_A/PROOF/created_ticket_order_status.json --proof-path REHYDRATION_PACK/RUNS/B64/Agent_A/PROOF/order_status_outbound_operator_reply_proof.json --require-operator-reply --require-send-message-used --require-send-message --wait-seconds 120
```

## Ticket reference (PII-safe)
- Ticket number: redacted:d40535ac09aa (fingerprint from `created_ticket_order_status.json`)
- Conversation id fingerprint: f35e3a9a8fa4

## /send-message evidence (2xx)
```json
{
  "proof_fields": {
    "send_message_used": true,
    "send_message_status_code": 200,
    "send_message_path_confirmed": true
  }
}
```

## Operator reply evidence (PII-safe snapshot excerpt)
```json
{
  "richpanel": {
    "post": {
      "ticket_channel": "email",
      "latest_comment_is_operator": true,
      "operator_reply_present": true
    }
  }
}
```

## Email delivery observation
- Operator reply visible in Richpanel UI for the ticket (see post snapshot excerpt).
- Sandbox inbox delivery observed for the created ticket’s from address (redacted hash `571abc2d0add`); verify in the mailbox tied to `MW_SMOKE_TICKET_FROM_EMAIL` if needed.
