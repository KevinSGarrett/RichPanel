# Rehydration (Project Context + Constraints)

Last updated: 2025-12-23
Last verified: 2025-12-23 — Wave 12 complete (Update 2). Documentation is ready for implementation.

> **Note (structure alignment):** the governance and cursor-pack folders were renumbered to match the wave schedule:
> - `docs/10_Governance_Continuous_Improvement/` → `docs/11_Governance_Continuous_Improvement/`
> - `docs/11_Cursor_Agent_Work_Packages/` → `docs/12_Cursor_Agent_Work_Packages/`
> Stub `MOVED.md` files exist at the old paths.

Use this file to quickly reload all essential context when resuming work.

---

## 0) Current status snapshot
- **Waves completed:** 00–11 ✅
- **Current wave:** None (documentation complete)
- **Next:** Begin implementation/build execution using Wave 12 tickets
- **Deferred tenant verification (required before go-live automation):**
  - Richpanel HTTP Target trigger location (Tagging vs Assignment Rules)
  - HTTP Target custom header support (preferred webhook auth)
  - JSON templating safety for message bodies
  - Shopify-linked order tracking field presence via Richpanel order APIs

### Architecture snapshot (Wave 02/07)
- AWS serverless: API Gateway → Lambda (ingress) → SQS FIFO → Lambda (worker) → DynamoDB
- Region: `us-east-2` (v1)
- Environment strategy: separate AWS accounts for `dev`, `staging`, `prod` under AWS Organizations (Control Tower optional)
  - Confirmed current state: AWS Organizations / Control Tower are **not set up yet**
  - Plan default: set up AWS Organizations (no Control Tower for v1)
- Queue lanes (v1): single SQS FIFO queue (no separate LiveChat lane)

### Routing + automation defaults (Waves 01/04/05)
- Auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception) tickets
- LLM output is advisory; policy engine is authoritative (fail closed)
- Tier 0 (chargebacks/disputes, fraud/legal): **never auto-send**
- Tier 2 (order status/tracking): **only with deterministic match**
- Templates-only automation (no free-form generation for customer replies in v1)
- Shipping exceptions (missing/incorrect/damaged/lost/DNR): Returns Admin owns (v1)
- Delivered-but-not-received: Tier 1 safe-assist + route to human

### Safety levers (Wave 06)
- Kill switch: `automation_enabled=false`
- Safe mode: `safe_mode=true` (route-only)

### Governance (Wave 11)
- Governance program, cadence, change control, versioning rules, and monthly audit checklist are documented.
- Quick start: `docs/11_Governance_Continuous_Improvement/Governance_Quick_Start.md`


## 1) Project summary (north star)
We are creating a **middleware** for **Richpanel** that:
- receives inbound customer messages
- performs a comprehensive scan using **OpenAI models**
- routes each message/conversation to the correct department/team with a **confidence scoring system**
- automates select top FAQs safely (especially **order status**)

This is a **“best-suggested”** design approach:
- prioritize accuracy, safety, reliability, and operational simplicity
- plan explicitly for common failure modes (duplicates, loops, rate limits, prompt injection, PII leakage)

---

## 2) Workflow (how we will build this plan)
- ChatGPT (this thread) = **Project Plan Documentation Manager**
- Cursor agents = builders (they will implement changes using prompts we generate later)
- Each turn:
  1) You attach the current documentation zip(s) + progress files
  2) We update the docs + trackers
  3) We return an updated zip for the next wave

---

## 3) Key inputs provided (attachments)
- `CommonIssues.zip` — list of common issues we must plan to avoid
- `Policies.zip` — rules/policies for ChatGPT PM + Cursor agents
- `RichPanel_Docs_Instructions_Library_001.zip` — Richpanel docs + your current setup snapshot
  - especially `RichPanel_Docs_Phase0/04_SETUP_CONFIGURATION/` (macros, automations, tags)
- `RoughDraft.zip` — more detailed project requirements
- `Agent Activity Heatmap.csv` — hourly message volume over 7 days
- `SC_Data_ai_ready_package.zip` — recent conversation dataset (3,613 conversations)

---

## 4) Decided defaults (as of now)

### 4.1 Infrastructure defaults (Wave 02)
- Hosting stack: AWS Serverless (API Gateway + Lambda + SQS FIFO + DynamoDB)
- AWS region (v1): `us-east-2` (US East — Ohio)
- Environment strategy: separate AWS accounts for `dev`, `staging`, `prod` under AWS Organizations (Control Tower optional)
  - Confirmed current state: AWS Organizations / Control Tower are **not set up yet**
  - Plan default: set up AWS Organizations (no Control Tower for v1)
- LiveChat is treated as the only “real-time” channel for v1; all other channels default to async targets
- Queue lanes (v1): single SQS FIFO queue (no separate LiveChat lane)

### 4.2 Routing + automation defaults (Wave 01)
- Auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception) tickets
- Audit approach (v1): logs-only (no durable audit table)
- Chargebacks/disputes route to dedicated Chargebacks/Disputes team/queue (Tier 0: no automation)
- LLM decisions use **Structured Outputs** (JSON Schema) with `mw_decision_v1` + optional `mw_tier2_verifier_v1` (Tier 2 verifier)
- Templates-only auto replies in early rollout (no free-form generation)
- Missing/incorrect items + shipping exceptions route to Returns Admin
- Delivered-but-not-received: Tier 1 safe-assist message + route to human

### 4.3 Richpanel integration defaults (Wave 03 — design complete; tenant verification deferred)
- Trigger mechanism (plan default): **Automation → HTTP Target**
  - preferred placement: Tagging Rules (top of list) *if available*
  - fallback placement: Assignment Rules (first rule), with “Skip all subsequent rules” = OFF
