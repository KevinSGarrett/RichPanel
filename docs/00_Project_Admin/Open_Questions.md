# Open Questions (Gap List)

Last updated: 2025-12-22
Last verified: 2025-12-22 — Deferred Richpanel tenant/UI verification items per owner instruction; proceeding with safe defaults.

These questions help us close gaps so the project plan is accurate and production-ready.

**Status legend**
- ✅ Closed (answered)
- 🟡 Partially answered / assumed (needs confirmation)
- 🔴 Open

---

**Note:** Some items are marked as “🟡 (verify in tenant)” — these are not questions for you to answer from memory.
They are assigned to Cursor agents to confirm via UI/API, and the plan includes fallbacks so we can proceed regardless.

## A) Product + business goals
1) 🔴 What is the primary success metric?
   - reduce first response time? increase CSAT? reduce cost? reduce backlog?
2) 🔴 What is the acceptable misroute rate in early rollout?
3) 🔴 Do any teams have strict SLAs (e.g., Phone Support must respond within X minutes)?

---

## B) Richpanel inbound trigger contract

**Note (owner decision):** We are **holding off** on Richpanel tenant/UI verification for now.  
Items marked **(Deferred verification)** are *not blocking* planning because the design includes safe fallbacks. We will revisit them before implementation / go-live.

4) 🟡 (Deferred verification) Where can we trigger the middleware from? (Tagging Rules vs Assignment Rules)
   - Plan default: **Automation → HTTP Target**.
   - Assumed fallback (safe): place the trigger in **Assignment Rules** if Tagging Rules cannot call HTTP Targets.

5) 🟡 (Deferred verification) What is the exact payload schema the HTTP Target can send?
   - Plan default: minimal payload: `ticket_id`, `ticket_url`, `event_type`, `sent_at`.
   - Assumed fallback: if templating is limited, send only `ticket_id` and fetch everything else via API.

6) 🟡 Are customer identifiers reliably available (email/phone/order#)?
   - Assumption: identifiers are **not reliably present** in the first message.
   - Plan: extract from message text (when present) + rely on deterministic order linkage when available; otherwise ask for order # / email.

7) 🟡 (Deferred verification) Can HTTP Target include custom headers for webhook authentication?
   - Plan default: `X-Middleware-Token` header.
   - Fallback: token in URL path or request body (plus API Gateway rate limiting).

8) 🟡 (Deferred verification) Can we express “tag NOT present” conditions in automations?
   - Plan default: guard legacy rules with `Tags does not contain mw-routing-applied`.
   - Fallback: disable/avoid “reassign even if already assigned” + route only on first inbound message.

9) 🟡 (Deferred verification) Is order linkage reliable from ticket → order (Shopify integration)?
   - Plan default: use `GET /v1/order/{conversationId}`; if it returns `{}`, treat as non-deterministic (no tracking disclosure).
   - Fallback: Tier 1 (“ask for order #”) + route to Returns Admin.

## C) Order status + tracking access
10) 🟡 Can we retrieve linked order details via Richpanel APIs in your tenant?
   - Evidence: Richpanel’s order schema includes fulfillment tracking number + tracking URL fields.
   - Still need to confirm:
     - are orders linked for most conversations?
     - are tracking fields populated from Shopify in practice?
11) 🔴 Do we have (or can we create) Shopify Admin API access for fallback order lookup?
12) 🟡 Identifier reliability:
   - structured “Order Number” field appears rarely in SC_Data,
   - first customer messages contain order numbers ~10% of the time (rough estimate),
   - so we must confirm extraction + “ask for order #” fallback is acceptable.

---

## D) Automation policy confirmations
13) ✅ Tracking link + tracking number may be included in auto-replies when deterministic match exists.
14) ✅ Delivered-but-not-received default confirmed:
   - send Tier 1 safe assist + route to human (no auto-resolve)
15) ✅ Auto-close policy: middleware must **never auto-close**.
16) ✅ Chargebacks/disputes: route to Chargebacks/Disputes queue (no automation).

---

## E) Data governance + privacy
17) ✅ SC_Data package is provided to help planning; we will use it only in aggregate + sanitized form.
18) 🟡 What is our policy for PII in logs and LLM prompts?
   - Recommended: redact/mask identifiers; minimize context; keep full transcripts out of logs
19) 🔴 Any compliance requirements (SOC2, GDPR/CCPA, PCI)?

---

## F) Operational constraints
20) ✅ Baseline latency targets defined (Wave 02; can be tightened later).
21) 🟡 Confirm business timezone for reporting (heatmap + SLAs).
   - Assumption: America/New_York (Eastern) based on your “Acknowledgment response” macro referencing EST hours.
22) 🔴 Budget constraints for OpenAI usage?

---

## G) AWS / infrastructure confirmations
23) ✅ Hosting stack selected: AWS Serverless (API Gateway + Lambda + SQS + DynamoDB).
24) ✅ AWS region selected for v1: `us-east-2` (US East — Ohio).
25) ✅ Environment strategy selected: separate AWS accounts for `dev`, `staging`, `prod` under AWS Organizations (Control Tower optional).
26) ✅ Current state: AWS Organizations / Control Tower are **not** set up yet (confirmed).
27) ✅ AWS management account ownership: **You (developer)** will own it (billing + org admin).
28) ✅ Control Tower adoption for v1: **No** (Organizations-only for v1; revisit later).
29) ✅ v1 audit approach decided: **logs-only** (defer DynamoDB audit-actions table).
30) ✅ v1 LiveChat priority handling decided: **single shared queue** (no separate lane in v1).
31) 🔴 Confirm baseline log retention per environment (dev/staging/prod) and any legal/compliance constraints.

---

## F) Security, privacy, compliance
1) 🟡 (Deferred verification) Which webhook auth option is supported by Richpanel HTTP Targets in your tenant?
   - HMAC signature + timestamp (preferred)
   - custom header token (good)
   - URL token fallback (acceptable)
2) 🟡 Confirm OpenAI platform **data controls** settings for your org/project (including whether Zero Data Retention is available/desired).
3) 🔴 Do you have any explicit legal/compliance requirements beyond “reasonable best practices” (e.g., SOC2 target date, retention limits, DPA requirements)?
4) 🔴 Who should have access to prod logs and secrets besides you (roles/names)?
5) 🟡 Confirm whether any customer channels involve regulated content (health/finance) that would raise compliance requirements.

