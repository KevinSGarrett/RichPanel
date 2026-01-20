# Test Matrix — RUN_20260120_2350Z (Agent B)

## Sandbox E2E Proofs (DEV)

### Order Status — Tracking (attempts failed)
- **Command:** `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number 1062 --confirm-test-ticket --diagnose-ticket-update --run-id RUN_20260120_2350Z --scenario order_status_tracking --proof-path REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_tracking_proof.json`
- **Result:** FAIL (skip_or_escalation_tags_present)
- **Evidence:** `REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_tracking_proof.json`
- **Notes:** Tickets 1062, 1050, 1049, 1048 all produced `route-email-support-team` + `mw-skip-*` tags; need a fresh open ticket without loop-prevention tags.

### Order Status — No Tracking (attempt failed)
- **Command:** `python scripts/dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 120 --profile rp-admin-kevin --ticket-number 1051 --confirm-test-ticket --diagnose-ticket-update --run-id RUN_20260120_2350Z --scenario order_status_no_tracking --proof-path REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_no_tracking_proof.json`
- **Result:** FAIL (skip_or_escalation_tags_present)
- **Evidence:** `REHYDRATION_PACK/RUNS/RUN_20260120_2350Z/B/e2e_order_status_no_tracking_proof.json`
- **Notes:** Ticket 1051 had loop-prevention tags; need a fresh open ticket without prior auto-reply.

## Local Checks
- `python scripts/test_e2e_smoke_encoding.py` — PASS
- `python scripts/run_ci_checks.py --ci` — PASS (warnings remain for legacy run folder naming)
