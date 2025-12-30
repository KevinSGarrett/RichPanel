# Vendor Change Management

Last updated: 2025-12-22

This document defines how we respond to changes or incidents in:
- Richpanel APIs and automation behavior
- Shopify order data and integration behavior
- OpenAI models and platform behavior

---

## Common vendor change scenarios
- API schema changes or endpoint deprecations
- rate limit changes / new quotas
- authentication changes (keys, headers)
- service incidents (latency spikes, downtime)
- pricing changes (cost spikes)

---

## Response playbook (v1)
1) Detect
- alarms for vendor 429/5xx
- latency alerts
- webhook error spikes

2) Mitigate
- enter safe mode (route-only)
- reduce concurrency
- increase backoff and respect Retry-After
- disable high-cost automation templates temporarily

3) Diagnose
- verify whether vendor behavior changed (logs)
- confirm contract assumptions are still true

4) Fix
- patch integration code/config
- update contract tests (Wave 09)
- update documentation and runbooks

5) Prevent recurrence
- add new monitoring
- add new smoke test cases
- document decision in change log

---

## Documentation requirements
Any vendor incident should produce:
- incident summary (Wave 10 postmortem)
- changes made and tests added
- updated risk register entry if appropriate

