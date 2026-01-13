# Next 10 Suggested Items (Repo Sync)

**Last refreshed:** 2026-01-13 (synced from `PM_REHYDRATION_PACK/10_NEXT_10_SUGGESTED_ITEMS.md`)

Keep exactly 10 items; update status (Shipped / In progress / Blocked / Next / Planned) and reorder by priority after every run.

---

## 1) Order-Status E2E: “PASS_STRONG” must include **reply + resolved/closed**
**Why:** We still have PASS based on a success tag. We want the gold-standard: middleware posts a reply **and** the ticket ends **resolved/closed** (or we document why Richpanel API cannot change status and what our alternative invariant is).  
**Owner:** Agent B  
**Status:** Next

**Definition of done (minimum):**
- A dev E2E smoke run proves:
  - order-status intent recognized
  - middleware replies (PII-safe evidence: message count delta / metadata only)
  - ticket status becomes **resolved/closed**
- Proof committed under `REHYDRATION_PACK/RUNS/<RUN_ID>/B/e2e_outbound_proof.json` (PII-safe).

---

## 2) OpenAI client logging: eliminate any **message excerpt** logging (PII risk)
**Why:** `backend/src/integrations/openai/client.py` still logs response excerpts; future prompts may contain PII and we must be safe by construction.  
**Owner:** Agent C  
**Status:** Next

---

## 3) Per-workload OpenAI model config (env vars + defaults) per OpenAI_Model_Plan
**Why:** We need explicit model assignment per workload (routing vs rewrite vs future FAQ) and a single place to control defaults.  
**Owner:** Agent C  
**Status:** Next

---

## 4) Responses API + Structured Outputs migration (Phase 1)
**Why:** Align with the OpenAI_Model_Plan: structured outputs reduce parsing risk and improve auditability.  
**Owner:** Agent C  
**Status:** Planned (after #2/#3)

---

## 5) Make ruff/black/mypy **blocking** again (remove advisory mode)
**Why:** CI is currently tolerant (advisory). We need clean lint debt before we remove `continue-on-error`.  
**Owner:** Agent C (code) + Agent A (docs)  
**Status:** Planned

---

## 6) Make Codecov **required** in branch protection (patch → project)
**Why:** Coverage is collecting reliably; the next step is enforcement via required checks (start with `codecov/patch`).  
**Owner:** Agent A (process/docs)  
**Status:** Planned (after a few more green uploads)

---

## 7) E2E smoke scenarios v2: add “FAQ” stub + negative/guard tests
**Why:** We want the same proof discipline used for order-status to apply to future FAQ automation, plus ensure skip/escalation never counts as PASS.  
**Owner:** Agent B  
**Status:** Planned

---

## 8) Observability: add PII-safe structured logs + metrics for automation outcomes
**Why:** We need fast debugging without leaking bodies: event_id, run_id, ticket_id_fingerprint, outcome reason, network/outbound flags.  
**Owner:** Agent C  
**Status:** Planned

---

## 9) Dev test-ticket lifecycle: stable “test ticket” procedure
**Why:** E2E runs shouldn’t stall on “which ticket id works.” We need a stable way to create/identify/clean a dev ticket.  
**Owner:** Agent B  
**Status:** Planned

---

## 10) Assistant Manager review workflow (AM_REHYDRATION_PACK) becomes routine
**Why:** We want a predictable, high-confidence 95+ review every run.  
**Owner:** Agent A (process)  
**Status:** In progress (pack created in chat; keep refining)
