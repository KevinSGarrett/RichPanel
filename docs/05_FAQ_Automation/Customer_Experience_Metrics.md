# Customer Experience Metrics for FAQ Automation (v1)

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
We need proof that FAQ automation:
- reduces agent load
- does not harm CSAT
- does not increase reopens or escalations

This document defines the minimum metrics and review cadence for early rollout.

---

## Core metrics (daily)
### 1) Auto-replies sent
- Count by `template_id`
- Count by channel (email/live chat/social)

### 2) Deflection proxy
Because we may still route to humans in early rollout, “deflection” is best measured as:
- % of tickets where the customer does **not** send another message within 24 hours after an auto-reply

### 3) Follow-up / friction rate
- % of auto-replied tickets where customer replies with:
  - “that’s wrong”
  - “still not shipped”
  - “not received”
  - “refund”
- (Agents can optionally tag these as `mw-auto-wrong` for easy counting.)

### 4) Time to first human response (when routed)
- Ensure auto-replies are not masking slow human follow-up.

### 5) Error rate
- Order lookup failures
- Send-message failures
- Rate limit events

---

## Quality metrics (weekly)
### 1) Misroute rate
Sample 100 tickets/week:
- Was the routed team correct?

### 2) Template correctness
Sample 100 auto replies/week:
- Was the template appropriate?
- Did it request the right info?
- Any tone issues?

### 3) Policy violations (must be zero)
- Any case where wrong customer order info was disclosed
- Any case where addresses/payment details were disclosed via automation

If any policy violation occurs:
- pause Tier 2 automation immediately
- perform incident review (see Reliability docs)

---

## Experiment strategy (recommended)
Rollout phases:
1) Shadow mode (no customer replies) — validate classification + routing
2) Tier 1 intake templates only — low risk
3) Tier 2 verified order status — gated and monitored
4) Expand template set cautiously

---

## Dashboard suggestions
If you use CloudWatch + a BI tool:
- Auto replies per hour vs agent capacity (heatmap overlay)
- Top intents by volume and auto coverage
- Error and fallback tag trends
