# Webhooks and Event Handling (Richpanel → Middleware)

Last updated: 2025-12-22
Last verified: 2025-12-22 — Updated to use Richpanel `/v1/tickets/*` endpoints and to include a safer trigger placement strategy (Tagging rules first).

This document defines:
- how Richpanel triggers middleware via **HTTP Targets**
- the recommended event contract + payload strategy
- how we avoid missed events, loops, and duplicate processing

---

## 1) What “inbound event” means in this project
An **inbound event** is triggered when:
- a customer starts a new conversation
- a customer sends a new message in an existing conversation

Inbound events should cause middleware to:
1) ingest + persist/enqueue
2) run routing + (optional) FAQ automation
3) apply tags / assign teams / send a reply only when safe

---

## 2) Delivery model assumptions (critical)
We will treat Richpanel HTTP Targets as **best-effort delivery**:
- do not assume retries
- do not assume ordering
- do not assume exactly-once delivery

Therefore, middleware must implement:
- **ACK-fast** ingress
- idempotency + dedup
- internal retries + DLQ

---

## 3) Triggering middleware from Richpanel (HTTP Target)

### 3.1 Preferred placement: Tagging Rules (to avoid “skip subsequent rules” conflicts)
Your current workspace contains Assignment Rules that commonly enable:
- **Skip all subsequent rules = ON**
- **Reassign even if already assigned = ON**

Those toggles can cause two failure modes:
1) our middleware trigger rule never runs (if it appears below a “skip subsequent” rule)
2) legacy assignment rules override middleware routing (“routing fights”)

**Best-suggested pattern (v1):**
- Create the middleware trigger as a **Tagging Rule** (or whichever automation category supports HTTP Targets + message triggers).
- Place it at the **top of that category’s rule list**.
- Ensure **Skip all subsequent rules = OFF**.

Why this is safer:
- Tagging Rules and Assignment Rules are typically evaluated independently (separate ordered lists). Even if an Assignment Rule stops other Assignment Rules, our Tagging Rule trigger can still fire.

> If your tenant does *not* allow HTTP Target actions inside Tagging Rules, then use the fallback pattern below.

### 3.2 Fallback placement: First Assignment Rule
If HTTP Target is only available in Assignment Rules:
- create `Middleware — Inbound Trigger` as the **first** Assignment Rule
- set **Skip all subsequent rules = OFF**

### 3.3 Worst-case fallback: Duplicate triggers are acceptable
If ordering cannot be reliably controlled:
- add the HTTP Target action to multiple high-volume channel rules (LiveChat / Email / Social / TikTok)
- rely on middleware idempotency to safely ignore duplicates

---

## 4) Required security for inbound requests

### 4.1 Shared-secret header
Richpanel should include a static secret header in the HTTP Target:
- `X-Middleware-Token: <secret>`

Middleware rejects requests missing the header or with the wrong value.

### 4.2 Request logging
Ingress logs must:
- never log secrets
- avoid logging full message bodies in production (store only hashed/censored or sampled)

---

## 5) Webhook payload schema (v1)

### 5.1 Recommended: Minimal payload (most robust)
**Why:** avoids JSON escaping problems and minimizes PII.

Example JSON template:
```json
{
  "ticket_id": "{{ticket.id}}",
  "ticket_url": "{{ticket.url}}",
  "trigger": "customer_message"
}
```

Middleware then fetches needed context via API:
- `GET /v1/tickets/{id}` (conversation/ticket)
- `GET /v1/order/{conversationId}` (order linkage)

### 5.2 Optional optimization: Include latest message text (only if JSON-escaping is confirmed)
If Richpanel’s JSON templating **properly escapes** strings (must be verified with test messages containing quotes/newlines), we can include:
```json
{
  "ticket_id": "{{ticket.id}}",
  "ticket_url": "{{ticket.url}}",
  "message": "{{ticket.lastMessage.text}}",
  "trigger": "customer_message"
}
```

Benefits:
- reduces Richpanel API reads (lower latency + lower rate-limit risk)

Risk:
- if Richpanel does not escape correctly, payloads can become invalid JSON and events may be lost.

> **Plan-default:** start with minimal payload. Upgrade only after the JSON-escaping test passes.

---

## 6) Middleware ingress contract

### 6.1 Endpoint
- `POST /richpanel/inbound`

### 6.2 Response requirements
- return `200 OK` quickly (target: < 300ms p95)
- do not do model calls or Richpanel API calls on the ingress path

### 6.3 Idempotency key
Because webhook payload may not include message_id, we define idempotency in v1 as:
- `idempotency_key = sha256(ticket_id + last_seen_message_hash)`

Where `last_seen_message_hash` can be:
- hash of message text (if included)
- or derived from the ticket API response (preferred)

We also store a short TTL for dedup keys (e.g., 24–72h) to prevent duplicate actions.

---

## 7) Worker processing logic (v1)

### 7.1 Context building
Worker loads:
1) ticket details via `GET /v1/tickets/{id}`
2) order linkage via `GET /v1/order/{conversationId}`
3) (if linked) full order via `GET /v1/order/{appclient_id}/{order_id}`

### 7.2 Routing + automation decisioning
Worker:
- runs classification + confidence
- if FAQ match is confident AND deterministic match exists → send auto-reply + apply tags
- else → apply route tag only

### 7.3 Applying side effects
Middleware should:
- add `mw-processed`
- add exactly one `route-*` tag
- add `mw-routing-applied`
- optionally add `mw-auto-replied`

All side effects must be idempotent.

---

## 8) Reconciliation sweeps (anti-missed-event safety net)
Because delivery is best-effort, we need a safety net job:
- periodically query for open tickets that are missing `mw-processed`
- enqueue them for processing

This requires tenant validation for the best query method:
- if Richpanel supports search by tags/status via API: use that
- otherwise, reconciliation may rely on export/reporting workflows

---

## 9) Validation checklist (Wave 03)
- [ ] Can a Tagging Rule run on “customer sends message” AND trigger an HTTP Target?
- [ ] Custom header support (`X-Middleware-Token`)
- [ ] Minimal payload template works and includes `ticket.id`
- [ ] (Optional) JSON escaping test passes for `ticket.lastMessage.text`
- [ ] Middleware trigger fires even when Assignment Rules have “skip subsequent rules” enabled
