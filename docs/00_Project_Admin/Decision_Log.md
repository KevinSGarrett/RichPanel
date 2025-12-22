# Decision Log

Last updated: 2025-12-22
Last verified: 2025-12-22 — Wave 06 complete (Update 3 closeout).

Use this file to record decisions that impact design, scope, or risk.

**Status legend**
- ✅ Decided
- 🟡 Proposed (default in plan unless you override)
- 🔴 Rejected

---

- **2025-12-21** — Initialized documentation plan structure and wave schedule.  
  **Status:** ✅ Decided  
  - Rationale: Required to keep a large plan navigable and prevent drift.
  - Owner: PM

- **2025-12-21** — Adopt a **two-layer routing model**: intent taxonomy → destination queue/team.  
  **Status:** ✅ Decided  
  - Rationale: Prevents team mapping drift and keeps taxonomy stable even if org changes.
  - Owner: PM + Support Ops

- **2025-12-21** — Use a **risk-tiered automation policy** (Tier 0–3).  
  **Status:** ✅ Decided  
  - Rationale: Lets us automate safely without causing privacy or policy failures.
  - Owner: PM + Support Ops

- **2025-12-21** — Tier 2 order-status auto-replies may include **tracking link + tracking number** when there is a deterministic order match.  
  **Status:** ✅ Decided  
  - Source: you confirmed “yes, when deterministic match.”
  - Owner: You + PM

- **2025-12-21** — Middleware should **never auto-close** tickets.  
  **Status:** ✅ Decided  
  - Source: you confirmed “A. never auto close.”
  - Rationale: Auto-close creates risk of missed edge cases and conflicts with existing Richpanel rules.
  - Owner: You + PM

- **2025-12-21** — Chargebacks/disputes must route to a **Chargebacks / Disputes** team/channel/queue (no automation).  
  **Status:** ✅ Decided  
  - Source: you explicitly stated chargebacks/disputes should go to a chargeback/dispute team/channel.
  - Owner: You + PM

- **2025-12-21** — Create a dedicated **Chargebacks / Disputes** queue (Richpanel Team + routing tag + assignment automation).  
  **Status:** ✅ Decided  
  - Source: you confirmed we can create this team if it is the best suggestion.
  - Rationale: High-risk workflow benefits from limited membership, consistent macros, and clear reporting.
  - Alternative: route to Leadership always (higher load; less specialized).
  - Owner: You + Support Ops

- **2025-12-21** — Missing/incorrect items + shipping exceptions are owned by **Returns Admin** (Fulfillment Exceptions / Claims).  
  **Status:** ✅ Decided  
  - Source: you approved using our best-suggestion default routing.
  - Rationale: Requires reship/refund decisions and policy enforcement; best aligned with Returns/Refund authority.
  - Alternative owners:
    - Email Support Team (if Returns Admin is strictly returns-only)
    - Dedicated Shipping/Claims team (future)
  - Owner: You + Support Ops

- **2025-12-21** — Delivered-but-not-received: send Tier 1 safe assist + route to human (no auto-resolve).  
  **Status:** ✅ Decided  
  - Source: you confirmed this is the best suggestion for the early rollout.
  - Rationale: Customers need immediate guidance, but refunds/reships are too risky to automate.
  - Owner: You + Support Ops

- **2025-12-21** — Routing implementation: use **routing tags + Richpanel automations/views** to achieve “team routing”; assign to agents via `assignee_id` only when needed.  
  **Status:** ✅ Decided (plan default; verify in Wave 03)
  - Rationale: Richpanel tickets typically do not expose a direct “team field” via API; tags and assignment rules are the stable control surface.
  - Owner: PM + Engineering


- **2025-12-21** — Order lookup approach: build an “Order Lookup” abstraction; prefer Richpanel order linkage when available; treat Shopify as source-of-truth.  
  **Status:** 🟡 Proposed (recommended default)  
  - Rationale: Richpanel provides order linkage APIs, but Shopify remains the authoritative order system.
  - Owner: Engineering + PM

