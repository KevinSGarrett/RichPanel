# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260128_1811Z`
- Generated (UTC): 2026-01-28T18:11:43.264869+00:00
- Environment: `prod`
- Region: `us-east-2`
- Stack name: `n/a`
- Sample mode: `explicit`
- Tickets requested: 17
- Tickets scanned: 17
- Orders matched: 17
- Tracking found: 11
- ETA available: 17
- Tracking or ETA available: 17
- Match success rate: 100.0%
- Would reply send: False
- Errors: 0
- Shopify probe enabled: True
- Shopify probe ok: True
- Shopify probe status: 200
- Summary path: `artifacts/readonly_shadow/live_shadow_summary.json`
- Drift warning: True
- Run warnings: none

## Route Decision Distribution (B61/C)
- Order Status: 0 (0.0%)
- Non-Order Status: 17 (100.0%)
- Unknown: 0 (0.0%)

## Match Method Telemetry (B61/C)
- Order Number: 11 (64.7%)
- Name + Email: 3 (17.6%)
- Email Only: 3 (17.6%)
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
- Order Number Share: 64.7% (threshold: drop > 15.0%)
- Schema Drift: 52.9% (threshold: > 20.0%)
- **Alerts: 1**
  - ⚠️ Schema drift (52.9%) exceeds threshold (20.0%)

## HTTP Trace Summary
- Total requests: 190
- Methods: {"GET": 190}
- Services: {"richpanel": 170, "shopify": 20}
- Sources: {"urllib": 190}
- AWS operations: {}
- AWS missing operations: 0
- Allowed methods only: True
- Trace path: `artifacts/readonly_shadow/live_shadow_http_trace.json`

## Notes
- Ticket identifiers are hashed in the JSON report.
- Shopify shop domains are hashed in the JSON report.
- No message bodies or customer identifiers are stored.
- HTTP trace captures urllib.request and AWS SDK (botocore) calls.
