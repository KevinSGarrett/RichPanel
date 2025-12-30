# On-call and escalation

Last updated: 2025-12-22

This document defines how incidents are triaged, who gets paged, and how escalations happen.

---

## Primary goals
- minimize customer harm
- restore service quickly
- avoid “routing fights” between automations and middleware
- ensure leadership awareness for SEV-0/SEV-1

---

## Suggested on-call model (v1)

Early-stage teams often start with a single owner. This is acceptable if we also document:
- backup contact (secondary)
- escalation to leadership for SEV-0/1
- “do not wait” actions (safe mode / automation off)

### Roles
- **Primary on-call (Engineering):** first responder, applies kill switch, manages incident log
- **Secondary on-call (Engineering):** backup, handles deep investigation, implements hotfix
- **Support Ops lead:** customer messaging coordination, macro/template decisions
- **Leadership escalation:** SEV-0/1 awareness and approval for major comms

---

## Escalation triggers (recommended)

### Escalate to Support Ops lead if:
- customers are receiving incorrect or confusing replies
- sudden spike in “agent override” or “wrong route” feedback tags
- template copy needs rapid adjustment

### Escalate to Engineering secondary if:
- DLQ growth persists after safe mode and tuning steps
- repeated 429s or vendor errors not stabilized within 15 minutes
- suspected bug in deterministic-match gating

### Escalate to Leadership if:
- **SEV-0/1** incident
- possible PII exposure
- chargeback/dispute workflow impacted
- public channel / social escalation likely

---

## Severity classification (operator shortcut)

### SEV-0 (drop everything)
Examples:
- incorrect automation leaking tracking info to wrong person
- automation sends refunds/cancellations (should be disabled in v1)
- prompt injection causes unsafe behavior that escapes gates
Immediate actions:
- `automation_enabled=false`
- `safe_mode=true`
- start [R003](runbooks/R003_Automation_Wrong_Reply_or_PII_Risk.md)

### SEV-1
Examples:
- routing down (no tags applied, backlog growing fast)
- webhook ingress failing broadly
Immediate actions:
- `safe_mode=true` (routing may still work; depends)
- start [R001](runbooks/R001_Webhook_Failures_and_Duplicate_Storms.md) and [R005](runbooks/R005_Backlog_Catchup_and_DLQ.md)

### SEV-2
Examples:
- slow routing, occasional errors, partial channel issues
Start relevant runbook and notify secondary if persistent >30–60 minutes.

### SEV-3
Examples:
- minor template typo, rare edge case misroute
Log as a task; schedule fix via normal release.

---

## Incident communications
Use:
- [Incident comms templates](templates/Incident_Comms_Templates.md)

For SEV-0/1, publish a status update cadence:
- every 15 minutes until stabilized
- then every 30–60 minutes until resolved

---

## Postmortems
- SEV-0/1: required within 2 business days
- repeated SEV-2: required
- SEV-3: optional (task-only)

Template:
- [Postmortem template](templates/Postmortem_Template.md)