- **2025-12-21** — Use `SC_Data_ai_ready_package.zip` as evidence for planning (taxonomy, templates, evaluation design).  
  **Status:** ✅ Decided  
  - Source: you clarified you provided it to help create the development plan documentation.
  - Requirements:
    - do not paste raw transcripts into docs
    - treat as sensitive data (PII)
    - use only aggregated stats and sanitized examples
  - Owner: PM
- **2025-12-21** — Hosting decision: use **AWS Serverless** architecture (API Gateway + Lambda + SQS FIFO + DynamoDB).  
  **Status:** ✅ Decided  
  - Source: you have no AWS preference and asked for the best-suggested stack.
  - Rationale: lowest ops burden + scales for webhook workloads + easy to enforce idempotency and backpressure.
  - Notes: ECS/Fargate remains a future option if workloads grow or latency predictability becomes a hard requirement.
  - Owner: You + PM

- **2025-12-21** — Baseline latency targets for early rollout (by channel urgency class).  
  **Status:** ✅ Decided  
  - Source: you asked for the best recommendation for latency by channel.
  - Defaults:
    - Ingress ack p95 < 500ms
    - Real-time channels: routing p95 < 15s; auto-reply p95 < 25s; p99 < 60s
    - Email-like channels: routing p95 < 60s; auto-reply p95 < 120s; degraded p99 < 10min
  - Owner: You + PM

- **2025-12-21** — AWS primary region selection for v1: `us-east-2` (US East — Ohio).  
  **Status:** ✅ Decided  
  - Source: US-wide customer base; you asked us to choose the best region.
  - Rationale: balanced US latency; standard AWS services; simple single-region rollout.
  - Notes: DR region option documented as `us-west-2` (optional later).
  - Owner: You + PM

- **2025-12-21** — AWS environment strategy: separate accounts for `dev`, `staging`, `prod` under AWS Organizations (Control Tower optional).  
  **Status:** ✅ Decided  
  - Source: you asked for the best recommendation and approved it.
  - Rationale: strong isolation boundary for security + blast radius reduction; clearer budgets/permissions.
  - Minimal fallback: 2 accounts (`prod` + `nonprod`) if setup overhead is too high.
  - Owner: You + PM

- **2025-12-21** — AWS management account ownership: **You (developer)** own the AWS Organization management account (billing + org admin).  
  **Status:** ✅ Decided  
  - Source: you confirmed “I will own it.”  
  - Rationale: establishes a single accountable owner for account creation, billing, and break-glass access (reduces operational ambiguity).
  - Notes: We still enforce root MFA + alternate contacts + break-glass documentation to prevent lockout.
  - Owner: You

- **2025-12-21** — AWS Control Tower adoption: **defer** (Organizations-only for v1).  
  **Status:** ✅ Decided  
  - Source: current state is no Control Tower; v1 requires speed + minimal setup overhead.
  - Rationale: Organizations provides the required multi-account isolation; Control Tower can be added later when guardrails automation is worth the complexity.
  - Owner: You + PM

- **2025-12-21** — AWS foundation decision: use **AWS Organizations without Control Tower** for v1 (Control Tower optional later).  
  **Status:** ✅ Decided  
  - Source: you confirmed you do **not** have AWS Organizations / Control Tower set up yet and want the best recommended approach.
  - Rationale: Organizations-only gets us the core benefit (account isolation + consolidated billing) with less overhead/moving parts than a Control Tower landing zone.
  - Notes:
    - Organizations is the required building block; Control Tower can be layered on later if you want automated guardrails + account vending.
    - Detailed checklist lives in `docs/02_System_Architecture/AWS_Organizations_Setup_Plan_No_Control_Tower.md`.
  - Owner: You + PM

