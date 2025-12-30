# Richpanel agent override and feedback

Last updated: 2025-12-22

This is the “how-to” guide for agents and team leads.

---

## Why feedback matters
The middleware improves over time by learning from:
- explicit agent overrides
- consistent feedback tags/macros
- weekly evaluation runs

We avoid free-form notes as the primary signal because they are hard to aggregate.

---

## Standard feedback tags (v1)

### Routing errors
- `mw:feedback:misroute`  
  “Ticket was routed to the wrong team.”

- `mw:feedback:wrong_intent:<intent>`  
  “Intent label was wrong.” (use the best matching intent)

### Automation issues
- `mw:feedback:bad_reply`  
  “Template used was wrong / misleading.”

- `mw:feedback:should_have_automated`  
  “This ticket was a top FAQ and could be automated.”

- `mw:feedback:should_not_automate`  
  “This should never be automated.”

### Safety/critical
- `mw:feedback:pii_risk`  
  Suspected exposure or too-specific personal info.

- `mw:feedback:chargeback_mishandled`  
  Chargeback/dispute incorrectly treated.

If any safety/critical tag is used, agents should also alert the on-call.

---

## Agent override procedure (recommended)
1. Assign the ticket to the correct team (normal Richpanel reassignment).
2. Apply the relevant feedback tag(s).
3. Leave a short internal note:
   - “Why: customer is requesting refund; not order status.”
4. If safety-related:
   - escalate immediately (SEV-0/1 depending on scale)

---

## What counts as a “good” feedback signal
Good:
- consistent tags used across teams
- specific intent correction
- one-line reason note

Not good:
- only a long paragraph note with no tags
- inconsistent tag spelling / ad-hoc tags
- editing templates on the fly

---

## Where feedback is reviewed
- Weekly: Support Ops + Engineering review top feedback clusters
- Monthly: update taxonomy, thresholds, and templates via governed release process

References:
- [Feedback signals and agent override macros](../../08_Observability_Analytics/Feedback_Signals_and_Agent_Override_Macros.md)
- [Quality monitoring and drift detection](../../08_Observability_Analytics/Quality_Monitoring_and_Drift_Detection.md)
