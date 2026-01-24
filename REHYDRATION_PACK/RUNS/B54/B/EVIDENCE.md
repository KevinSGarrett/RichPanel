# B54 Evidence

## Command(s)
```
python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --scenario order_status --ticket-number <redacted> --require-outbound --require-openai-routing --require-openai-rewrite --followup --run-id b54-20260123151223 --proof-path REHYDRATION_PACK/RUNS/B54/B/PROOF/order_status_outbound_followup_proof.json
```

## PASS_STRONG excerpt
```
[RESULT] classification=PASS_STRONG; status=PASS; failure_reason=none
```

## Key proof fields (from JSON)
- `openai_routing_used`: true
- `openai_rewrite_used`: true
- `closed_after`: true
- `message_count_delta`: 1
- `last_message_source_after`: middleware
- `followup_routed_support`: true
- `followup_reply_sent`: false
- `followup_skip_tags_added`: `["mw-skip-followup-after-auto-reply", "route-email-support-team"]`

## Proof artifact
- `REHYDRATION_PACK/RUNS/B54/B/PROOF/order_status_outbound_followup_proof.json`