- **2025-12-21** — Channel urgency class: treat **LiveChat as the only “real-time” channel** for v1; treat all other channels as asynchronous by default.  
  **Status:** ✅ Decided (revisit if operations require)
  - Source: you believe LiveChat only; you asked for recommended latency strategy.
  - Rationale: aligns SLOs with actual operational needs; avoids unnecessary complexity.
  - Owner: You + PM


- **2025-12-21** — State + idempotency persistence: use **DynamoDB** with TTL-based cleanup (minimal v1 schema).  
  **Status:** ✅ Decided  
  - Rationale: required to prevent duplicate replies/routing and support safe multi-step flows.
  - Reference: `docs/02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md`
  - Owner: You + PM

- **2025-12-21** — Rate limiting strategy (v1): enforce downstream protection via **worker reserved concurrency caps** + token buckets + 429 backoff + DLQ.  
  **Status:** ✅ Decided  
  - Rationale: prevents 429 storms and keeps system stable during spikes.
  - Reference: `docs/07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md`
  - Owner: You + PM

- **2025-12-21** — Initial worker reserved concurrency: start at **5** (tunable).  
  **Status:** 🟡 Proposed  
  - Rationale: conservative default until we measure OpenAI/Richpanel/Shopify quotas and real processing time.
  - Owner: You + PM

- **2025-12-21** — Response generation policy (v1): prefer **template-based replies** (LLM used for classification/decisioning, not freeform replies).  
  **Status:** 🟡 Proposed  
  - Rationale: reduces cost and risk; ensures consistent tone and prevents hallucinated claims.
  - Reference: `docs/07_Reliability_Scaling/Cost_Model.md`
  - Owner: You + PM

- **2025-12-21** — v1 audit trail approach: **logs-only** (skip optional DynamoDB `rp_mw_audit_actions` table in v1).  
  **Status:** ✅ Decided  
  - Rationale: Keep v1 state footprint minimal and reduce PII risk; structured logs + CloudWatch Logs Insights are sufficient for early rollout troubleshooting.  
  - Upgrade path: If durable audit becomes necessary (compliance/process), enable Table C in a later wave.  
  - Owner: PM + Engineering

- **2025-12-21** — v1 queue strategy: **single SQS FIFO queue** (no separate LiveChat “real-time lane” in v1).  
  **Status:** ✅ Decided  
  - Rationale: Current volumes are well within a single FIFO queue’s capability; simpler operational surface for early rollout.  
  - Trigger to revisit: LiveChat routing p95 consistently > 15–25s due to backlog.  
  - Owner: PM + Engineering
- **2025-12-22** — Richpanel API path convention for “conversation” operations: use `/v1/tickets/{id}` (not `/v1/conversations/*`).  
  **Status:** ✅ Decided  
  - Source: Richpanel public API Reference labels the resource as “Conversation” but uses `https://api.richpanel.com/v1/tickets/{id}` for GET/PUT.  
  - Rationale: prevents implementation drift and broken integrations caused by incorrect endpoint paths.  
  - Owner: PM + Engineering

- **2025-12-22** — Middleware inbound trigger placement (v1): prefer **Tagging Rules** (top of list), fallback to **first Assignment Rule**.  
  **Status:** ✅ Decided  
  - Rationale: your existing Assignment Rules frequently enable “Skip all subsequent rules”, which can block later Assignment Rules. Tagging Rules are typically evaluated independently, making the trigger more reliable.  
  - Owner: PM + Support Ops

- **2025-12-22** — HTTP Target payload strategy (v1): start with **minimal payload** (`ticket_id` + `ticket_url`) and fetch message/context via API; add message text to payload only after JSON escaping is verified.  
  **Status:** ✅ Decided  
  - Rationale: avoids lost events caused by invalid JSON templates when message text contains quotes/newlines; provides a safe upgrade path that reduces API calls later.  
  - Owner: PM + Engineering

