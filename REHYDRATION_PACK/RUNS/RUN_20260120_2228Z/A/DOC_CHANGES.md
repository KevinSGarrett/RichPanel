# Doc Changes Summary — RUN_20260120_2228Z Agent A

**Run ID:** RUN_20260120_2228Z  
**Agent:** A  
**Branch:** b48-order-status-docs-openai-contract  
**Date:** 2026-01-20

---

## What Changed

This run created **2 new documentation files** and **updated 1 existing file** to codify the Order Status + OpenAI integration contract.

---

## New Documents

### 1. Order_Status_OpenAI_Contract.md

**Path:** `docs/08_Engineering/Order_Status_OpenAI_Contract.md`

**Purpose:** Make the Order Status + OpenAI design impossible to "forget" by documenting:

- Where OpenAI is used (intent classification + unique reply generation)
- How it is configured (model env vars / secrets)
- How it is validated (eval harness + smoke proof mode)

**Key Sections:**

1. **Flow Diagram** (text-based)
   - Shows full pipeline: inbound ticket → OpenAI routing → order lookup → deterministic draft → OpenAI rewrite → close ticket → follow-up routing
   - Explicit gates at each OpenAI call point
   - Evidence requirements highlighted

2. **Code Map**
   - `llm_routing.py` — Intent classification
   - `llm_reply_rewriter.py` — Reply rewriting
   - `pipeline.py` — Orchestration
   - `openai/client.py` — API key loading from Secrets Manager

3. **Configuration Map**
   - All OpenAI-related env vars with defaults:
     - `OPENAI_MODEL` (default: gpt-5.2-chat-latest)
     - `OPENAI_ROUTING_PRIMARY` (default: false)
     - `OPENAI_REPLY_REWRITE_ENABLED` (default: false)
     - `OPENAI_ROUTING_CONFIDENCE_THRESHOLD` (default: 0.85)
     - `OPENAI_REPLY_REWRITE_CONFIDENCE_THRESHOLD` (default: 0.7)
   - AWS secret paths:
     - `rp-mw/<env>/openai/api_key` (dev/staging/prod)

4. **PII Policy**
   - Routing: may include customer text (first 2000 chars), prompt forbids PII in response
   - Rewrite: uses deterministic draft (PII-minimized), scans for suspicious content
   - Shadow mode: OpenAI calls permitted but NO replies sent

5. **Proof Requirements**
   - Routing evidence: `llm_called=true`, `response_id`, `model`, `confidence`, `final_intent`
   - Rewrite evidence: `rewrite_attempted=true`, `rewrite_applied=true` (or fallback_used + error_class)
   - Fail case: proof is NOT acceptable if OpenAI was not called (unless intentionally disabled)

6. **Operational Runbooks**
   - Cost management (estimates: $0.025-0.045 per resolution)
   - Rate limiting (429 handling with exponential backoff)
   - Incident response (outage, PII leak, cost spike scenarios)
   - Change control (adding new OpenAI calls, changing models, emergency disable)

**Lines:** 780+

**Why:** This is the single source of truth for Order Status + OpenAI integration. It prevents "forgetting" critical design details during development, deployment, and incident response.

---

### 2. PR_Review_Checklist.md

**Path:** `docs/08_Engineering/PR_Review_Checklist.md`

**Purpose:** Codify all PR requirements in one place (risk labels, Claude gate, Bugbot, Codecov, OpenAI evidence).

**Key Sections:**

1. **Required Labels**
   - Exactly one `risk:R0` through `risk:R4` label

2. **Required Reviews**
   - Claude gate (mandatory, auto-applied, response ID + token usage required)
   - Bugbot review (or documented fallback)

3. **Required CI Checks**
   - Unit tests, lint, CI checks, Codecov

4. **Order Status Special Requirements**
   - OpenAI evidence required (routing + rewrite)
   - E2E proof (PASS_STRONG) for both scenarios
   - Follow-up routing verification (optional)

