# Shadow Read-Only Report - B59/C

## Run metadata
- Run ID: `RUN_20260126_2030Z`
- Generated (UTC): 2026-01-26T20:31:54Z
- Environment: `prod`
- Shop domain: `scentimen-t.myshopify.com`
- Sample: 17 explicit ticket IDs (hashed in artifacts)

## Results
- Tickets scanned: 17
- Orders matched: 17
- Orders unmatched: 0
- Tracking found: 11
- ETA available: 17
- Errors: 0
- Shopify probe: 200 OK

## Read-only verification
- HTTP trace allowed methods only: `true`
- Methods: `{"GET": 198, "POST": 22}` (POSTs are AWS SecretsManager GetSecretValue)
- Services: `{"richpanel": 170, "shopify": 21, "shipstation": 6, "aws_secretsmanager": 22, "aws_portal": 1}`

## Notes
- Richpanel conversation endpoints returned 403 for some tickets; ticket reads still succeeded.
- Ticket identifiers are hashed; no message bodies or customer identifiers are stored.
- Source artifacts:
  - `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260126_2030Z.json`
  - `artifacts/readonly_shadow/live_readonly_shadow_eval_report_RUN_20260126_2030Z.md`
  - `artifacts/readonly_shadow/live_readonly_shadow_eval_http_trace_RUN_20260126_2030Z.json`
