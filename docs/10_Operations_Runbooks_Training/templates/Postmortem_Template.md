# Postmortem template

Last updated: 2025-12-22

Use this template for SEV-0/SEV-1 incidents and repeated SEV-2 incidents.

---

## Incident summary
- **Incident ID:**  
- **Severity:** SEV-0 / SEV-1 / SEV-2
- **Start time:**  
- **End time:**  
- **Duration:**  
- **Detected by:** alert / customer report / support ops / other
- **Customer impact:**  
- **Systems impacted:** ingress / queue / worker / vendor / templates

## Timeline (UTC)
> Keep this factual and timestamped.
- <time> — <event>
- <time> — <event>

## Root cause
- **Primary root cause:**  
- **Contributing factors:**  
- **Why it wasn’t caught earlier:**  

## What worked
- <bullet list>

## What didn’t work
- <bullet list>

## Customer harm analysis
- Did customers receive incorrect replies?  
- Any possible PII exposure?  
- Chargeback/dispute impact?  
- Refund/returns impact?

## Mitigations applied
- safe_mode: true/false (timestamps)
- automation_enabled: true/false (timestamps)
- concurrency changes (what/when)
- vendor retry/backoff changes
- rollbacks or hotfixes

## Detection improvements
- which signal should have alerted sooner?
- which dashboard/query helped?
- new alert thresholds needed?

## Prevention and remediation tasks
> Create 1–3 high-leverage tasks. Assign owners and deadlines.

| Task | Owner | Priority | Due date | Status |
|---|---|---:|---:|---|
|  |  |  |  |  |

## Follow-up approvals
- Support Ops reviewed: yes/no  
- Engineering reviewed: yes/no  
- Leadership reviewed (if needed): yes/no

## Links
- incident comms thread
- dashboards
- logs query links
- related PRs/releases
