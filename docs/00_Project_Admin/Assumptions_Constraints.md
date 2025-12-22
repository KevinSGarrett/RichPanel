# Assumptions & Constraints

Last updated: 2025-12-22
Last verified: 2025-12-22 — Updated assumptions for Richpanel automation ordering + minimal webhook payload strategy.

This file tracks assumptions we are making **until confirmed**.
Each assumption should be either validated, revised, or moved into a Decision Log entry.

---

## A) Current assumptions (not yet fully confirmed)

### A1) Integration & events
1) Richpanel will trigger our middleware via an Automation **HTTP Target** (plan default).
   - Still to confirm: exact UI capabilities in your tenant (headers + templating variables).
2) Middleware can update conversations (tags, replies) via Richpanel APIs using API key auth.
3) Inbound events include enough identifiers to support strong idempotency.
   - If message_id is missing, we will use a deterministic hash fallback until confirmed.
4) Many conversations will not have order numbers or tracking numbers in the first message; we must rely on order linkage or ask for order number safely.
5) Automation ordering is controllable (drag/drop priority) so we can ensure the middleware trigger rule runs before any “skip subsequent rules” rules.
   - If not controllable, we may need to embed HTTP Target actions into channel rules instead.

### A2) Order lookup sources
6) Richpanel Order APIs can retrieve the order linked to a conversation.
   - Evidence: Richpanel order schema examples include tracking number + tracking URL fields.
   - Still to confirm: whether these fields are populated consistently in your Shopify integration.
7) Shopify Admin API will be used as fallback only if required (pending access confirmation).

### A3) Latency classes
8) LiveChat is the only “real-time” channel for v1; all other channels are treated as async.
   - We can promote additional channels later if needed.

### A4) Reporting timezone
9) Business reporting timezone is Eastern (America/New_York) unless confirmed otherwise.
   - Rationale: existing acknowledgement messaging references EST business hours.

### A5) Response generation approach
10) Customer-facing replies for v1 will be **template-based** whenever possible (LLM used for classification/decisioning).
   - This reduces cost and reduces risk of hallucinated claims.

---

## B) Hard constraints (confirmed)
- Middleware must be production-grade: security, observability, reliability, and testing are first-class.
- Middleware must **never auto-close** tickets.
- Chargebacks/disputes route to **Chargebacks / Disputes** Team/queue (Tier 0; no automation).
- Shipping exceptions (missing/incorrect/lost/damaged/delivered-not-received) route to **Returns Admin**.
- Hosting stack (default): **AWS Serverless** (API Gateway + Lambda + SQS FIFO + DynamoDB).
- Baseline latency targets for early rollout are set (can be tightened later).
- Documentation must stay navigable and modular (`docs/INDEX.md` + `docs/CODEMAP.md` maintained).
- Workflow roles:
  - ChatGPT = PM (this plan)
  - Cursor agents = builders
  - Must align work packs with `Policies.zip`.

---

## C) Items to confirm in Wave 03 / Wave 05
- Exact HTTP Target payload schema and trigger details (events, variables, message id availability).
- Whether automation conditions support “Tags does not contain …”.
- Identifier reliability in tenant APIs (email/phone/customer_id/order linkage).
- Whether Richpanel Order APIs in your tenant include tracking number/link (populated from Shopify).
- Shopify Admin API access and required scopes (only if fallback needed).

---

## AWS / infrastructure
- AWS region (v1): `us-east-2` (US East — Ohio).
- Environment strategy: separate AWS accounts for `dev`, `staging`, `prod` under AWS Organizations (Control Tower optional). **Current state:** no Organizations/Control Tower yet.

## Cloud foundation
- AWS Organization management account owner: **You (developer)** (confirmed).
- Control Tower: deferred for v1 (Organizations-only).
