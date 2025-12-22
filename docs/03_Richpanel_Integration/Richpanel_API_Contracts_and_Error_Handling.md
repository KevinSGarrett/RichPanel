# Richpanel API Contracts and Error Handling

Last updated: 2025-12-22
Last verified: 2025-12-22 — Aligned endpoint paths to Richpanel API Reference ("Conversation" objects use `/v1/tickets/*` paths).

This document lists the Richpanel APIs the middleware is expected to use, plus required error handling behaviors.
We will validate exact request/response schemas against your tenant before implementation.

> **Terminology note:** Richpanel UI/docs often say “Conversation”, but the API paths frequently use `/v1/tickets/...`.
> In this plan we use **conversation_id** conceptually, but treat it as the same thing as **ticket id** in API paths.

---

## 1) Authentication (required)
Richpanel API calls use an API key sent via header:
- `x-richpanel-key: <api_key>`

Key management requirements:
- store the key in **AWS Secrets Manager** (per environment)
- rotate keys periodically
- never log the key

---

## 2) Core read operations (context building)

### 2.1 Retrieve a conversation (ticket)
- `GET /v1/tickets/{id}`

Use cases:
- fetch latest conversation metadata
- confirm existing tags and assignment state
- obtain customer profile fields (email/phone) if needed

### 2.2 Retrieve conversations by customer email/phone (optional)
- `GET /v1/tickets/{type}/{id}` where `{type}` is typically `email` or `phone`

Use cases:
- reconciliation and debugging
- fallback lookups when webhook payload is missing a ticket id (should be rare)

### 2.3 Tags + teams (drift checks + mapping)
- List tags: `GET /v1/tags`
- List teams: `GET /v1/teams`

Use cases:
- name → id mapping cache (if API requires ids)
- nightly drift detection (rename/deletion)

---

## 3) Orders (Shopify integration via Richpanel)

### 3.1 Retrieve order linkage for a conversation
- `GET /v1/order/{conversationId}`

Expected behavior:
- if an order is linked, the response returns `orderId` and `appClientId`
- if no order is linked, an **empty object** `{}` is returned

This is a critical gating signal for the **order status automation**:
- if `{}` → do not attempt to auto-answer order status with tracking details

### 3.2 Retrieve the full order object
- `GET /v1/order/{appclient_id}/{order_id}`

Expected fields (examples exist in Richpanel docs):
- `fulfillmentStatus`
- `fulfillment[].tracking[].trackingNumber`
- `fulfillment[].tracking[].trackingUrl`
- `statusUrl` (customer-facing “order status” link)

We will use these fields **only when deterministic match exists**, and we will never invent tracking details.

### 3.3 (Optional) Attach an order to a conversation
- `PUT /v1/tickets/{id}/attach-order/{appClientId}/{orderId}`

Use cases:
- if you later want the middleware to link a Shopify order to a conversation (typically only after verifying order identity)

---

## 4) Core write operations (side effects)

### 4.1 Add / remove tags
- Add tags: `PUT /v1/tickets/{id}/add-tags`
- Remove tags: `PUT /v1/tickets/{id}/remove-tags`

Notes:
- Some tenants expect **tag IDs** (UUIDs) rather than tag names. Middleware must maintain a cache.

### 4.2 Update a conversation / post a reply
- `PUT /v1/tickets/{id}`

Use cases:
- add an agent/bot comment (auto-reply)
- update fields/state where supported

> The exact payload shape for posting comments must be confirmed in staging, because vendors often have strict schemas.

---

## 5) Error handling (non-negotiable)

### 5.1 Retries and backoff
- Retry on transient errors (network, 5xx, timeouts)
- Exponential backoff with jitter
- Cap retries and send to DLQ after threshold

### 5.2 Rate limits (429)
- Respect `Retry-After` if present
- Backoff aggressively for bursty conditions
- Prefer smoothing via queue worker concurrency

### 5.3 Idempotency
All outbound actions must be idempotent or guarded by idempotency keys, especially:
- posting replies
- adding/removing routing tags
- attaching orders

### 5.4 Partial failure strategy
If we can’t complete full automation (e.g., order lookup fails):
- still do routing + tags if possible
- avoid auto-replies that could be wrong
- record a structured log + (optional) internal note for agents

---

## 6) Validation tasks (Wave 03 → Wave 05)
- Confirm exact comment/post-reply schema for `PUT /v1/tickets/{id}`
- Confirm whether tags endpoints accept IDs, names, or both
- Confirm order linkage coverage and tracking field population for Shopify-integrated orders
- Confirm whether we can identify *customer vs agent* message authors from the webhook payload (preferred) or only via `GET /v1/tickets/{id}`

---

## Sources (for engineers)
- Richpanel API Reference — Authentication
- Richpanel API Reference — Retrieve a Conversation (`GET /v1/tickets/{id}`)
- Richpanel API Reference — Update a Conversation (`PUT /v1/tickets/{id}`)
- Richpanel API Reference — Add Tags (`PUT /v1/tickets/{id}/add-tags`)
- Richpanel API Reference — Remove Tags (`PUT /v1/tickets/{id}/remove-tags`)
- Richpanel API Reference — Attach Order (`PUT /v1/tickets/{id}/attach-order/{appClientId}/{orderId}`)
- Richpanel API Reference — Retrieve an Order Linked to a Conversation (`GET /v1/order/{conversationId}`)
- Richpanel API Reference — Retrieve an Order (`GET /v1/order/{appclient_id}/{order_id}`)
- Richpanel Guides — Order Event Structure (examples for `statusUrl`, `fulfillment[].tracking[]`)
