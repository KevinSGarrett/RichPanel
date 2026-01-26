# Evidence — B58/B

## Command(s)
```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario order_status --ticket-number <redacted> --require-outbound --require-operator-reply --require-send-message-path --followup --run-id B58-SANDBOX-20260125-OPR1110 --proof-path REHYDRATION_PACK\RUNS\B58\B\PROOF\order_status_operator_reply_followup_proof.json
```

## PASS_STRONG excerpt
```
[RESULT] classification=PASS_STRONG; status=PASS; failure_reason=none
```

## Key proof fields (from JSON)
- `ticket_channel`: email
- `latest_comment_is_operator`: true
- `operator_reply_required`: true
- `operator_reply_confirmed`: true
- `send_message_path_required`: true
- `send_message_path_confirmed`: true
- `send_message_tag_present`: true
- `closed_after`: true
- `followup_routed_support`: true
- `followup_reply_sent`: false
- `followup_skip_tags_added`: `["mw-skip-followup-after-auto-reply", "route-email-support-team"]`

## Proof artifact
- `REHYDRATION_PACK/RUNS/B58/B/PROOF/order_status_operator_reply_followup_proof.json`
