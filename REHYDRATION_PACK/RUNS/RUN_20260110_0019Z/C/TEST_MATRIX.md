# Test Matrix

**Run ID:** $runId  
**Agent:** C  
**Date:** 2026-01-10

| Area | Scenario | Test | Result |
|---|---|---|---|
| Outbound | Ticket already resolved/closed/solved | OutboundOrderStatusTests.test_outbound_skips_when_ticket_already_resolved | PASS |
| Outbound | Follow-up after mw-auto-replied | OutboundOrderStatusTests.test_outbound_followup_after_auto_reply_routes_to_email_support | PASS |
| Outbound | Normal enabled path | OutboundOrderStatusTests.test_outbound_executes_when_enabled | PASS |
