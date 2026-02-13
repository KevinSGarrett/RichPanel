# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260213_1729Z`
- Generated (UTC): 2026-02-13T17:30:14.000672+00:00
- Environment: `prod`
- Region: `us-east-2`
- Stack name: `n/a`
- Sample mode: `explicit`
- Tickets requested: 7
- Tickets scanned: 7
- Orders matched: 7
- Tracking found: 7
- ETA available: 7
- Tracking or ETA available: 7
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
- Non-Order Status: 7 (100.0%)
- Unknown: 0 (0.0%)

## Match Method Telemetry (B61/C)
- Order Number: 6 (85.7%)
- Name + Email: 1 (14.3%)
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
- Order Number Share: 85.7% (threshold: drop > 15.0%)
- Schema Drift: 42.9% (threshold: > 20.0%)
- **Alerts: 1**
  - ⚠️ Schema drift (42.9%) exceeds threshold (20.0%)

## HTTP Trace Summary
- Total requests: 140
- Methods: {"GET": 100, "POST": 40}
- Services: {"aws_portal": 1, "aws_secretsmanager": 26, "openai": 14, "richpanel": 84, "shopify": 15}
- Sources: {"aws_sdk": 27, "urllib": 113}
- AWS operations: {"GetSecretValue": 26}
- AWS missing operations: 0
- Allowed methods only: True
- Trace path: `C:\RichPanel_GIT\REHYDRATION_PACK\RUNS\RUN_20260213_1603Z\b80\live_shadow_http_trace.json`

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
