# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260126_0319Z`
- Generated (UTC): 2026-01-26T03:20:47.831935+00:00
- Environment: `prod`
- Region: `n/a`
- Stack name: `n/a`
- Sample mode: `explicit`
- Tickets requested: 17
- Tickets scanned: 17
- Orders matched: 16
- Tracking found: 11
- ETA available: 16
- Tracking or ETA available: 16
- Match success rate: 94.1%
- Would reply send: False
- Errors: 0
- Shopify probe enabled: True
- Shopify probe ok: True
- Shopify probe status: 200
- Summary path: `C:\RichPanel_GIT\REHYDRATION_PACK\RUNS\B62\C\PROOF\live_shadow_summary.json`
- Drift warning: False
- Run warnings: none

## Route Decision Distribution (B61/C)
- Order Status: 0 (0.0%)
- Non-Order Status: 17 (100.0%)
- Unknown: 0 (0.0%)

## Match Method Telemetry (B61/C)
- Order Number: 10 (58.8%)
- Name + Email: 3 (17.6%)
- Email Only: 3 (17.6%)
- No Match: 1 (5.9%)
- Parse Error: 0 (0.0%)

## Failure Buckets (B61/C - PII Safe)
- No Identifiers: 0
- Shopify API Error: 0
- Richpanel API Error: 0
- Ambiguous Match: 0
- No Order Candidates: 0
- Parse Error: 0
- Other Errors: 0

## Match Failure Buckets (Deployment Gate)
- No Email: 0
- No Order Number: 0
- Ambiguous Customer: 0
- No Order Candidates: 0
- Order Match Failed: 0
- Parse Error: 0
- API Error: 0
- Other/Unknown: 1

## Drift Watch (B61/C)
- Match Rate: 94.1% (threshold: drop > 10.0%)
- API Error Rate: 0.0% (threshold: > 5.0%)
- Order Number Share: 58.8% (threshold: drop > 15.0%)
- Schema Drift: 0.0% (threshold: > 20.0%)
- Alerts: 0

## HTTP Trace Summary
- Total requests: 218
- Methods: {"GET": 198, "POST": 20}
- Services: {"aws_portal": 2, "aws_secretsmanager": 20, "richpanel": 170, "shipstation": 5, "shopify": 21}
- Sources: {"aws_sdk": 22, "urllib": 196}
- AWS operations: {"GetSecretValue": 20}
- AWS missing operations: 0
- Allowed methods only: True
- Trace path: `C:\RichPanel_GIT\REHYDRATION_PACK\RUNS\B62\C\PROOF\live_shadow_http_trace.json`

## Notes
- Ticket identifiers are hashed in the JSON report.
- No message bodies or customer identifiers are stored.
- HTTP trace captures urllib.request and AWS SDK (botocore) calls.