5. **Evidence Artifacts**
   - RUN_REPORT.md, TEST_MATRIX.md, DOCS_IMPACT_MAP.md

6. **Final Checks**
   - All checks green, no placeholders, no PII, run artifacts complete
   - PR title score ≥95, PR body score ≥95 (R0/R1) or ≥97 (R2/R3/R4)

7. **Merge Policy**
   - Merge commit ONLY (no squash, no rebase)

**Lines:** 175+

**Why:** This repo didn't have a PR template, so this checklist fills that gap. It's especially critical for order-status PRs that must show OpenAI evidence.

---

## Modified Documents

### 3. CI_and_Actions_Runbook.md

**Path:** `docs/08_Engineering/CI_and_Actions_Runbook.md`

**Changes:**

- **Section:** "Order Status Proof (canonical requirements)" (lines 475-482)
- **Added:**
  - Explicit statement: "An order_status proof run is NOT acceptable if routing did not call OpenAI (unless intentionally disabled AND documented)"
  - Explicit statement: "An order_status proof run is NOT acceptable if reply rewrite did not call OpenAI (if unique message requirement is in force)"
  - Cross-reference to `docs/08_Engineering/Order_Status_OpenAI_Contract.md`

**Lines Changed:** ~10

**Why:** The runbook already had proof requirements, but the OpenAI evidence requirement was buried in the details. This update makes it impossible to miss.

---

## Generated/Updated Files

### 4. Docs Registry

**Files:**

- `docs/REGISTRY.md` (human-readable index)
- `docs/_generated/doc_registry.json` (machine-readable)
- `docs/_generated/doc_registry.compact.json` (minified)

**Changes:**

- Registry count: 406 → 407 docs
- New entries:
  - `docs/08_Engineering/Order_Status_OpenAI_Contract.md`
  - `docs/08_Engineering/PR_Review_Checklist.md`

**Why:** Keeps the doc registry in sync with the actual docs on disk (enforced by CI checks).

---

## Impact Summary

| Category | Count | Files |
|----------|-------|-------|
| New docs | 2 | Order_Status_OpenAI_Contract.md, PR_Review_Checklist.md |
| Modified docs | 1 | CI_and_Actions_Runbook.md |
| Generated/updated | 3 | REGISTRY.md, doc_registry.json, doc_registry.compact.json |
| **Total** | **6** | |

---

## Why These Changes Matter

1. **Order_Status_OpenAI_Contract.md**
   - **Problem:** OpenAI integration details were scattered across code comments, runbooks, and implicit assumptions
   - **Solution:** Single canonical contract with flow diagram, code map, config map, PII policy, and proof requirements
   - **Outcome:** Impossible to "forget" where/how/why OpenAI is used

2. **PR_Review_Checklist.md**
   - **Problem:** No single place to see all PR requirements (risk labels, Claude gate, Bugbot, Codecov, OpenAI evidence)
   - **Solution:** Comprehensive checklist that covers all gate types
   - **Outcome:** Reduces PR rework loops, ensures evidence is captured

3. **CI_and_Actions_Runbook.md (updated)**
   - **Problem:** OpenAI evidence requirement was implicit ("proof JSON should show...")
   - **Solution:** Explicit statement: proof is NOT acceptable without OpenAI evidence
   - **Outcome:** No ambiguity about what makes a valid proof

---

## Cross-References

- **OpenAI Contract:** `docs/08_Engineering/Order_Status_OpenAI_Contract.md`
- **CI Runbook:** `docs/08_Engineering/CI_and_Actions_Runbook.md` (lines 475-482)
- **PR Checklist:** `docs/08_Engineering/PR_Review_Checklist.md`
- **Registry:** `docs/REGISTRY.md` + `docs/_generated/doc_registry.json`

---

**Run completed:** 2026-01-20 22:28 UTC  
**Agent:** Cursor (Sonnet 4.5)  
**Branch:** b48-order-status-docs-openai-contract