- **2025-12-22** — Defer Richpanel tenant/UI verification checks (HTTP Target placement, headers support, JSON templating escape behavior, and order-link reliability).  
  **Status:** ✅ Decided  
  - Source: owner requested we hold off and proceed with best-suggested defaults.
  - Rationale: planning can continue safely because the integration design includes robust fallbacks (minimal payload + API reads; token in URL/body if headers unavailable; Assignment Rules trigger fallback; deterministic gating for order status).
  - Reminder: run the verification checklist before implementation / go-live to confirm exact tenant capabilities and simplify the final config steps.
  - Owner: You (AWS/Richpanel admin) + PM + Cursor builders



- **2025-12-22** — Adopt **Structured Outputs** (JSON Schema) for all LLM decisions (`mw_decision_v1`), validated strictly in code (fail closed).  
  **Status:** 🟡 Proposed (default)  
  - Rationale: prevents malformed JSON / missing fields; makes decisions auditable and testable.
  - Artifacts: `docs/04_LLM_Design_Evaluation/schemas/`
  - Owner: PM + Engineering

- **2025-12-22** — Use a **single primary classifier call** (routing + tier + template plan) plus an optional **Tier 2 verifier** call for sensitive automation.  
  **Status:** 🟡 Proposed (default)  
  - Rationale: reduces latency/cost vs multi-step prompting; verifier reduces Tier 2 false positives.
  - Owner: PM + Engineering

- **2025-12-22** — Default model strategy: `gpt-5-mini` (classification-style, reasoning effort none) with optional nano→mini cascade later.  
  **Status:** 🟡 Proposed (default)  
  - Rationale: strong quality for classification with manageable cost/latency; cascade is a later optimization.
  - Owner: PM + Engineering

- **2025-12-22** — v1 taxonomy expanded to include: cancel_order, address_change_order_edit, cancel_subscription, billing_issue, influencer_marketing_inquiry.  
  **Status:** 🟡 Proposed (default)  
  - Rationale: matches Top FAQs and prevents “unknown” overuse.
  - Source of truth: `docs/04_LLM_Design_Evaluation/Intent_Taxonomy_and_Labeling_Guide.md`
  - Owner: PM + Support Ops

- **2025-12-22** — Planning deliverable is **documentation-first**; Cursor usage during planning is **optional** (used only if explicitly requested or for feasibility validation).  
  **Status:** ✅ Decided  
  - Source: you clarified Cursor is intended for build phase; optional use is acceptable only if it increases efficiency.
  - Rationale: Prevents process confusion; keeps plan as source of truth while allowing optional validation artifacts.
  - Artifact location (optional): `reference_artifacts/`
  - Owner: You + PM

- **2025-12-22** — Multi-intent messages follow a deterministic **priority matrix** (Tier 0 overrides; P1>P2>... precedence).  
  **Status:** ✅ Decided  
  - Source: Wave 04 closeout (required for consistent routing + safety).  
  - Rationale: Prevents “easy” intents (order status) from overriding high-risk workflows (chargebacks/legal/fraud).  
  - Document: `docs/04_LLM_Design_Evaluation/Multi_Intent_Priority_Matrix.md`

- **2025-12-22** — Customer-facing automation replies use **template_id only** (no free-form generated copy).  
  **Status:** ✅ Decided  
  - Source: Wave 04 closeout; aligns with “never auto-close” + safety requirements.  
  - Rationale: Enables reviewable, auditable, and consistent messaging; reduces prompt-injection risk.  
  - Document: `docs/04_LLM_Design_Evaluation/Template_ID_Catalog.md` (copy finalized in Wave 05).

- **2025-12-22** — CI enforces **hard regression gates**: schema validity, Tier 0 FN=0, Tier 2/Tier 3 violations=0.  
  **Status:** ✅ Decided  
  - Rationale: Prevents unsafe automation and missed escalations from reaching production.  
  - Document: `docs/08_Testing_Quality/LLM_Regression_Gates_Checklist.md`

