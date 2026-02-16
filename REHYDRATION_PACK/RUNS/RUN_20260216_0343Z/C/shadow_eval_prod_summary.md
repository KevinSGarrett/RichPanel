# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260216_0348Z`
- Generated (UTC): 2026-02-16T03:50:42.810430+00:00
- Environment: `prod`
- Region: `us-east-2`
- Stack name: `n/a`
- Sample mode: `explicit`
- Tickets requested: 11
- Tickets scanned: 11
- Orders matched: 11
- Tracking found: 10
- ETA available: 11
- Tracking or ETA available: 11
- Match success rate: 100.0%
- Would reply send: False
- Errors: 0
- Shopify probe enabled: True
- Shopify probe ok: True
- Shopify probe status: 200
- Summary path: `C:\RichPanel_GIT\REHYDRATION_PACK\RUNS\RUN_20260216_0343Z\C\live_shadow_summary.json`
- Drift warning: True
- Run warnings: none

## Route Decision Distribution (B61/C)
- Order Status: 9 (81.8%)
- Non-Order Status: 2 (18.2%)
- Unknown: 0 (0.0%)

## Match Method Telemetry (B61/C)
- Order Number: 9 (81.8%)
- Name + Email: 2 (18.2%)
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
- Order Number Share: 81.8% (threshold: drop > 15.0%)
- Schema Drift: 54.5% (threshold: > 20.0%)
- **Alerts: 1**
  - ⚠️ Schema drift (54.5%) exceeds threshold (20.0%)

## HTTP Trace Summary
- Total requests: 208
- Methods: {"GET": 151, "POST": 57}
- Services: {"aws_portal": 1, "aws_secretsmanager": 35, "openai": 22, "richpanel": 128, "shipstation": 1, "shopify": 21}
- Sources: {"aws_sdk": 36, "urllib": 172}
- AWS operations: {"GetSecretValue": 35}
- AWS missing operations: 0
- Allowed methods only: True
- Trace path: `C:\RichPanel_GIT\REHYDRATION_PACK\RUNS\RUN_20260216_0343Z\C\live_shadow_http_trace.json`

## Richpanel Burst Summary (30s)
- Max requests in any 30s window: 40

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
