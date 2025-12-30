# User Manual (Internal)

Last verified: 2025-12-29 — Wave F05 (scaffold).

This manual is for internal users (support/ops) interacting with the automation system.

## What users should be able to do (v1)
- Understand whether a ticket was **routed** or **automated**
- See the **reasoning** and confidence (where safe)
- Override automation by:
  - escalation tags
  - reassignments
  - safe mode / kill switch (ops only)
- Find the right runbook when something looks wrong

## Where users work
- Primary interface: Richpanel (tickets, tags, assignments)
- Planned: admin console (later build wave)

## Key concepts
- **Safe mode**: route-only, no automation
- **Kill switch**: disables automation pipeline
- **Tier 0**: never automate; route to humans

## FAQs
- Where do I see automation decisions? (TBD; depends on Richpanel configuration)
- How do I escalate? (TBD; see ops handbook/runbooks)

## Related
- Ops handbook: `docs/10_Operations_Runbooks_Training/Operations_Handbook.md`
- Runbook index: `docs/10_Operations_Runbooks_Training/Runbook_Index.md`
- Security incident response: `docs/06_Security_Privacy_Compliance/Incident_Response_Security_Runbooks.md`