- **2025-12-22** — Golden set labeling is governed by a formal SOP (dual labeling + adjudication + versioning).  
  **Status:** ✅ Decided  
  - Rationale: Ensures eval credibility and supports long-term drift control.  
  - Document: `docs/04_LLM_Design_Evaluation/Golden_Set_Labeling_SOP.md`

- **2025-12-22** — Wave 05 templates use **Mustache-style placeholders** (no logic, optional sections supported).  
  **Status:** ✅ Decided  
  - Rationale: Deterministic rendering, easy review, and safe missing-variable behavior.  
  - Document: `docs/05_FAQ_Automation/Template_Rendering_and_Variables.md`

- **2025-12-22** — Middleware template files are the **source of truth**; Richpanel macros are treated as a synced mirror.  
  **Status:** ✅ Decided  
  - Rationale: Prevents copy drift; enables versioning, review, and regression testing.  
  - Document: `docs/05_FAQ_Automation/Macro_Alignment_and_Governance.md`

- **2025-12-22** — v1 automated replies **must not include shipping/billing addresses**, even if available.  
  **Status:** ✅ Decided  
  - Rationale: Reduces privacy risk and “wrong order” harm; aligns with fail-closed posture.  
  - Document: `docs/05_FAQ_Automation/Order_Status_Automation.md`

- **2025-12-22** — Tier 0 acknowledgements (chargeback/legal/fraud/harassment) are **disabled by default** (route-only in early rollout).  
  **Status:** ✅ Decided  
  - Rationale: Avoids unintended legal/financial commitments; keeps escalation workflows clean.  
  - Document: `docs/05_FAQ_Automation/Templates_Library_v1.md`


- **2025-12-22** — Standardize template placeholders on **Mustache** syntax (`{{var}}` and sections).  
  **Status:** ✅ Decided  
  - Rationale: Templates are machine-rendered; a single placeholder format prevents copy/engine drift.
  - Owner: PM

- **2025-12-22** — Introduce `brand_constants_v1.yaml` to centralize brand name, signature, and policy links for templates.  
  **Status:** ✅ Decided  
  - Rationale: Avoids editing 20+ templates when a signature or link changes; reduces drift.
  - Owner: PM + Support Ops

- **2025-12-22** — Create a dedicated Richpanel macro set prefixed `AUTO:` for automation-aligned replies (optional but recommended).  
  **Status:** 🟡 Proposed  
  - Rationale: Improves agent consistency and reduces copy drift. Middleware does not depend on Richpanel macros.
  - Owner: Support Ops

- **2025-12-22** — Sender identity for automated replies should appear as “Support” (not “Bot”), with a stable signature.  
  **Status:** 🟡 Proposed (recommended default)  
  - Rationale: Reduces customer confusion and aligns with existing macro tone; keeps transparency without derailing threads.
  - Owner: Support Ops

- **2025-12-22** — Channel scope for auto-send (v1): enable on LiveChat + Email; route-only on Social/TikTok/Phone until validated.  
  **Status:** 🟡 Proposed (recommended default)  
  - Rationale: Highest ROI channels with lowest public-facing risk; staged rollout reduces incidents.
  - Owner: Support Ops + PM


- **2025-12-22** — Wave 05 defaults: enable FAQ auto-replies on **LiveChat + Email**; keep **Social/TikTok/Phone** route-only in v1.  
  **Status:** ✅ Decided (default; can be overridden)  
  - Rationale: maximizes ROI while limiting higher-risk/public channels until validated.
  - Owner: PM + Support Ops

- **2025-12-22** — Wave 05 defaults: automated replies appear as **Support** (not “Bot”), with email signature `— {{support_signature}}`.  
  **Status:** ✅ Decided (default; can be overridden)  
  - Rationale: reduces customer friction and keeps tone consistent.
  - Owner: PM + Support Ops

- **2025-12-22** — Wave 05 defaults: do **not** prepend “Automated update:” in v1.  
  **Status:** ✅ Decided (default; can be overridden)  
  - Rationale: avoids drawing attention to automation; templates already include a human handoff.
  - Owner: PM

