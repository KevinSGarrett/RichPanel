# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260128_1637Z`
- Generated (UTC): 2026-01-28T16:39:10.756289+00:00
- Environment: `prod`
- Region: `us-east-2`
- Stack name: `n/a`
- Sample mode: `explicit`
- Tickets requested: 17
- Tickets scanned: 17
- Orders matched: 0
- Tracking found: 0
- ETA available: 0
- Tracking or ETA available: 0
- Match success rate: 0.0%
- Would reply send: False
- Errors: 8
- Shopify probe enabled: True
- Shopify probe ok: False
- Shopify probe status: 401
- Summary path: `artifacts/readonly_shadow/live_shadow_summary.json`
- Drift warning: True
- Run warnings: ticket_fetch_failed

## Route Decision Distribution (B61/C)
- Order Status: 0 (0.0%)
- Non-Order Status: 9 (52.9%)
- Unknown: 8 (47.1%)

## Match Method Telemetry (B61/C)
- Order Number: 0 (0.0%)
- Name + Email: 0 (0.0%)
- Email Only: 0 (0.0%)
- No Match: 17 (100.0%)
- Parse Error: 0 (0.0%)

## Failure Buckets (B61/C - PII Safe)
- No Identifiers: 0
- Shopify API Error: 0
- Richpanel API Error: 0
- Ambiguous Match: 0
- No Order Candidates: 9
- Parse Error: 0
- Other Errors: 8

## Match Failure Buckets (Deployment Gate)
- No Email: 0
- No Order Number: 3
- Ambiguous Customer: 0
- No Order Candidates: 6
- Order Match Failed: 0
- Parse Error: 0
- API Error: 0
- Other/Unknown: 8

## Drift Watch (B61/C)
- Match Rate: 0.0% (threshold: drop > 10.0%)
- API Error Rate: 47.1% (threshold: > 5.0%)
- Order Number Share: 0.0% (threshold: drop > 15.0%)
- Schema Drift: 66.7% (threshold: > 20.0%)
- **Alerts: 2**
  - ⚠️ API error rate (47.1%) exceeds threshold (5.0%)
  - ⚠️ Schema drift (66.7%) exceeds threshold (20.0%)

## HTTP Trace Summary
- Total requests: 164
- Methods: {"GET": 164}
- Services: {"richpanel": 142, "shopify": 22}
- Sources: {"urllib": 164}
- AWS operations: {}
- AWS missing operations: 0
- Allowed methods only: True
- Trace path: `artifacts/readonly_shadow/live_shadow_http_trace.json`

## Notes
- Ticket identifiers are hashed in the JSON report.
- No message bodies or customer identifiers are stored.
- HTTP trace captures urllib.request and AWS SDK (botocore) calls.
