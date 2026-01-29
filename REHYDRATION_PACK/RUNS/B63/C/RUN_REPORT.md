# Run Report — B63/C

## Metadata
- Date (UTC): 2026-01-29
- Run ID: `RUN_20260129_0150Z`
- Branch: `b63/shadow-validator-drift-triage`
- Workspace: `C:\RichPanel_GIT`
- Environment: `prod` (read-only)
- Status: `OK` (drift_watch.has_alerts=false; run_warnings: ticket_fetch_failed)

## Objective
Stabilize shadow validator drift-watch by filtering noisy schema keys while keeping real contract drift detectable, then produce a green read-only shadow report.

## Summary
- ticket_count: 109; match_success_rate: 81.65%
- tracking_or_eta_available_rate: 79.82%; would_reply_send: false
- match_methods: order_number=51, name_email=23, email_only=15, none=20
- match_failure_buckets: no_order_number=5, no_order_candidates=1, no_email=1, other_failure=13
- run_warnings: ticket_fetch_failed (stale explicit ticket IDs)
- drift_watch.has_alerts: false (api_error_rate=0.0%, schema_new_ratio=13.54%)
- shopify_probe.status_code: 200
- http_trace_summary.allowed_methods_only: true

## Drift driver table
| Key path | Category | Proposed handling |
| --- | --- | --- |
| `id`, `scenario_id`, `organization_id`, `assignee_id` | Noisy / expected (IDs) | Ignore in schema fingerprint (implemented) |
| `created_at`, `updated_at`, `first_closed_at` | Noisy / expected (timestamps) | Ignore in schema fingerprint (implemented) |
| `url`, pagination keys (`page`, `cursor`) | Noisy / expected (metadata) | Ignore in schema fingerprint (implemented) |
| `comments` / `comments[]` | Noisy / expected (message subtree) | Keep presence but stop descent (implemented) |
| `customFields` / `custom_fields` | Noisy / expected (custom fields) | Keep presence but stop descent (implemented) |
| `customer_profile.email`, `via.channel`, `order_number` | Real contract drift | Keep; alert if missing/renamed/shape change |

## Artifacts
- `REHYDRATION_PACK/RUNS/B63/C/PROOF/live_shadow_report.json`
- `REHYDRATION_PACK/RUNS/B63/C/PROOF/live_shadow_summary.json`
- `REHYDRATION_PACK/RUNS/B63/C/PROOF/live_shadow_summary.md`
- `REHYDRATION_PACK/RUNS/B63/C/PROOF/live_shadow_http_trace.json`

## Notes
- Ticket listing endpoints returned 403; explicit IDs were used from the secret, yielding 13 stale IDs (warning only).
- Schema key stats for drift triage are in `schema_key_stats` within the summary JSON.