- **2025-12-22** — Wave 05 defaults: policy/help links are **disabled by default** (URLs remain blank) until verified.  
  **Status:** ✅ Decided (default; can be overridden)  
  - Rationale: prevents shipping incorrect links; links can be enabled safely via `brand_constants_v1.yaml`.
  - Owner: PM + Support Ops

- **2025-12-22** — Wave 05 baseline: `support_signature` default is **Customer Support** until brand constants are populated.  
  **Status:** ✅ Decided (implementation-safe default)  
  - Rationale: prevents placeholder leakage while allowing implementation to proceed.
  - Owner: PM


- **2025-12-22** — Wave 06 — Adopt a strict **PII minimization + redaction** policy:
  - no raw message bodies stored by default
  - redact PII before logging
  - do not log OpenAI request/response bodies (metadata only)
  - Tier 2 disclosure only with deterministic match  
  **Status:** ✅ Decided  
  - Rationale: PII leakage and wrong-customer disclosure are the highest-risk failure modes.
  - Owner: PM + Engineering

- **2025-12-22** — Wave 06 — Store all credentials in **AWS Secrets Manager** and rotate quarterly (or immediately on suspicion of exposure).  
  **Status:** ✅ Decided  
  - Rationale: avoids secret sprawl and supports clean environment separation.
  - Owner: Engineering

- **2025-12-22** — Wave 06 — Webhook authentication strategy is **tiered**:
  - preferred: HMAC signature + timestamp (anti-replay)
  - fallback: header token
  - last resort: URL token  
  **Status:** 🟡 Proposed (verify Richpanel HTTP Target capabilities)  
  - Rationale: supports production security even if Richpanel tenant capabilities are limited.
  - Owner: Engineering + Support Ops



---

## 2025-12-22 — Wave 06 (Update 2)

- **2025-12-22** — Wave 06 — Add an operational **kill switch / safe mode**:
  - global `automation_enabled` flag (route-only when off)
  - `safe_mode` flag (forces route-only; reduces concurrency)
  - template-level enable flags  
  **Status:** ✅ Decided  
  - Rationale: the highest-risk failure mode is incorrect or abusive automation; we must be able to stop it quickly without code changes.
  - Default storage: SSM Parameter Store (runtime flags) with short cache TTL.
  - Owner: Engineering

- **2025-12-22** — Wave 06 — Adopt an AWS **security baseline checklist** for v1 production readiness.  
  **Status:** ✅ Decided  
  - Rationale: avoids “tribal knowledge” security setup and prevents common misconfigurations (no MFA, no DLQ alarms, no budgets, etc.).
  - Includes: API throttling, webhook auth, DLQ+alarms, log retention, secrets manager, least privilege roles.
  - Owner: Engineering

- **2025-12-22** — Wave 06 — Prod ingress protection includes:
  - API Gateway throttling (required)
  - AWS WAF rate-based rule (recommended)  
  **Status:** 🟡 Proposed (depends on cost/ops preference)  
  - Rationale: WAF reduces abuse risk; we can defer if throttling + strong auth is sufficient for v1.
  - Owner: Engineering

- **2025-12-22** — Establish a **minimum security monitoring baseline** (alarms + dashboards) for v1.  
  **Status:** ✅ Decided  
  - Rationale: Prevent silent failures, detect abuse/PII risk quickly, and reduce time-to-containment.  
  - Owner: Engineering

- **2025-12-22** — Webhook secrets rotate with **overlap** (accept multiple active tokens; no-downtime rotation).  
  **Status:** ✅ Decided  
  - Rationale: Prevent inbound disruptions during routine rotation and enable emergency rotation during compromise.  
  - Owner: Engineering

- **2025-12-22** — Use a controlled **break-glass role** + monthly IAM access review cadence for prod.  
  **Status:** ✅ Decided  
  - Rationale: Enables fast incident response while limiting routine access and maintaining auditability.  
  - Owner: Engineering + Leadership