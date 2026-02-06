# Order Status Definition of Done (Feb 10, 2026)

**Purpose:** This is the concrete “done = deployable” checklist for the **Order Status automation**.

**Last updated:** 2026-01-21 (1:00pm Central)

## The critical OpenAI fact (do not miss this)
Order Status automation uses **OpenAI in two distinct places**:

1) **Ticket intent detection (classification)**
   - Code: `backend/src/richpanel_middleware/automation/llm_routing.py`
   - What it does: classifies the customer message into an intent (including the order-status intents).

2) **Customer reply crafting (unique message)**
   - Code: `backend/src/richpanel_middleware/automation/llm_reply_rewriter.py` (invoked from `backend/src/richpanel_middleware/automation/pipeline.py`)
   - What it does: rewrites the deterministic draft order-status reply into a more natural, unique response while preserving the factual content.

If either (1) or (2) is missing or unverified, then **Order Status is not “done” for Feb 10**.

---

## OS-0 Hard gates (apply to every Order Status PR)
Done when **all** are true:

- PR health checks are green:
  - Bugbot: reviewed; findings addressed or explicitly justified
  - Codecov: patch green
  - Claude review: ran with Anthropic API (must show a real request id / usage)
- `python scripts/run_ci_checks.py --ci` exits 0, with a clean git tree.
- Latest run artifacts are placeholder-free.

Evidence required in run artifacts:
- Links/screenshots/snippets showing Bugbot, Codecov, and Claude review results.
- The exact commands executed and PASS output excerpts.

---

## OS-1 Ticket intent detection (OpenAI router)
Done when **all** are true:

- The pipeline performs intent detection using the LLM router (OpenAI) with a deterministic fallback:
  - Code path: `compute_dual_routing(...)` in `llm_routing.py`, consumed by `pipeline.py`.
- Order-status intents are recognized and used for action selection:
  - At minimum: `order_status_tracking`, `shipping_delay_not_shipped`.
- The OpenAI model used for routing is explicitly recorded and **GPT-5.x only**:
  - Runtime model is controlled by `OPENAI_MODEL` (or equivalent config) and defaults are guarded by `scripts/verify_openai_model_defaults.py`.
- Failure behavior is safe:
  - If OpenAI fails/timeouts, or confidence is below threshold, we fall back deterministically (no outbound side effects triggered by a “maybe”).

Evidence required:
- Unit tests proving:
  - Positive: order-status message routes to order-status intent.
  - Negative: non-order-status message does *not* route to order-status intent.
  - Fallback: OpenAI failure/low confidence uses deterministic routing.
- A small eval run (shadow/offline) producing a confusion matrix on labeled examples.
  - Store **PII-safe** eval evidence (hashes + intent + confidence), not raw customer text.

---

## OS-2 Order matching (Richpanel + Shopify read-only)
Done when **all** are true:

- The system can match a Richpanel ticket to a Shopify order using allowed identifiers.
- Shopify access is **read-only** and proven as such (scopes configured in Shopify).
- When real Richpanel is used, it is used in **read-only mode** (process + hard technical blocks).

Evidence required:
- Unit tests for mapping logic.
- A prod shadow validation (read-only) showing successful “ticket → order” matching on real orders, with PII-safe artifacts.
- A dev sandbox E2E run showing webhook ingestion + outbound send-message + ticket state transitions (no Shopify test orders).

---

## OS-3 Tracking lookup and “not shipped yet” detection
Done when **all** are true:

- If tracking exists, we can return:
  - tracking number (if available)
  - tracking URL/link (if available)
  - carrier/service (if available)
- If tracking does not exist (order not shipped), the system chooses the “not shipped yet” path.

Evidence required:
- Unit tests for tracking extraction across payload shapes.
- A prod shadow validation (read-only) showing tracking extraction and “not shipped yet” detection on real orders.
- A dev sandbox E2E run covering message flow + ticket state transitions (no Shopify test orders).

---

## OS-4 Customer reply generation (OpenAI unique message)
Done when **all** are true:

- The system produces a **deterministic draft** that is factually correct (tracking details OR calculated ETA window).
- The system then uses **OpenAI to craft the final user-facing message**:
  - OpenAI rewriter is enabled for the order-status action (feature flag / config), with safe fallback to draft if OpenAI fails.
  - The rewriter input is **PII-safe** (no raw customer name/email, no full ticket bodies, no full order payloads).
  - The rewriter output is validated:
    - contains the required facts
    - contains no forbidden content
    - respects tone policy

Evidence required:
- Unit tests proving the rewriter is invoked when enabled and skipped when disabled.
- An E2E proof run (sandbox Richpanel) that captures:
  - draft reply
  - rewriter enabled
  - OpenAI call occurred (response id / usage captured)
  - final message differs from the draft but preserves facts

---

## OS-5 Ticket lifecycle
Done when **all** are true:

- After the order-status reply is posted, the ticket is resolved/closed.
- If the customer replies after closure:
  - ticket is re-opened and routed to the email support team
  - loop-prevention guard prevents repeated auto-replies

Evidence required:
- Unit tests for loop prevention and follow-up routing.
- Sandbox E2E run demonstrating close + follow-up reroute.

---

## OS-6 Testing model: sandbox writeable + prod read-only shadow
Done when **all** are true:

- Sandbox Richpanel is used for:
  - write/edit/close/re-open
  - outbound messaging to test tickets
  - end-to-end proofs that include side effects
- Shopify sandbox / test orders are **not available** and must not be created.
- Prod Richpanel + prod Shopify are used only for **read-only shadow runs**:
  - no tag writes
  - no messages
  - no resolves
  - no updates
  - no side effects
  - matching + tracking + ETA extraction validated with PII-safe artifacts

Evidence required:
- A “read-only hard block” mechanism exists (code + process) and is proven.
- Shadow proof artifacts show only GET calls were made (or the tool refused to proceed).

---

## OS-7 Secrets + config (must be unambiguous)
Done when **all** are true:

- OpenAI API key is stored in AWS Secrets Manager per environment:
  - `rp-mw/dev/openai/api_key`
  - `rp-mw/staging/openai/api_key`
  - `rp-mw/prod/openai/api_key`
- Shopify Admin API token is stored per environment (read-only scopes):
  - `rp-mw/dev/shopify/admin_api_token`
  - `rp-mw/staging/shopify/admin_api_token`
  - `rp-mw/prod/shopify/admin_api_token`
- Richpanel secrets are stored per environment:
  - sandbox/dev: `rp-mw/dev/richpanel/api_key` and `rp-mw/dev/richpanel/webhook_token`
  - prod: `rp-mw/prod/richpanel/api_key` (and webhook token if used)

Evidence required:
- A docs table mapping **GitHub Actions secrets ↔ AWS Secrets Manager**.
- A “which secret is safe for what” section:
  - sandbox secrets: ok to write (only to sandbox)
  - prod secrets: read-only shadow mode only

---

## OS-8 Observability + rollback
Done when **all** are true:

- We have dashboards/log queries for:
  - intent decisions
  - order match success/fail
  - tracking found vs not found
  - close + follow-up route rates
  - OpenAI call success/failure + latency (no PII)
- We have kill switches:
  - disable OpenAI routing primary (fallback deterministic)
  - disable OpenAI reply rewriting (send deterministic draft)
  - disable outbound entirely

Evidence required:
- Documented runbook entries for “turn off OpenAI routing” and “turn off OpenAI rewrite”.
