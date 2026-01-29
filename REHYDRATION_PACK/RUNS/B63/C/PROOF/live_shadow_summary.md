# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260129_0150Z`
- Generated (UTC): 2026-01-29T01:55:25.434856+00:00
- Environment: `prod`
- Region: `us-east-2`
- Stack name: `n/a`
- Sample mode: `explicit`
- Tickets requested: 109
- Tickets scanned: 109
- Orders matched: 89
- Tracking found: 70
- ETA available: 84
- Tracking or ETA available: 87
- Match success rate: 81.7%
- Would reply send: False
- Errors: 13
- Shopify probe enabled: True
- Shopify probe ok: True
- Shopify probe status: 200
- Summary path: `artifacts/readonly_shadow/live_shadow_summary.json`
- Drift warning: False
- Run warnings: ticket_fetch_failed

## Route Decision Distribution (B61/C)
- Order Status: 0 (0.0%)
- Non-Order Status: 96 (88.1%)
- Unknown: 13 (11.9%)

## Match Method Telemetry (B61/C)
- Order Number: 51 (46.8%)
- Name + Email: 23 (21.1%)
- Email Only: 15 (13.8%)
- No Match: 20 (18.4%)
- Parse Error: 0 (0.0%)

## Failure Buckets (B61/C - PII Safe)
- No Identifiers: 1
- Shopify API Error: 0
- Richpanel API Error: 0
- Ambiguous Match: 0
- No Order Candidates: 6
- Parse Error: 0
- Other Errors: 13

## Match Failure Buckets (Deployment Gate)
- No Email: 1
- No Order Number: 5
- Ambiguous Customer: 0
- No Order Candidates: 1
- Order Match Failed: 0
- Parse Error: 0
- API Error: 0
- Other/Unknown: 13

## Drift Watch (B61/C)
- Match Rate: 81.7% (threshold: drop > 10.0%)
- API Error Rate: 0.0% (threshold: > 5.0%)
- Order Number Share: 46.8% (threshold: drop > 15.0%)
- Schema Drift: 13.5% (threshold: > 20.0%)
- **Alerts: 0**

## HTTP Trace Summary
- Total requests: 1164
- Methods: {"GET": 1164}
- Services: {"richpanel": 1055, "shopify": 109}
- Sources: {"urllib": 1164}
- AWS operations: {}
- AWS missing operations: 0
- Allowed methods only: True
- Trace path: `artifacts/readonly_shadow/live_shadow_http_trace.json`

## Notes
- Ticket identifiers are hashed in the JSON report.
- Shopify shop domains are hashed in the JSON report.
- No message bodies or customer identifiers are stored.
- HTTP trace captures urllib.request and AWS SDK (botocore) calls.
