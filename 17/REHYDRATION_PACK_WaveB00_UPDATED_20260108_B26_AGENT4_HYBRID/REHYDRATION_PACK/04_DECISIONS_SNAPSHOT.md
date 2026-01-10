# Decisions Snapshot (Canonical)

This is a lightweight snapshot for **fast rehydration**.

Full decision log:
- `docs/00_Project_Admin/Decision_Log.md`

Last updated: 2025-12-29 (Wave F13)

---

## Decided (locked for implementation v1)

### Team + workflow
- **Team model:** ChatGPT (PM) + **3 Cursor agents** (Agent A, Agent B, Agent C)
- **Docs updates:** agents **update docs directly** every run (living docs must stay current)
- **Phase separation:** Foundation (docs/structure) is complete without Build kickoff; **B00 is only for when implementation begins**.
- **Minimal manual work:** PM + agents do the work; human does copy/paste + zip transfers only
- **Refactors:** allowed when justified, but must preserve contracts and keep tests/docs/registries consistent

### Secrets + environments
- **Secrets manager:** AWS Secrets Manager
- **Rule:** no secrets in repo; env templates live in `config/.env.example`

### Architecture + tooling defaults
- **Runtime architecture (v1):** AWS serverless
  - API Gateway → webhook receiver Lambda → SQS FIFO (+ DLQ) → worker Lambdas → DynamoDB idempotency/state
- **IaC tool of record (v1):** AWS CDK (TypeScript)
- **Backend language:** Python 3.11
- **Frontend:** planned/admin UI placeholder included (Next.js TypeScript)

### GitHub operating model (locked)
- **Main:** protected (PR required; required status checks)
- **Default execution:** sequential (single `run/<RUN_ID>` branch; agents A → B → C)
- **Merge style:** merge commit (preserve run boundaries)
- **Tooling:** GitHub CLI (`gh`) + auth token configured (agents can create/merge PRs; inspect Actions)
- **Branch budget:** keep branch count low; delete `run/<RUN_ID>` after merge (no branch explosion)

### Documentation OS rules
- **Canonical docs navigation:** `docs/INDEX.md` (curated)
- **Machine registries:** generated via scripts (`regen_doc_registry.py`, `regen_reference_registry.py`)
- **Plan checklist compiled view:** generated via `scripts/regen_plan_checklist.py`
- **Pack invariants:** validated via `scripts/verify_rehydration_pack.py` and `scripts/verify_plan_sync.py`

---


### Support automation defaults (CR-001)
- Order status when **no tracking exists yet**: send a conservative ETA window derived from verified order date + shipping bucket (Standard 3–5 business days; Rushed/Priority 1 business day; Pre-Order variable).
- Auto-close policy: default is no auto-close; allow auto-close only for an explicit whitelist of deflection-safe Tier 2 templates that include reply-to-reopen language (initial whitelist: `t_order_eta_no_tracking_verified`).

## Still open (non-blocking)
- Build-mode activation checklist items (AWS account/env details, CI baseline) — tracked in:
  - `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`

