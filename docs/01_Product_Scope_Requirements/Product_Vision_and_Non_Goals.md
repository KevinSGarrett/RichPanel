# Product Vision and Non-Goals

Last updated: 2025-12-21
Last verified: 2025-12-21 — Minor wording alignment (team/queue routing).

## Vision
Build a **production-grade middleware** that sits between **Richpanel** and your internal support org to:

1) **Route inbound customer messages to the right team** (Sales, Technical Support, Returns, etc.) with a measurable confidence score.
2) **Automate the highest-volume FAQs** (starting with order status/tracking) in a safe, conservative way.
3) Reduce agent workload and reduce “back-and-forth” by extracting key entities and providing structured summaries/handoffs.

## Why this exists
- Manual triage is slow and inconsistent.
- High-volume repetitive questions (especially order status) consume a large fraction of support capacity.
- Misroutes create delays, duplicate handling, and poor customer experience.

## Target outcomes (draft)
(We will finalize the numbers in Wave 01.)

- **Routing accuracy:** ≥ 90% correct destination (team/queue) on validated sample
- **Automation resolution rate:** 10–25% of inbound volume auto-resolved (starting with order status)
- **Latency:** route decision within 30–60 seconds of inbound message (excluding downstream API downtime)
- **Quality:** prevent privacy leaks and minimize wrong/unsafe replies (must be close to zero)

## Primary users
- **Customers:** get faster answers for common questions.
- **Support agents:** fewer misrouted tickets; better context and structured intake.
- **Support ops/leadership:** visibility into volumes, automation coverage, and failure modes.

## Non-goals (explicit)
These are intentionally out-of-scope unless you approve a scope change:

1) **Replacing Richpanel** (we integrate; we do not rebuild ticketing).
2) **Building a full OMS/ERP layer** (Shopify remains source-of-truth for orders).
3) **Automating high-risk actions by default** (e.g., issuing refunds, chargeback handling, changing shipping addresses) without explicit policy + verification.
4) **“AGI customer support agent”** — we will not allow the LLM to take arbitrary actions; all actions must be allowlisted and policy-gated.
5) **Perfect accuracy on day one** — we will design for iterative improvement with evaluation + drift monitoring.

## Guiding principles (best-practice defaults)
- **Safety first:** conservative automation; ask for info rather than guessing.
- **Deterministic contracts:** versioned payload schema, structured LLM outputs, idempotent actions.
- **Observability by design:** every automated decision must be traceable and measurable.
- **Incremental rollout:** start with routing + 1–2 FAQs; expand only after metrics prove safety and value.

## Scope boundaries (v0.1)
### In scope
- Intent classification + entity extraction
- Confidence scoring + thresholds
- Team routing + tagging
- Order status/tracking automation (with identity checks)
- Error handling, retries, and safe fallbacks
- Logging/metrics/tracing plan (production-grade)

### Out of scope (for now)
- Multi-language expansions (unless needed)
- Voice/phone automation (routing only)
- Automated refunds/returns processing in Shopify (later phase only)
