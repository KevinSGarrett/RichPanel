# Wave Naming and Mapping

Last updated: 2025-12-29 — Wave F09

This repo separates **Foundation work** (file/folder structure + documentation OS) from **Build work** (implementation).
This prevents confusion where “documentation waves” accidentally turn into “building the system”.

---

## Wave ID glossary

- **Fxx** = **Foundation waves** (repo structure, documentation, indexing, policies, templates, validation automation).  
  **No Cursor execution is required** to complete Foundation.

- **Bxx** = **Build waves** (implementation of the actual Richpanel automation system).  
  Cursor agents + per-run artifacts become required once mode switches to `build`.

- **Cxx** = **Continuous improvement waves** (post‑release refinements).

---

## Key clarification: do we need B00 to finish documentation?

No.

- Foundation is “done” when the documentation OS and folder structure are complete and the validators pass.
- **B00** is only needed when you decide to **start building** the system.

See:
- `docs/00_Project_Admin/Definition_of_Done__Foundation.md`
- `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`

---

## Where B00 fits in the original “Wave 00–10” schedule

Earlier drafts used a single numbered schedule (“Wave 00…Wave 10+”) that mixed documentation work and implementation work.

In that legacy list:
- **Waves 00–03** are best interpreted as **Foundation**
- **Wave 04 and onward** are **Build/Implementation**

**B00** is the **Build kickoff** step. In the legacy numbering, treat it as:
- **the first step of Wave 04** (or a short “Wave 03 → Wave 04 transition”).

---

## Legacy “Wave 00–10” schedule (v0)

This is preserved here for reference because it is frequently quoted.

- **Wave 00 — Phase 0 Skeleton**
  - Goal: complete minimal skeleton + operational layer
  - Done: rehydration pack exists, policies imported, scaffolds exist, indexes regenerated

- **Wave 01 — Decision lock + conventions hardening**
  - Goal: remove ambiguity before implementation
  - Done: IaC/tooling decisions locked, run/task/doc ID conventions final, baseline .gitignore, CONTRIBUTING hardened

- **Wave 02 — Reference library indexing (Richpanel docs)**
  - Goal: make vendor docs retrievable without grep
  - Done: curated vendor index + machine registry for reference/richpanel/

- **Wave 03 — Rehydration pack automation**
  - Goal: enforce pack quality and consistency
  - Done: scripts generate/validate run folders + required files

- **Wave 04 — Backend code skeleton v1**
  - Goal: runnable backend in stub mode
  - Done: tests pass in stub mode, basic entrypoints exist

- **Wave 05 — Infra skeleton v1**
  - Goal: deployable skeleton aligned to plan
  - Done: dev/staging/prod templates + basic deploy path documented

- **Wave 06 — QA/Evals harness v1**
  - Goal: regression-proof routing + automation quality
  - Done: offline eval + baseline CI gate exists

- **Wave 07 — Observability/audit trail structure**
  - Goal: decisions are reconstructable
  - Done: event schema + audit trail path defined and scaffolded

- **Wave 08 — Security/privacy enforcement structure**
  - Goal: structural safety, not just policy text
  - Done: redaction/injection controls scaffolded + runbooks linked

- **Wave 09 — CI/CD + release hygiene**
  - Goal: automated quality + docs/index correctness
  - Done: CI validates lint/tests/registry, release checklist exists

- **Wave 10+ — Continuous improvement waves**
  - Goal: reduce token cost + navigation friction, keep drift at zero
  - Done: measurable improvements, no broken navigation ever

---

## Crosswalk: legacy waves → current phases

| Legacy wave | What it means (today) | Current phase |
|---|---|---|
| Wave 00–03 | Documentation OS + repo structure + indexing + pack automation | Foundation (Fxx) |
| Wave 04–09 | Implementation (backend/infra/QA/observability/security/CI) | Build (Bxx) |
| Wave 10+ | Ongoing refinement after build | Improvement (Cxx) |

If a conflict exists, treat `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md` as canonical.
