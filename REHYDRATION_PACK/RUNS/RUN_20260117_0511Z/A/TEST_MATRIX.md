## Test Matrix
| Scenario                          | Ticket | Status change | Success tag added | Skip/escalation tags | Follow-up reply sent | Routed to support | Result      |
|-----------------------------------|--------|---------------|-------------------|----------------------|----------------------|-------------------|-------------|
| order_status_no_tracking + FU     | 0d21ae129a64   | OPEN→CLOSED   | Yes               | No                   | No                   | No                | PASS_STRONG |

Notes:
- Evidence captured in `e2e_outbound_proof.json` (PII-safe).
- Follow-up executed; no duplicate reply observed.
- Route-to-support tag not added; no skip/escalation tags present.
- Success tags present: `mw-auto-replied`, `mw-order-status-answered`, run-scoped tag.
- Status closed via auto-close after middleware reply.
