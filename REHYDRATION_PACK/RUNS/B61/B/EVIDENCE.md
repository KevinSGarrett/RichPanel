# Evidence — B61/B

## Scope and safety
- Sandbox only; no production writes.
- All values PII-safe; use `<redacted>` for any real emails or subjects.

## Scenario 1 — Not order status (route-to-support, no outbound)
**Why no outbound:** intent is non-order-status (cancel subscription), should route to Email Support Team with no automated reply attempt.

**Command (sandbox):**
```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario not_order_status --create-ticket --ticket-from-email <redacted> --ticket-subject <redacted> --ticket-body <redacted> --fail-on-outbound-block --run-id B61-SANDBOX-NOT-ORDER-STATUS-20260127-1735Z --proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\not_order_status_proof.json --create-ticket-proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\created_ticket_not_order_status.json
```

**Proof fields to verify:**
- `intent_after` is **not** order_status*
- `outbound_attempted` is false
- `routed_to_support` is true (Email Support Team)

## Scenario 2 — Order status, no match (route-to-support, no outbound)
**Why no outbound:** order-status intent present, but order context missing or no match; should route to support with no send.

**Command (sandbox):**
```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario order_status_no_match --create-ticket --ticket-from-email <redacted> --ticket-subject <redacted> --ticket-body <redacted> --fail-on-outbound-block --run-id B61-SANDBOX-NO-MATCH-20260127-1755Z --proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\order_status_no_match_proof.json --create-ticket-proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\created_ticket_no_match.json
```

**Proof fields to verify:**
- `intent_after` is order_status*
- `order_match_success` is false
- `order_match_failure_reason` is set (PII-safe)
- `outbound_attempted` is false
- `routed_to_support` is true

## Scenario 3 — Allowlist blocked (tagged + routed to support, no send)
**Why no outbound:** allowlist gating blocks outbound; tag applied and ticket routed to support.

**Command (sandbox):**
```powershell
cd C:\RichPanel_GIT
python scripts\dev_e2e_smoke.py --env dev --region us-east-2 --stack-name RichpanelMiddleware-dev --wait-seconds 180 --profile rp-admin-kevin --scenario allowlist_blocked --create-ticket --ticket-from-email <redacted> --require-allowlist-blocked --run-id B61-SANDBOX-ALLOWLIST-BLOCKED-20260127-1935Z --proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\order_status_allowlist_blocked_proof.json --create-ticket-proof-path REHYDRATION_PACK\RUNS\B61\B\PROOF\created_ticket_allowlist_blocked.json
```

**If allowlist is not configured:** the script emits a `SKIP` proof with `classification_reason=allowlist_not_configured`.

**Proof fields to verify:**
- `allowlist_blocked_tag_present` is true
- `send_message_tag_absent` is true
- `routed_to_support` is true

## Proof artifacts
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/created_ticket_not_order_status.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/not_order_status_proof.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/created_ticket_no_match.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/order_status_no_match_proof.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/created_ticket_allowlist_blocked.json`
- `REHYDRATION_PACK/RUNS/B61/B/PROOF/order_status_allowlist_blocked_proof.json`
