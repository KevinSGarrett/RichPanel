# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260129_0213Z`
- Generated (UTC): 2026-01-29T02:17:36.551508+00:00
- Environment: `prod`
- Region: `us-east-2`
- Stack name: `n/a`
- Sample mode: `explicit`
- Tickets requested: 109
- Tickets scanned: 109
- Orders matched: 84
- Tracking found: 68
- ETA available: 79
- Tracking or ETA available: 82
- Match success rate: 77.1%
- Would reply send: False
- Errors: 17
- Shopify probe enabled: True
- Shopify probe ok: True
- Shopify probe status: 200
- Summary path: `artifacts/readonly_shadow/live_shadow_summary.json`
- Drift warning: False
- Run warnings: ticket_fetch_failed

## Route Decision Distribution (B61/C)
- Order Status: 0 (0.0%)
- Non-Order Status: 92 (84.4%)
- Unknown: 17 (15.6%)

## Match Method Telemetry (B61/C)
- Order Number: 47 (43.1%)
- Name + Email: 21 (19.3%)
- Email Only: 16 (14.7%)
- No Match: 25 (22.9%)
- Parse Error: 0 (0.0%)

## Failure Buckets (B61/C - PII Safe)
- No Identifiers: 1
- Shopify API Error: 0
- Richpanel API Error: 0
- Ambiguous Match: 0
- No Order Candidates: 7
- Parse Error: 0
- Other Errors: 17

## Match Failure Buckets (Deployment Gate)
- No Email: 1
- No Order Number: 6
- Ambiguous Customer: 0
- No Order Candidates: 1
- Order Match Failed: 0
- Parse Error: 0
- API Error: 0
- Other/Unknown: 17

## Drift Watch (B61/C)
- Match Rate: 77.1% (threshold: drop > 10.0%)
- API Error Rate: 0.0% (threshold: > 5.0%)
- Ticket Fetch Failure Rate: 15.6% (warning-only)
- Order Number Share: 43.1% (threshold: drop > 15.0%)
- Schema Drift: 15.2% (threshold: > 20.0%)
- **Alerts: 0**

## HTTP Trace Summary
- Total requests: 1174
- Methods: {"GET": 1174}
- Services: {"richpanel": 1071, "shopify": 103}
- Sources: {"urllib": 1174}
- AWS operations: {}
- AWS missing operations: 0
- Allowed methods only: True
- Trace path: `artifacts/readonly_shadow/live_shadow_http_trace.json`

## Notes
- Ticket identifiers are hashed in the JSON report.
- Shopify shop domains are hashed in the JSON report.
- No message bodies or customer identifiers are stored.
- HTTP trace captures urllib.request and AWS SDK (botocore) calls.
