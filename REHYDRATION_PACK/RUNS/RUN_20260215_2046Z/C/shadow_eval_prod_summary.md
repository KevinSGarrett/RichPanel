# Live Read-Only Shadow Eval Report

- Run ID: `RUN_20260215_2147Z`
- Generated (UTC): 2026-02-15T21:49:23.518667+00:00
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
- Summary path: `REHYDRATION_PACK\RUNS\RUN_20260215_2046Z\C\live_shadow_summary.json`
- Drift warning: True
- Run warnings: none

## Route Decision Distribution (B61/C)
- Order Status: 0 (0.0%)
- Non-Order Status: 11 (100.0%)
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
- Trace path: `REHYDRATION_PACK\RUNS\RUN_20260215_2046Z\C\live_shadow_http_trace.json`

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

## Preorder Proof (B82)
- No draft bodies recorded; report contains booleans + body fingerprints only.
- would_reply_send: False (all tickets)
- Preorder tickets: 3
- Non-preorder tickets: 8 (no preorder wording detected)

### Preorder tickets (+45 ship date, tag evidence, reply signals)
| ticket_id_redacted | preorder_tag_matches | order_created_date | preorder_ship_date_human | ship_date_plus_45 | window_min_days | window_max_days | window_calc_iso | window_matches_business_days | delivery_window_human | ship_in_days | arrives_in_days | reply_has_preorder | reply_has_ship_date | reply_has_ship_schedule_phrase | reply_has_ship_in_days | reply_has_delivery_window | reply_has_estimated_delivery_phrase | reply_has_arrives_in_days | ends_with_tracking |
| - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| redacted:cb6d57d9b987 | pre-order | 2026-01-18 | Wednesday, March 4, 2026 | PASS | n/a | n/a | n/a | None | n/a | 21 days | n/a | True | True | True | True | False | False | False | True |
| redacted:ef6eeba126f7 | pre-order | 2026-01-17 | Tuesday, March 3, 2026 | PASS | 3 | 7 | 2026-03-06 to 2026-03-12 | True | March 6–March 12, 2026 | 18 days | 21–27 days | True | True | True | True | True | True | True | True |
| redacted:dbb9295f3e6c | pre-order | 2026-01-07 | Saturday, February 21, 2026 | PASS | 3 | 7 | 2026-02-25 to 2026-03-03 | True | February 25–March 3, 2026 | 8 days | 12–18 days | True | True | True | True | True | True | True | True |

### Non-preorder tickets (verified no preorder wording)
redacted:cd92c15d6341, redacted:a372973056e6, redacted:0074fb03dde8, redacted:fd6e103a5093, redacted:924e4905c954, redacted:f427ba602116, redacted:174deb98a48f, redacted:48bc2f8f66b1

