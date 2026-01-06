# Integration Test Plan

Last updated: 2025-12-22  
Scope: Wave 09 (Testing/QA/Release readiness).

This plan defines the **integration tests** that validate the middleware behavior across components:
- ingress webhook → queue → worker
- decision pipeline (LLM + policy gates)
- action layer (tag/route + optional auto-reply templates)
- idempotency + de-dup protections
- safe-mode/kill-switch behavior

Integration tests are designed to run **without a live Richpanel tenant** by using stubs/mocks.
When a staging Richpanel tenant is available, we also define a minimal “E2E smoke” subset.

---

## Integration test setup

### Recommended approach (v1)
- A stub server for:
  - Richpanel API endpoints used by middleware (tickets/tags/orders)
  - Shopify endpoints (optional)
  - OpenAI Responses API (or a deterministic fake)
- Queue can be:
  - real SQS in dev account, or
  - local queue abstraction for tests

### Why stubs (not live vendors)?
Because:
- vendor rate limits make tests flaky
- we must avoid sending accidental customer replies
- we need deterministic control over 429/500 behavior

---

## Integration test categories

## A) Ingress contract + ACK-fast

**IT-A1 — Valid minimal payload accepted**
- Input: webhook payload with `ticket_id`, `event_type`, `sent_at`
- Expect:
  - 2xx response within ACK SLO
  - message enqueued
  - no synchronous vendor calls

**IT-A2 — Invalid payload rejected**
- Input: missing `ticket_id`
- Expect:
  - 4xx response
  - no enqueue
  - security log event emitted (PII-safe)

**IT-A3 — Duplicate inbound event**
- Send same payload twice with same idempotency key
- Expect:
  - only one worker execution results in action planning
  - second is a no-op (idempotency)

---

## B) Routing correctness (route-only)

**IT-B1 — Route to each department**
For each department in:
- Sales Team
- Backend Team
- Technical Support Team
- Phone Support Team
- TikTok Support
- Returns Admin
- LiveChat Support
- Leadership Team
- Social Media Team
- Email Support Team

Use stubbed model outputs that choose intents mapped to each destination.
Expect:
- routing tag applied
- assignment behavior matches plan (tag-first; assignment optional)

**IT-B2 — Unknown/low-confidence routes to fallback**
- Model outputs `confidence < threshold`
- Expect:
  - route to fallback team (e.g., Email Support) or “Needs Review” tag (per routing spec)
  - no auto-reply

---

## C) Tier 0 safety (never automate)

**IT-C1 — Chargeback/dispute**
- Model outputs chargeback intent with high confidence
- Expect:
  - route to Chargebacks/Disputes team/queue
  - no auto-reply template applied
  - optional neutral acknowledgement is allowed only if explicitly enabled (default: off)

**IT-C2 — Policy engine overrides unsafe model**
- Model outputs: suggests an auto-reply or Tier 2 action for Tier 0
- Expect:
  - policy engine forces route-only (Tier 0)
  - observability event `policy_override` emitted

---

## D) Tier 1 safe-assist templates (no private info)

**IT-D1 — “Ask for order #” when order not deterministically linked**
- Input: order status-like message without order link
- Expect:
  - Tier 1 template selected: `ask_order_number`
  - includes only safe fields
  - does not disclose tracking or address

**IT-D2 — Delivered-but-not-received**
- Expect:
  - Tier 1 safe-assist template
  - routing to Returns Admin (claims)
  - no promises of refund/reship

---

## E) Tier 2 verified automation (deterministic match required)

**IT-E1 — Order linked, tracking present**
- Richpanel stub returns linked order with tracking url/number
- Expect:
  - Tier 2 verifier approves
  - Tier 2 template used (order status + tracking)
  - no address disclosure
  - automation de-dup prevents repeated replies for same ticket within window

**IT-E2 — Order linked, tracking missing**
- Expect:
  - template chooses “status without tracking” variant
  - still safe, no address disclosure

**IT-E3 — Order not linked**
- Richpanel order endpoint returns `{}` for ticket
- Expect:
  - Tier 1 ask-for-order# template
  - no Tier 2 automation

---

## F) Rate limits + retries

**IT-F1 — Richpanel 429 with Retry-After**
- Stub returns 429 once, then 200
- Expect:
  - worker backs off and retries
  - no duplicate customer replies
  - retry count bounded

**IT-F2 — OpenAI timeout**
- Stub times out
- Expect:
  - fail-closed route-only fallback
  - error logged (redacted)

---

## G) Loop prevention

**IT-G1 — Middleware’s own reply must not re-trigger**
- Simulate: after middleware posts reply, Richpanel emits outbound message event
- Expect:
  - inbound trigger rule ignores messages created by automation (by tag/metadata)
  - no repeated calls

---

## H) Attachments + non-text

**IT-H1 — Non-text only message**
- Expect:
  - route to human queue (e.g., Email Support or Returns Admin depending on context)
  - no OCR by default
  - attachment fetch is bounded and safe (no base64 inline)

---

## Minimal E2E smoke (optional, staging)
When you have a safe staging Richpanel setup:
- Create a test ticket
- Send a test customer message
- Confirm:
  - tag applied within SLO
  - safe-mode disables automation
  - enabling automation sends exactly one reply

---

## Exit criteria (Wave 09)
Wave 09 considers integration testing “ready” when:
- IT-A through IT-G can be executed with stubs
- a minimal smoke checklist exists for staging
- failures produce actionable logs/metrics (Wave 08 alignment)
