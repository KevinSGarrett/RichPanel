# Progress & Wave Schedule

Last updated: 2025-12-22  
Last verified: 2025-12-22 — Wave 06 complete (Update 3 closeout)

This is the **single source of truth** for:
- the full end-to-end wave schedule
- what each wave must produce
- what is complete vs in-progress
- risks/concerns and mitigations
- next actions (to avoid drift)

---

## Current status
- **Current wave:** Wave 07 — Reliability / Scaling / Capacity (next)
- **Waves completed:** 00–06 ✅  
- **Key deferred item:** Richpanel tenant verification (HTTP Target capabilities) — tracked in “Deferred backlog”

---

## Full wave schedule (end-to-end)

### Wave 00 — Phase 0: Folder structure, roadmap, rehydration
**Goal:** Create the documentation framework so the plan stays navigable and doesn’t drift.  
**Status:** Complete ✅

### Wave 01 — Discovery & requirements baseline
**Goal:** Convert the project summary into clear requirements, workflows, and success metrics.  
**Status:** Complete ✅  
**Outputs:** vision/non-goals, departments, FAQ scope, SLAs, assumptions + open questions.

### Wave 02 — System architecture & infrastructure decisions
**Goal:** Select hosting architecture and state model; define throughput plan.  
**Status:** Complete ✅  
**Outputs:** serverless AWS stack, region selection (`us-east-2`), multi-account recommendation, idempotency/state schema, capacity/cost framework.

### Wave 03 — Richpanel integration & configuration design
**Goal:** Define webhook/event ingestion, Richpanel API usage, routing mechanics, tags/macros strategy.  
**Status:** Design complete ✅ (tenant verification deferred ⚠️)  
**Outputs:** API contract plan, webhook integration plan, routing tags, drift plan, verification checklist.

### Wave 04 — LLM routing design + confidence scoring + safety
**Goal:** Taxonomy, prompts, structured outputs, gating/policy engine, eval plan + CI regression gates.  
**Status:** Complete ✅  
**Outputs:** schemas, policy gates, template-id interface, eval framework, golden set SOP.

### Wave 05 — FAQ automation design (copy + macros + playbooks)
**Goal:** Approved template library + safe automation playbooks for top FAQs.  
**Status:** Complete ✅  
**Outputs:** template library (YAML+MD), order status automation, FAQ playbooks, macro mapping, channel variants, pre-launch checklist.

### Wave 06 — Security / privacy / compliance hardening
**Goal:** PII handling, retention, secrets management, access controls, audit plan, kill switch.  
**Status:** Complete ✅  
**Outputs:** threat model, controls matrix, incident runbooks, AWS baseline checklist, kill switch spec, monitoring/alarms baseline, webhook rotation runbook, break-glass procedure.

### Wave 07 — Reliability, scaling, capacity & cost
**Goal:** SLOs, failure modes, load/cost planning, retries, DR posture.  
**Status:** Not started ⏳

### Wave 08 — Observability, analytics, evaluation operations
**Goal:** dashboards, alerting, event taxonomy, quality monitoring, drift detection.  
**Status:** Not started ⏳

### Wave 09 — Testing, QA, and release strategy
**Goal:** test plan, staging strategy, rollout phases, kill-switch drills, regression gates.  
**Status:** Not started ⏳

### Wave 10 — Operations and runbooks
**Goal:** on-call, incident response, operational playbooks, release/rollback drills.  
**Status:** Not started ⏳

### Wave 11 — Governance and continuous improvement
**Goal:** model update policy, taxonomy drift process, feedback loop, change management.  
**Status:** Not started ⏳

### Wave 12 — Cursor agent execution packs (build-ready tickets)
**Goal:** Convert plan into build-ready task packs aligned with `Policies.zip`.  
**Status:** Not started ⏳

---

## Wave 06 progress (this wave)

### Completed (Update 1)
- Created Wave 06 core security documentation set (PII, retention, secrets, IAM, threat model, runbooks).

### Completed (Update 2)
- Added **AWS security baseline checklist** (Organizations-only friendly)
- Added **Kill switch / Safe mode** spec (disable automation quickly, route-only)
- Rewrote/cleaned security docs to remove placeholders and align to v1 defaults:
  - webhook auth & request validation
  - network/egress controls
  - incident response runbooks
  - controls matrix

### Remaining to close Wave 06
- Confirm the best webhook auth option supported by the Richpanel tenant:
  - preferred: HMAC w/ timestamp
  - v1 default: static header token
  - fallback: URL token
- Confirm OpenAI org “data controls” posture (store=false and any org-level retention settings)
- Optional: add company-specific compliance requirements (legal review)

---

## Key issues / concerns and how we address them

### 1) Webhook spoofing → unauthorized automation
Mitigation:
- webhook auth (token/HMAC) + request validation
- throttling + WAF rate-based rule in prod
- idempotency + bounded retries
- kill switch to stop automation quickly

### 2) PII leakage (logs / datasets / vendors)
Mitigation:
- redact before logging; metadata-only logs
- minimize data sent to OpenAI
- retention limits + deletion process
- access controls and least privilege

### 3) Wrong order-status disclosures
Mitigation:
- deterministic match gate + Tier 2 verifier
- no address disclosure in v1
- template-driven responses only
- kill switch and template-level disable

### 4) Deferred Richpanel tenant verification
Mitigation:
- plan uses safe fallbacks (minimal payload, token auth, API fetch)
- verification tasks remain tracked; must be completed before go-live

---

## Deferred backlog (must revisit before go-live)
- Confirm where HTTP Targets can be triggered from (Tagging Rules vs Assignment Rules)
- Confirm whether HTTP Targets support custom headers
- Confirm templating safety if including message text in JSON
- Confirm Richpanel order linkage + tracking fields presence in your tenant

---

## Next best actions (Wave 06 Update 3)
1) Draft the **AWS alarm thresholds** and a “minimum dashboards” list (security + abuse + costs).
2) Add an **access review cadence** (who reviews IAM permissions and when).
3) Add a **webhook auth rotation runbook** (token rotation without downtime).
4) Keep tenant verification deferred, but ensure it is scheduled before build/go-live.

