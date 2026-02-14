# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260213_1955Z`
- Generated (UTC): 2026-02-13T19:55:41.031186+00:00
- Environment: `prod`
- Region: `us-east-2`
- Stack name: `n/a`
- Sample mode: `explicit`
- Tickets requested: 1
- Tickets scanned: 1
- Orders matched: 1
- Tracking found: 1
- ETA available: 1
- Tracking or ETA available: 1
- Match success rate: 100.0%
- Would reply send: False
- Errors: 0
- Shopify probe enabled: True
- Shopify probe ok: True
- Shopify probe status: 200
- Summary path: `C:\RichPanel_GIT\REHYDRATION_PACK\RUNS\RUN_20260213_1603Z\b80\live_shadow_summary.json`
- Drift warning: True
- Run warnings: none

## Route Decision Distribution (B61/C)
- Order Status: 0 (0.0%)
- Non-Order Status: 1 (100.0%)
- Unknown: 0 (0.0%)

## Match Method Telemetry (B61/C)
- Order Number: 1 (100.0%)
- Name + Email: 0 (0.0%)
- Email Only: 0 (0.0%)
- No Match: 0 (0.0%)
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
- Other/Unknown: 0

## Drift Watch (B61/C)
- Match Rate: 100.0% (threshold: drop > 10.0%)
- API Error Rate: 0.0% (threshold: > 5.0%)
- Ticket Fetch Failure Rate: 0.0% (warning-only)
- Order Number Share: 100.0% (threshold: drop > 15.0%)
- Schema Drift: 100.0% (threshold: > 20.0%)
- **Alerts: 1**
  - ⚠️ Schema drift (100.0%) exceeds threshold (20.0%)

## HTTP Trace Summary
- Total requests: 26
- Methods: {"GET": 16, "POST": 10}
- Services: {"aws_portal": 1, "aws_secretsmanager": 8, "openai": 2, "richpanel": 12, "shopify": 3}
- Sources: {"aws_sdk": 9, "urllib": 17}
- AWS operations: {"GetSecretValue": 8}
- AWS missing operations: 0
- Allowed methods only: True
- Trace path: `C:\RichPanel_GIT\REHYDRATION_PACK\RUNS\RUN_20260213_1603Z\b80\live_shadow_http_trace.json`

## Richpanel Burst Summary (30s)
- Max requests in any 30s window: 10

## Retry-After Validation
- Checked: 0; violations: 0

## Richpanel Identity
- base_url: https://api.richpanel.com
- resolved_env: prod
- api_key_hash: 7ab000f0
- api_key_secret_id: rp-mw/prod/richpanel/api_key

## Notes
- Ticket identifiers are hashed in the JSON report.
- Shopify shop domains are hashed in the JSON report.
- No message bodies or customer identifiers are stored.
- HTTP trace captures urllib.request and AWS SDK (botocore) calls.
