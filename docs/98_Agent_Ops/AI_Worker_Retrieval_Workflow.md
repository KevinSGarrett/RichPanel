# AI Worker Retrieval Workflow

Last updated: 2025-12-29  
Last verified: 2025-12-29 — updated with reference library + citation guidance (Wave F04)

This document describes the **standard retrieval workflow** for AI workers so they can find the right information quickly **without blowing token limits**.

---

## 1) Identify what is canonical vs reference

### 1.1 Canonical project plan (source of truth)
Use `docs/` as the canonical plan library.

Start with:
- `docs/INDEX.md` (curated navigation)
- `docs/00_Project_Admin/Decision_Log.md` (locked decisions)
- `docs/00_Project_Admin/Canonical_vs_Legacy_Documentation_Paths.md` (avoid drift)

### 1.2 Reference libraries (supporting sources)
Use `reference/` for vendor docs and other non-plan inputs.

Start with:
- `reference/INDEX.md`
- `reference/richpanel/TOP_20.md`
- `reference/richpanel/INDEX.md`

Reference docs inform implementation, but **do not override** canonical decisions/specs unless the decision log is updated.

---

## 2) Fast retrieval path (token-efficient)

1) **Check the rehydration pack** (current truth + mode):
   - `REHYDRATION_PACK/00_START_HERE.md`
   - `REHYDRATION_PACK/MODE.yaml`
   - `REHYDRATION_PACK/04_DECISIONS_SNAPSHOT.md`
   - `REHYDRATION_PACK/02_CURRENT_STATE.md`

2) **Navigate via curated indexes**:
   - `docs/INDEX.md` → jump to the relevant domain (Routing, Richpanel integration, Security, etc.)
   - For Richpanel vendor behavior details, use:
     - `docs/03_Richpanel_Integration/Vendor_Doc_Crosswalk.md`
     - `reference/richpanel/TOP_20.md`

3) **If not found in ~60 seconds, use machine registries** (next section).

---

## 3) Machine registries (fast lookup without grepping)

### 3.1 Docs registry
- `docs/_generated/doc_registry.json`  
  Full list of docs files with metadata:
  - `title`
  - `status` (`canonical` / `supplemental` / `legacy` / `generated`)
  - `in_index` (true/false)
  - approximate size/line count

Use it when you only remember “a concept” but not the doc path.

### 3.2 Heading-level index
- `docs/_generated/heading_index.json`  
  Use this when you remember a **section name** (“Idempotency”, “Dedup window”, “Webhook auth”) but not the file.

### 3.3 Reference registry
- `reference/_generated/reference_registry.json`  
  Use this to locate vendor docs by topic/tag/category (especially in `reference/richpanel/Non_Indexed_Library/`).

---

## 4) How to cite sources (required)

When making decisions, writing specs, or producing run notes, cite sources by **path + section**.

### 4.1 Citation format
Use one of the following:

- **Markdown docs**
  - `docs/<path>.md — Section: "<heading text>"`
  - If the heading is stable, include the anchor:
    - `docs/<path>.md#<heading>`

- **Reference txt files**
  - `reference/richpanel/<path>.txt — First line/title: "<title_guess>"`

### 4.2 Examples
- `docs/03_Richpanel_Integration/Idempotency_Retry_Dedup.md — Section: "Dedup strategy"`
- `reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Reliability and Retries of HTTP Targets & API Calls/Delivery Guarantees for HTTP Targets.txt — First line/title: "Delivery Guarantees for HTTP Targets"`

### 4.3 Excerpt rule (token discipline)
If you need to quote, do **one small excerpt** (3–10 lines) and then summarize in your own words.

---

## 5) Updating docs without drift

When you add or modify important documentation:
1) Update the relevant curated index (`docs/INDEX.md` or `reference/*/INDEX.md`)
2) Regenerate registries:
   - `python scripts/regen_doc_registry.py`
   - `python scripts/regen_reference_registry.py`
3) Validate:
   - `python scripts/verify_plan_sync.py`
