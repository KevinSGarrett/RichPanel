# Agent Run Report

## Metadata
- **Run IDs:** `B61-SANDBOX-NOT-ORDER-STATUS-20260127-1735Z`, `B61-SANDBOX-NO-MATCH-20260127-1755Z`, `B61-SANDBOX-ALLOWLIST-BLOCKED-20260127-1935Z`
- **Agent:** B
- **Date (UTC):** 2026-01-27
- **Worktree path:** `C:\RichPanel_GIT`
- **Branch:** `b61/sandbox-e2e-negative-cases`
- **PR:** N/A

## Objective + stop conditions
- **Objective:** Add negative-case scenarios + proof fields to `dev_e2e_smoke.py`, unit tests for proof evaluation, and sandbox run docs for non-order-status, no-match, and allowlist-blocked cases.
- **Stop conditions:** PASS proof artifacts for non-order-status and no-match cases, plus PASS or explicit SKIP for allowlist-blocked when allowlist is configured or absent.

## What changed (high-level)
- Added negative-case scenarios (`not_order_status`, `order_status_no_match`, `allowlist_blocked`) with new proof fields for intent, outbound attempts, support routing, and order-match failure.
- Added allowlist config detection and SKIP proof output when allowlist gating is not configured, plus tag polling for allowlist-blocked proofs.
- Extended unit tests to cover new proof fields, skip behavior, and `--fail-on-outbound-block`.

## Commands to run (sandbox only)
- `python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario not_order_status --create-ticket --ticket-from-email <redacted> --ticket-subject <redacted> --ticket-body <redacted> --fail-on-outbound-block --run-id B61-SANDBOX-NOT-ORDER-STATUS-20260127-1735Z --proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\not_order_status_proof.json --create-ticket-proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\created_ticket_not_order_status.json`
- `python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario order_status_no_match --create-ticket --ticket-from-email <redacted> --ticket-subject <redacted> --ticket-body <redacted> --fail-on-outbound-block --run-id B61-SANDBOX-NO-MATCH-20260127-1755Z --proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\order_status_no_match_proof.json --create-ticket-proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\created_ticket_no_match.json`
- `python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario allowlist_blocked --create-ticket --ticket-from-email <redacted> --require-allowlist-blocked --run-id B61-SANDBOX-ALLOWLIST-BLOCKED-20260127-1935Z --proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\order_status_allowlist_blocked_proof.json --create-ticket-proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\created_ticket_allowlist_blocked.json`

## Tests
- `python scripts/run_ci_checks.py` (PASS)
- `python scripts/test_e2e_smoke_encoding.py` (PASS)

## Proof artifacts
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/created_ticket_not_order_status.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/not_order_status_proof.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/created_ticket_no_match.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/order_status_no_match_proof.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/created_ticket_allowlist_blocked.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/order_status_allowlist_blocked_proof.json`
