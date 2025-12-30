# FAQ Automation De-duplication and Rate Limits (v1)

Last updated: 2025-12-22  
Status: **Final (Wave 05 closeout)**

## Purpose
Auto-replies introduce new failure modes:
- duplicate webhooks → duplicate replies
- automation loops (our tags trigger more rules)
- rate limits at Richpanel or OpenAI
- customer spam (multiple auto responses in a short time)

This document defines the minimum safeguards for v1.

References:
- Common issue `03-idempotency-duplicate-events.md`
- Common issue `01-automation-loops.md`
- Common issue `05-rate-limits.md`

---

## 1) Idempotency (per inbound event/message)
**Rule:** one customer inbound message → at most one middleware decision → at most one auto-reply.

Implementation approach (planned):
- Compute an idempotency key, e.g.:
  - `conversation_id + inbound_message_id`
- Store key in DynamoDB with TTL (e.g., 7 days).
- If key already exists → **skip** (do not reply again).

---

## 2) Per-ticket auto-reply cooldown
Even if the customer sends multiple messages in a row:
- avoid spamming

Recommended defaults:
- **Max 1 auto-reply per ticket per 10 minutes**
- **Max 3 auto-replies per ticket per 24 hours**

If the limit is exceeded:
- route-only
- add tag `mw-auto-rate-limited`

---

## 3) Per-customer global cooldown (optional but recommended)
To prevent edge cases (customer spamming across channels):
- Max 5 auto-replies per customer per 24 hours

---

## 4) Safe tagging strategy (avoid loops)
Tags are useful for routing, but can also trigger Richpanel rules.

Rules:
- Use a small, namespaced tag set:
  - `mw-*`
- Do not create Richpanel automation rules that trigger on `mw-auto-sent` unless explicitly intended.
- Maintain a “routing tag allowlist” that is safe to apply automatically.

Example safe tags:
- `mw-intent-order-status`
- `mw-intent-missing-items`
- `mw-template-t_order_status_verified`
- `mw-auto-sent`

---

## 5) When NOT to auto-reply
Skip auto-reply if:
- ticket is already closed/solved
- last message is from an agent
- the inbound message is an attachment-only message (no text)
- ticket is marked VIP (future), or customer is in escalation state
- Tier 0 signals are present

---

## 6) Retry policy
- Webhook events: acknowledge fast (HTTP 200) then process asynchronously (queue) to avoid timeout retries.
- Richpanel API calls: bounded retries with jitter (respect rate limits).
- Sending messages: if send fails, do not retry indefinitely (avoid duplicate sends). Prefer:
  - retry 1–2 times
  - then route-only + tag `mw-send-failed`

---

## 7) Observability tags and logs
Recommended standard tags:
- `mw-auto-sent`
- `mw-auto-skipped-duplicate`
- `mw-auto-rate-limited`
- `mw-send-failed`
- `mw-order-lookup-needed`

Logs should include:
- conversation_id
- inbound_message_id
- decision_id
- template_id (if any)
- routing team/tags
- timing and error codes (redacted)

---

## 8) Test scenarios (must-pass before enabling auto-replies)
- Same inbound webhook delivered twice → only one reply sent
- Customer sends 5 quick messages → cooldown triggers, no spam
- Tags applied by middleware do not cause reassignment loops
- Richpanel API rate limits do not cause cascading failures
