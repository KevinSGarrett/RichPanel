# User Journeys and Workflows

Last updated: 2025-12-21
Last verified: 2025-12-21 — Updated to reflect tag-driven team routing.

This document captures the **core workflows** the middleware must support.

---

## 1) Workflow A — Standard routing (no auto-reply)

**Trigger:** customer message arrives in Richpanel (any channel)

**Happy path**
1) Richpanel triggers middleware on inbound customer message.
2) Middleware:
   - normalizes payload
   - extracts text + context
   - classifies intent(s) + confidence
3) Middleware applies routing rules:
   - channel defaults (e.g., TikTok → TikTok Support)
   - intent overrides (e.g., returns → Returns Admin)
4) Middleware updates Richpanel:
   - adds routing tags (destination intent/team)
   - optional: sets `assignee_id` (agent) when needed/allowed
   - adds `middleware_processed` (or equivalent) flag to prevent loops
   - Richpanel automations/views handle the “team queue” placement based on tags
5) Conversation appears in correct team queue.

**Failure path**
- If LLM fails or confidence is low → route to default team and tag `needs_manual_triage`.

---

## 2) Workflow B — FAQ automation (order status example)

**Trigger:** inbound message is detected as an automatable FAQ.

**Goal:** send a correct automated reply safely, without leaking incorrect information.

**Happy path**
1) Middleware detects intent: `order_status_tracking` with high confidence.
2) Middleware extracts entities:
   - order number (if present)
   - email/phone from Richpanel metadata (if available)
3) Middleware performs deterministic lookup in Shopify (recommended):
   - find matching order(s)
   - compute an “order match confidence”
4) Decision:
   - if match is deterministic and policy allows → auto-send status + tracking link
   - else → ask customer for order number (safe fallback) and route to a human queue

**Key guardrail**
- Do **not** guess which order. If multiple possible matches exist, ask for order #.

---

## 3) Workflow C — Multi-intent / ambiguous messages

Example: “I want to cancel but also my diffuser isn’t working.”

**Approach**
- Extract multiple intents.
- Apply a tie-breaker:
  - route to the team that can best handle the highest-risk/highest-effort intent first
  - tag all intents so agents can see context

If confidence is low across all intents:
- default to Email Support Team (or channel default) + tag `low_confidence`.

---

## 4) Workflow D — Attachments and non-text payloads

Common cases:
- screenshots of app errors
- photos of damaged products
- PDFs or email threads

**Policy**
- If attachment is small and retrievable: fetch and summarize (when safe and within limits).
- If too large or fetch fails: route to human and tag `attachment_unprocessed`.

(Full attachment playbook is in `docs/03_Richpanel_Integration/Attachments_Playbook.md`.)

---

## 5) Workflow E — Middleware and/or dependency outage

Dependencies:
- Richpanel APIs
- Shopify APIs
- OpenAI APIs

**Principle**
- Always ACK inbound triggers quickly.
- Use internal queue/retry.
- If dependency is down:
  - do not auto-send risky replies
  - route to human
  - add internal note explaining automation was skipped due to dependency outage

---

## 6) Summary diagram (high level)

```
Customer -> Richpanel -> (Inbound trigger) -> Middleware
                                |
                                v
                        Normalize + Classify
                                |
               +----------------+----------------+
               |                                 |
               v                                 v
        FAQ automation?                     Routing only?
               |                                 |
     +---------+---------+                       |
     |                   |                       |
     v                   v                       v
Verified + low risk?   Not verified            Assign/tag team
     |                   |
     v                   v
Auto-send reply      Ask for info + route
```
