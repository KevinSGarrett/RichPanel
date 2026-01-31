# Sandbox OpenAI Order Status Proof

- Status: `PASS_STRONG`
- Run ID: `b65-dev-20260131-b1`
- Environment: `dev` (Richpanel sandbox)

## Env flags
- `MW_OPENAI_ROUTING_ENABLED=true`
- `MW_OPENAI_INTENT_ENABLED=true`
- `MW_OPENAI_REWRITE_ENABLED=true`
- `MW_OPENAI_SHADOW_ENABLED=true`
- `RICHPANEL_OUTBOUND_ENABLED=true`
- `MW_ALLOW_NETWORK_READS=true`
- `OPENAI_ALLOW_NETWORK=true`

## Command
`python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --scenario order_status_tracking --require-openai-routing --require-openai-rewrite --create-ticket --proof-path REHYDRATION_PACK/RUNS/B65/A/PROOF/sandbox_openai_order_status_proof.json --run-id b65-dev-20260131-b1 --wait-seconds 120 --profile rp-admin-kevin`

## OpenAI evidence
- Routing response_id: `chatcmpl-D4DpBmF3dgb4tu0BwIrTfaQ1CmDDR`
- Intent response_id: `chatcmpl-D4DpRryCwf5RgflSRww1Jzs2seMWE`
- Rewrite response_id: `chatcmpl-D4DpFNc1D3RyYmf0S7mkKE1Rx2YLA`

## Notes
- Dev is the Richpanel sandbox environment.
- Proof JSON redacts identifiers; no raw ticket text is stored beyond sanitized excerpts.
