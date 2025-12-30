# Chunking and Indexing Standard (AI-first)

**Purpose:** keep documentation and run artifacts **easy to retrieve** and **token-efficient** for AI workers.

---

## 1) Core rules (non-negotiable)

### 1.1 No orphan files
Every non-trivial doc or code area must be linked from:
- `docs/INDEX.md` (curated)
- and/or `docs/REGISTRY.md` / `docs/_generated/doc_registry.json` (complete)

### 1.2 Prefer small, single-purpose files
- Target **300–900 lines** per markdown file (soft cap).
- If a document grows beyond ~900 lines, **split it**:
  - `Topic_Part_01.md`
  - `Topic_Part_02.md`
  - plus a short `Topic.md` that acts as a table-of-contents + summary.

### 1.3 Stable IDs for reference
When creating any new “important” doc (spec/runbook/template), assign a stable ID:
- `DOC-<AREA>-###` for docs/specs
- `RUN-YYYYMMDD-###` for run sessions
- `POL-<AREA>-###` for policies (already provided)

Store the ID near the top of the file.

### 1.4 “Read order” blocks
At the top of any doc that is part of a workflow, include:
- **Read order**
- **Who uses this**
- **When to update**

---

## 2) Mandatory doc header template

Copy/paste this at the top of new markdown docs:

```md
# <Title>

**Doc ID:** DOC-<AREA>-###  
**Last updated:** YYYY-MM-DD  
**Owner:** <person/role>  
**Status:** draft | active | deprecated  
**Depends on:** <links>

## Read order
1. <link>
2. <link>

## Purpose
<1–3 sentences>

---
```

---

## 3) Indexing expectations

### 3.1 Curated index (human + AI)
- `docs/INDEX.md` must point to all “top of funnel” docs.
- Every new major feature must appear in:
  - `docs/ROADMAP.md`
  - `docs/CODEMAP.md`

### 3.2 Machine registry (AI retrieval)
We keep a generated registry:
- `docs/_generated/doc_registry.json`
- `docs/_generated/doc_outline.json`
- `docs/_generated/heading_index.json`

It allows:
- quick lookup by title
- path resolution without searching
- simple filtering by section

If you add/move/delete docs, regenerate the registry.

---

## 4) Chunk style guidelines (token efficiency)
- Prefer bullets and tables over long prose.
- Put “canonical answers” in **short** sections.
- Put examples in appendices.
- Avoid duplication: link instead.

---

## 5) Where to put things

- Specs / architecture: `docs/02_System_Architecture/`, `docs/03_Richpanel_Integration/`, `docs/04_LLM_Design_Evaluation/`
- Runbooks: `docs/09_Deployment_Operations/` and `docs/10_Operations_Runbooks_Training/`
- Agent workflow: `docs/98_Agent_Ops/`
- Raw reference docs (vendor docs): `/reference/`

