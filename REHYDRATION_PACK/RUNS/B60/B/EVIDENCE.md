# Evidence — B60/B

## Sandbox prep (no secrets)
- Updated dev worker Lambda code package to include allowlist gating.
- Set `MW_OUTBOUND_ALLOWLIST_EMAILS` on `rp-mw-dev-worker` (value redacted).

## Allowlisted run — create-ticket API call summary (no secrets)
- POST `/v1/tickets` (channel=email, tags=`["mw-smoke-autoticket"]`)
- from_email_redacted: `redacted:bd7b0dc44282`
- subject_fingerprint: `50958548edbd`
- body_fingerprint: `239d62776d95`
- ticket_number_redacted: `redacted:63ecbfa3a1ad`
- conversation_id_redacted: `redacted:224e9bc0c14b`

## Allowlisted run — command
```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario order_status --create-ticket --ticket-from-email <redacted> --ticket-subject <redacted> --ticket-body <redacted> --require-openai-routing --require-openai-rewrite --require-outbound --require-operator-reply --require-send-message-path --followup --run-id B60-SANDBOX-ALLOWLIST-20260126-1700Z --proof-path REHYDRATION_PACK\RUNS\B60\B\PROOF\order_status_allowlist_send_proof.json --create-ticket-proof-path REHYDRATION_PACK\RUNS\B60\B\PROOF\created_ticket_allowlist.json
```

## Allowlisted run — key proof fields
- `ticket_channel`: "email"
- `openai_routing_used`: true
- `openai_rewrite_used`: true
- `operator_reply_present`: true
- `operator_reply_required`: true
- `operator_reply_confirmed`: true
- `send_message_path_required`: true
- `send_message_path_confirmed`: true
- `allowlist_blocked_tag_present`: false

## Blocked run — create-ticket API call summary (no secrets)
- POST `/v1/tickets` (channel=email, tags=`["mw-smoke-autoticket"]`)
- from_email_redacted: `redacted:ddf5785522f0`
- subject_fingerprint: `9c2688817b24`
- body_fingerprint: `d03caec59a68`
- ticket_number_redacted: `redacted:b280279a0ef2`
- conversation_id_redacted: `redacted:54e1d8a47b61`

## Blocked run — command
```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario order_status --create-ticket --ticket-from-email <redacted> --ticket-subject <redacted> --ticket-body <redacted> --require-allowlist-blocked --run-id B60-SANDBOX-BLOCKED-20260126-1730Z --proof-path REHYDRATION_PACK\RUNS\B60\B\PROOF\order_status_allowlist_blocked_proof.json --create-ticket-proof-path REHYDRATION_PACK\RUNS\B60\B\PROOF\created_ticket_blocked.json
```

## Blocked run — key proof fields
- `ticket_channel`: "email"
- `allowlist_blocked_tag_present`: true
- `send_message_tag_absent`: true
- `send_message_tag_present`: false
- `operator_reply_present`: false

## Proof artifacts
- `REHYDRATION_PACK/RUNS/B60/B/PROOF/created_ticket_allowlist.json`
- `REHYDRATION_PACK/RUNS/B60/B/PROOF/order_status_allowlist_send_proof.json`
- `REHYDRATION_PACK/RUNS/B60/B/PROOF/created_ticket_blocked.json`
- `REHYDRATION_PACK/RUNS/B60/B/PROOF/order_status_allowlist_blocked_proof.json`
