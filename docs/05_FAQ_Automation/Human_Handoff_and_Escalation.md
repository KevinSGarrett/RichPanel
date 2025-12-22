# Human Handoff and Escalation

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
Define how the middleware behaves when:
- confidence is low
- the issue is high-risk (Tier 0)
- an auto-reply was sent but a human still needs to resolve
- the ticket state might conflict with existing Richpanel automations

## Guiding principles
1) **Fail closed**: when unsure, route to a human.
2) **Do not auto-close**: customers must always have a path to a human.
3) **Make the agent’s job easier**: provide a short machine summary and the classification rationale.
4) **Avoid routing fights**: coordinate with existing Richpanel assignment rules.

---

## When to route (always)
Regardless of confidence, route immediately for:
- chargebacks/disputes
- legal threats
- fraud / identity issues
- harassment / abusive messages
- data deletion requests (if applicable)

These are Tier 0 intents and should not be automated in v1.

---

## When to auto-reply + route
For most Tier 1/Tier 2 templates in v1:
- Send the approved template (if allowed by gating), AND
- Route to the appropriate team.

Why route even after auto-reply?
- Early rollout needs human oversight.
- Some customers will respond with “that’s wrong” or follow-up questions.

Future (post-stabilization):
- Consider “deflection mode” (auto-reply only, no routing) for very high-confidence Tier 2 order status replies.

---

## Confidence thresholds (recommended defaults)
These are starting points; calibrate with offline eval + shadow mode.

- Tier 2 verified templates:
  - require deterministic match
  - require confidence ≥ 0.85
- Tier 1 intake templates:
  - allow confidence ≥ 0.70  
  (because the template only asks for info and does not disclose anything sensitive)
- Below Tier 1 threshold:
  - route only (no auto message), unless the channel requires an immediate ack

---

## What information to pass to agents (agent summary block)
When routing, attach (as internal note, or metadata logged) a summary:

- Detected intents (canonical)
- Confidence score(s)
- Selected team + tags
- Whether an auto-reply was sent (template_id)
- If order lookup was attempted:
  - linked order found? yes/no
  - any API error codes (redacted)

Example internal note:
```text
MW Router:
- intent: order_status_tracking (0.92)
- action: auto-replied (t_order_status_verified), routed to Email Support Team
- order_linked: yes (order_id: 12345)
- tags: mw-intent-order-status, mw-auto-sent, mw-order-status-auto-v1
```

---

## Escalation triggers (heuristics)
Even if the LLM intent is benign, escalate when:
- customer mentions chargeback/dispute
- “sue”, “lawyer”, “attorney”, “legal”
- “fraud”, “stolen card”, “identity”
- threats or harassment
- high-profile customer (if you later add VIP tagging)

Escalation = Tier 0 route, no auto reply in v1.

---

## Coordination with Richpanel automations
Your tenant currently has assignment rules that auto-assign by channel (example: messenger → LiveChat Support).

To avoid conflicts:
- Middleware should prefer **tag-based routing** that triggers assignment rules, rather than directly overwriting assignee repeatedly.
- Maintain a small allowlist of “middleware routing tags” and keep assignment rule ordering stable.

Common issue to avoid:
- “ticket state conflicts” (assignment bouncing between teams).

---

## “Route to human” is the default answer for Wave 05
Whenever we are not 100% sure:
- route to a human
- send an intake template if it helps gather information safely

This is the safest path to production-grade reliability.
