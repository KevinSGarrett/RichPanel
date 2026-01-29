# Evidence — B64/Agent_A

## Scope and safety
- Sandbox/dev only; no production writes.
- Outbound replies limited to sandbox inboxes; identifiers redacted in artifacts.
- Proof JSON is PII-safe (guarded by `dev_e2e_smoke.py`).

## Proof command
```powershell
cd C:\RichPanel_GIT
$env:MW_SMOKE_TICKET_FROM_EMAIL="<redacted>"
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --profile rp-admin-kevin --scenario order_status_tracking --create-ticket --create-ticket-proof-path REHYDRATION_PACK/RUNS/B64/Agent_A/PROOF/created_ticket_order_status.json --proof-path REHYDRATION_PACK/RUNS/B64/Agent_A/PROOF/order_status_outbound_operator_reply_proof.json --require-operator-reply --require-send-message-used --require-send-message --wait-seconds 120
```

```powershell
python scripts/gmail_delivery_verify.py --query newer_than:2d in:anywhere subject:Sandbox subject:autoticket --expected-to <redacted> --max-results 50 --out REHYDRATION_PACK/RUNS/B64/Agent_A/PROOF/gmail_delivery_proof.json
```

## Ticket reference (PII-safe)
- Ticket number: redacted:ca153fc499ff (fingerprint from `created_ticket_order_status.json`)
- Conversation id fingerprint: 0f90947a4c6c

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
- Gmail delivery confirmed via `gmail_delivery_proof.json` (status=found, expected_to_match_count=1; message timestamp 2026-01-29T16:57:51Z).
