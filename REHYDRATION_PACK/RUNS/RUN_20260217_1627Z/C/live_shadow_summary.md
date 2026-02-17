# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260217_1730Z`
- Generated (UTC): 2026-02-17T17:33:15.002351+00:00
- Environment: `prod`
- Region: `us-east-2`
- Stack name: `n/a`
- Sample mode: `explicit`
- Tickets requested: 10
- Tickets scanned: 10
- Orders matched: 10
- Tracking found: 6
- ETA available: 10
- Tracking or ETA available: 10
- Match success rate: 100.0%
- Would reply send: False
- Errors: 0
- Shopify probe enabled: True
- Shopify probe ok: True
- Shopify probe status: 200
- Summary path: `REHYDRATION_PACK\RUNS\RUN_20260217_1627Z\C\live_shadow_summary.json`
- Drift warning: True
- Run warnings: none

## Route Decision Distribution (B61/C)
- Order Status: 9 (90.0%)
- Non-Order Status: 1 (10.0%)
- Unknown: 0 (0.0%)

## Match Method Telemetry (B61/C)
- Order Number: 9 (90.0%)
- Name + Email: 0 (0.0%)
- Email Only: 1 (10.0%)
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
- Order Number Share: 90.0% (threshold: drop > 15.0%)
- Schema Drift: 40.0% (threshold: > 20.0%)
- **Alerts: 1**
  - ⚠️ Schema drift (40.0%) exceeds threshold (20.0%)

## HTTP Trace Summary
- Total requests: 223
- Methods: {"GET": 147, "POST": 76}
- Services: {"aws_portal": 1, "aws_secretsmanager": 56, "openai": 20, "richpanel": 118, "shipstation": 8, "shopify": 20}
- Sources: {"aws_sdk": 57, "urllib": 166}
- AWS operations: {"GetSecretValue": 56}
- AWS missing operations: 0
- Allowed methods only: True
- Trace path: `REHYDRATION_PACK\RUNS\RUN_20260217_1627Z\C\live_shadow_http_trace.json`

## Richpanel Burst Summary (30s)
- Max requests in any 30s window: 30

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
