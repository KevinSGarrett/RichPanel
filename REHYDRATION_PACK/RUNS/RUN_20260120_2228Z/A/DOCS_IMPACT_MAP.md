# Docs Impact Map: B48 Agent A

**Run ID:** RUN_20260120_2228Z  
**Agent:** A  
**Date:** 2026-01-20

---

## Summary

This run created **2 new canonical docs** and **updated 1 existing doc** to codify the Order Status + OpenAI integration contract.

**Total Impact:**

- New: 2 docs
- Modified: 1 doc
- Generated: 3 registries
- Deleted: 0 docs

---

## New Documents

### docs/08_Engineering/Order_Status_OpenAI_Contract.md

**Status:** Canonical  
**Type:** Technical contract / integration specification  
**Audience:** Engineers, DevOps, PM, Incident Response

**Purpose:**

Make the Order Status + OpenAI design impossible to "forget" by documenting:

- Where OpenAI is used (intent classification + unique reply generation)
- How it is configured (model env vars / secrets)
- How it is validated (eval harness + smoke proof mode)

**Key Sections:**

1. Executive Summary
2. Flow Diagram (text-based)
3. Code Map (llm_routing.py, llm_reply_rewriter.py, pipeline.py)
4. Configuration Map (env vars, AWS secrets)
5. PII Policy
6. Production-Read-Only Shadow Mode
7. Proof Requirements
8. Validation Harness
9. OpenAI Usage Compliance
10. Monitoring & Observability
11. Incident Response
12. Change Control
13. Related Documentation
14. Revision History

**Cross-References:**

- `docs/08_Engineering/CI_and_Actions_Runbook.md` (Order Status Proof section)
- `docs/08_Engineering/PR_Review_Checklist.md` (OpenAI evidence requirements)
- `docs/08_Engineering/OpenAI_Model_Plan.md`
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`
- `docs/05_FAQ_Automation/Order_Status_Automation.md`
- `docs/08_Engineering/Secrets_and_Environments.md`

**Impact:**

- ✅ Prevents "forgetting" OpenAI integration points during development
- ✅ Provides single source of truth for deployment and incident response
- ✅ Makes proof requirements explicit and unambiguous

---

### docs/08_Engineering/PR_Review_Checklist.md

**Status:** Canonical  
**Type:** Process checklist  
**Audience:** Engineers, PR reviewers, Cursor agents

**Purpose:**

Codify all PR requirements in one place:

- Risk labels (risk:R0 through risk:R4)
- Claude gate (mandatory, unskippable)
- Bugbot review (or documented fallback)
- CI checks (unit tests, lint, Codecov)
- Order Status special requirements (OpenAI evidence, E2E proof)

**Key Sections:**

1. Required Labels
2. Required Reviews
3. Required CI Checks
4. Order Status Changes (special requirements)
5. Evidence Artifacts
6. Final Checks
7. Merge Policy
8. Related Documentation
9. Revision History

**Cross-References:**

- `REHYDRATION_PACK/PR_DESCRIPTION/07_PR_TITLE_SCORING_RUBRIC.md`
- `REHYDRATION_PACK/PR_DESCRIPTION/03_PR_DESCRIPTION_SCORING_RUBRIC.md`
- `docs/08_Engineering/CI_and_Actions_Runbook.md`
- `docs/08_Engineering/Order_Status_OpenAI_Contract.md`
- `docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md`

**Impact:**

- ✅ Reduces PR rework loops (all requirements in one place)
- ✅ Ensures evidence artifacts are captured
- ✅ Makes OpenAI evidence requirement explicit for order-status PRs

---

## Modified Documents

### docs/08_Engineering/CI_and_Actions_Runbook.md

**Status:** Canonical  
**Type:** CI/CD runbook  
**Audience:** Engineers, Cursor agents

**Changes:**

- **Section:** "Order Status Proof (canonical requirements)" (lines 475-482)
- **Added:** ~10 lines
  - Explicit "NOT acceptable" statements:
    - "An order_status proof run is NOT acceptable if routing did not call OpenAI (unless intentionally disabled AND documented)"
    - "An order_status proof run is NOT acceptable if reply rewrite did not call OpenAI (if unique message requirement is in force)"
  - Cross-reference to `docs/08_Engineering/Order_Status_OpenAI_Contract.md`

**Impact:**

- ✅ Makes OpenAI evidence requirement unambiguous
- ✅ Prevents proofs without OpenAI evidence from being accepted
- ✅ Links to full contract doc for details

---

## Generated Documents

### docs/REGISTRY.md

**Type:** Generated index  
**Changes:** Registry count 406 → 407 docs

---

### docs/_generated/doc_registry.json

**Type:** Generated machine-readable registry  
**Changes:** Added entries for 2 new docs

---

### docs/_generated/doc_registry.compact.json

**Type:** Generated minified registry  
**Changes:** Updated for 2 new docs

---

## Deleted Documents

**None.**

---

## Cross-Reference Graph

```
Order_Status_OpenAI_Contract.md
  ├─ Referenced by: CI_and_Actions_Runbook.md
  ├─ Referenced by: PR_Review_Checklist.md
  ├─ References: OpenAI_Model_Plan.md
  ├─ References: Prod_ReadOnly_Shadow_Mode_Runbook.md
  ├─ References: Order_Status_Automation.md
  └─ References: Secrets_and_Environments.md

PR_Review_Checklist.md
  ├─ References: Order_Status_OpenAI_Contract.md
  ├─ References: CI_and_Actions_Runbook.md
  ├─ References: Prod_ReadOnly_Shadow_Mode_Runbook.md
  └─ References: PR_DESCRIPTION/ (scoring rubrics)

CI_and_Actions_Runbook.md (updated)
  └─ References: Order_Status_OpenAI_Contract.md (NEW)
```

---

## Impact on Existing Workflows

### Development Workflow

**Before:** OpenAI integration details scattered across code comments and implicit assumptions

**After:** Single canonical contract (`Order_Status_OpenAI_Contract.md`) serves as reference

---

### PR Review Workflow

**Before:** No single checklist; requirements scattered across runbooks and rehydration pack

**After:** `PR_Review_Checklist.md` provides all requirements in one place

---

### CI/CD Workflow

**Before:** OpenAI evidence requirement was implicit ("proof JSON should show...")

**After:** Explicit "NOT acceptable" statements in `CI_and_Actions_Runbook.md`

---

### Incident Response Workflow

**Before:** No OpenAI-specific runbook; responders would search code comments

**After:** `Order_Status_OpenAI_Contract.md` includes incident response section (outage, PII leak, cost spike)

---

## Validation

- ✅ All new docs follow naming conventions
- ✅ All new docs have revision history tables
- ✅ All new docs have cross-references
- ✅ Registry regenerated and validated (407 docs)
- ✅ No placeholders (`???`, `TBD`, `WIP`)
- ✅ No PII in docs
- ✅ All cross-references resolve

---

**Report completed:** 2026-01-20 22:28 UTC
