# Evidence — B59/B

## Create-ticket API call summary (no secrets)
- POST `/v1/tickets` (channel=email, tags=`["mw-smoke-autoticket"]`)
- from_email_redacted: `redacted:571abc2d0add`
- subject_fingerprint: `7952ecef0ebf`
- body_fingerprint: `273d941da5cc`
- ticket_number_redacted: `redacted:b7e307660e16`
- conversation_id_redacted: `redacted:b38cfc99e990`

## Command(s)
```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario order_status --create-ticket --ticket-from-email <redacted> --ticket-subject <redacted> --ticket-body <redacted> --require-openai-routing --require-openai-rewrite --require-outbound --require-operator-reply --require-send-message-path --followup --run-id B59-SANDBOX-AUTOTICKET-20260126-1254Z --proof-path REHYDRATION_PACK\RUNS\B59\B\PROOF\order_status_operator_reply_followup_proof_autoticket.json --create-ticket-proof-path REHYDRATION_PACK\RUNS\B59\B\PROOF\created_ticket.json
```

## Key proof fields (from JSON)
- `openai_routing_used`: true
- `openai_rewrite_used`: true
- `latest_comment_is_operator`: true
- `operator_reply_required`: true
- `operator_reply_confirmed`: true
- `send_message_path_required`: true
- `send_message_path_confirmed`: true
- `send_message_tag_present`: true
- `closed_after`: true
- `followup_routed_support`: true
- `followup_reply_sent`: false

## Proof artifacts
- `REHYDRATION_PACK/RUNS/B59/B/PROOF/created_ticket.json`
- `REHYDRATION_PACK/RUNS/B59/B/PROOF/order_status_operator_reply_followup_proof_autoticket.json`