- Webhook authentication:
  - plan default: static secret header `X-Middleware-Token` (per environment)
  - fallback: long random token in URL path or request body if headers aren’t supported
- Payload minimization (PII + robustness):
  - plan default: send `ticket_id` (+ optional `ticket_url`, `event_type`)
  - middleware fetches message/order details via Richpanel API
- Order-status gating:
  - deterministic match required; use `GET /v1/order/{conversationId}` and treat `{}` as “no linked order”
- Tenant verification tasks (deferred; not blocking):
  - HTTP Target availability in Tagging vs Assignment Rules
  - header support for HTTP Target requests
  - JSON escaping if including message text templates
  - order-link reliability and tracking fields population

### 4.3 Tooling / workflow defaults
- Primary deliverable is the **documentation plan** (this folder).
- Cursor agents are **builders** and are primarily used in the build phase.
- During planning, Cursor usage is **optional** (used only to validate feasibility or when you explicitly request it).
- A non-production Wave 04 offline-eval scaffold exists under `reference_artifacts/` as an optional reference; docs remain the source of truth.

## 5) Departments / destinations (current)
1. Sales Team  
2. Backend Team  
3. Technical Support Team  
4. Phone Support Team  
5. TikTok Support  
6. Returns Admin  
7. LiveChat Support  
8. Leadership Team  
9. SocialMedia Team  
10. Email Support Team  
11. Chargebacks / Disputes (new dedicated queue)

---

## 6) Key confirmed decisions (locked)
### Product / ops decisions
- ✅ **Order status automation** may include tracking number/link **only** when there is a **deterministic match**.
- ✅ Middleware must **auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception)** tickets.
- ✅ Chargebacks/disputes route to a dedicated **Chargebacks / Disputes** team/queue (Tier 0; no automation).
- ✅ Shipping exceptions (missing/incorrect/lost/damaged/delivered-not-received) route to **Returns Admin** (early rollout default).
- ✅ Delivered-but-not-received → **Tier 1 safe assist + route to human** (no auto-resolve).
- ✅ Channel urgency (v1): **LiveChat only** treated as “real-time”; others are async.

### Architecture decisions (Wave 02)
- ✅ Hosting (best-suggested default): **AWS Serverless**
  - API Gateway → Lambda (Ingress) → SQS FIFO → Lambda (Worker) → DynamoDB (+ Secrets Manager)
- ✅ Queue type: **SQS FIFO**, grouped by `conversation_id` for per-conversation ordering.
- ✅ v1 queue lanes: **single queue** (no separate LiveChat lane in v1; optional later)
- ✅ DynamoDB: minimal state + idempotency (TTL-based cleanup)
- ✅ v1 audit trail: **logs-only**
- ✅ Rate limiting + backpressure: concurrency caps + token buckets + 429 backoff + DLQ (v1)
- ✅ Primary AWS region (v1): `us-east-2` (Ohio)
  - optional later DR region: `us-west-2`
- ✅ Environment strategy: separate AWS accounts for `dev` / `staging` / `prod`
  - AWS Organizations **not set up yet**
  - Control Tower deferred for v1 (Organizations-only)
  - AWS Organizations management account owner: **you (developer)**

### Baseline latency targets (early rollout)
- Ack p95 < 500ms
- LiveChat: routing p95 < 15s; verified auto-reply p95 < 25s
- Async channels: routing p95 < 60s; verified auto-reply p95 < 120s

---

## 7) Data-driven insight we will design around (SC_Data)
The recent dataset (3,613 conversations) suggests identifiers are frequently missing from the **first** customer message:
- First customer message contains:
  - order number-like pattern: ~9.5% of conversations
  - phone number-like pattern: ~7.5%
  - email-like pattern: ~3.6%
  - tracking-number-like pattern: <1%

Implication:
- We cannot rely on the initial message text alone for order lookup.
- Prefer Richpanel-linked order; else ask for order number; never disclose sensitive info without deterministic match.

(These are rough regex-based estimates; we’ll refine in Wave 04 eval design.)

---

## 8) PII handling expectations (baseline)
We likely handle:
- phone numbers, emails
- order numbers
- tracking numbers/links

Baseline stance:
- minimize what we store
- redact in logs and prompts whenever possible
- only disclose tracking/order details to the customer when identity match is deterministic

See: `docs/06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md`

---

## 9) High-priority open items (still need confirmation)
These do not block architecture, but they impact integration correctness and automation safety.

### Richpanel integration reality checks
- What HTTP Target payload variables are actually available in your tenant UI?
- Can automation conditions express “Tags does not contain <tag>”?
- Do we get an event/message id in the trigger payload, or only conversation id?
- Confirm we can order automations so the middleware trigger rule runs first.

### Order status readiness
- Confirm Richpanel order linkage coverage in your tenant
- Confirm tracking fields are populated from Shopify for linked orders

### Shopify (fallback) readiness
- Shopify Admin API access method (custom app token/scopes) — currently unknown

### Compliance / retention
- Log retention per environment (dev/staging/prod)
- Any compliance requirements (SOC2/GDPR/CCPA) that affect retention and access controls


### 4.3 FAQ automation + templates (Wave 05)
- Customer-facing copy is defined in:
  - `docs/05_FAQ_Automation/Templates_Library_v1.md`
  - `docs/05_FAQ_Automation/templates/templates_v1.yaml`
- Tier 2 verified order status automation spec:
  - `docs/05_FAQ_Automation/Order_Status_Automation.md`
- Macro alignment approach (avoid drift):
  - `docs/05_FAQ_Automation/Macro_Alignment_and_Governance.md`
- Auto-reply safety safeguards:
  - `docs/05_FAQ_Automation/FAQ_Automation_Dedup_Rate_Limits.md`
