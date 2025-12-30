# Master Wave Schedule (Full)

Last updated: 2025-12-29 (Wave F12)

This file is the **authoritative wave plan** for building and operating the repo as an AI-first system.

It covers two phases:

- **Phase F — Foundation (mode: `foundation`)**  
  Build the repo OS: structure, docs, indexes, policies, rehydration packs, validation automation.

- **Phase B — Build (mode: `build`)**  
  Implement the actual Richpanel automation system with Cursor agents, producing per-run artifacts.

The active mode flag is stored in:
- `REHYDRATION_PACK/MODE.yaml`

**Important (foundation vs build)**
- If your objective is **file/folder structure + documentation**, Phase **F** is the deliverable.
- Phase **B** (including **B00**) is a future plan for **implementation** and is not required to finish the documentation OS.
- Foundation completion criteria: `docs/00_Project_Admin/Definition_of_Done__Foundation.md`.
- Legacy “Wave 00–10” mapping: `docs/00_Project_Admin/Wave_Naming_and_Mapping.md`.

---

## Global “done looks like” (applies to every wave)

A wave is **DONE** only when:

1) The intended folders/files exist in the repo.
2) Navigation is updated when needed:
   - `docs/INDEX.md` (if canonical docs were added/renamed)
   - `docs/CODEMAP.md` (if structure changed)
3) Generated registries are updated:
   - `python scripts/regen_doc_registry.py`
   - `python scripts/regen_reference_registry.py` (if reference docs changed)
   - `python scripts/regen_plan_checklist.py` (if plan checkboxes changed materially)
4) Validations pass:
   - `python scripts/verify_rehydration_pack.py`
   - `python scripts/verify_plan_sync.py`
   - `python scripts/verify_doc_hygiene.py` (warnings acceptable unless `--strict`)
5) Changelog updated:
   - `CHANGELOG.md`
   - wave log (e.g., `WAVE_F06_CHANGELOG.md`) if the change set is large
6) Rehydration packs updated:
   - `REHYDRATION_PACK/` reflects the current state
   - `PM_REHYDRATION_PACK/` updated so this window stays aligned

---

## Phase F — Foundation (mode: foundation)

### F00 — Initial skeleton + baseline navigation ✅ DONE
**Goal**
- Establish initial repo structure and baseline documentation skeleton.

**Key deliverables**
- `docs/` structure
- `REHYDRATION_PACK/` and `PM_REHYDRATION_PACK/` created
- initial `docs/INDEX.md` + `docs/CODEMAP.md`

**Done looks like**
- Repo opens with clear “start here” docs.
- No broken links in `docs/INDEX.md`.

---

### F01 — Foundation rules + mode separation ✅ DONE
**Goal**
- Clarify that Cursor agents are only required in `build` mode, not in foundation.

**Key deliverables**
- `REHYDRATION_PACK/MODE.yaml`
- mode-aware pack instructions
- guardrails for PM vs agents

**Done looks like**
- `verify_rehydration_pack.py` passes in foundation mode.
- Pack templates exist but are not required in foundation mode.

---

### F02 — Docs indexing + navigation hardening ✅ DONE
**Goal**
- Make docs easy to navigate and easy for AI to retrieve.

**Key deliverables**
- docs registry + heading index generation
- `docs/REGISTRY.md` (generated)
- `docs/_generated/heading_index.json` (generated)

**Done looks like**
- `docs/REGISTRY.md` matches discovered docs.
- `docs/INDEX.md` links resolve.

---

### F03 — Rehydration pack automation hardening ✅ DONE
**Goal**
- Enforce rehydration pack invariants with automation.

**Key deliverables**
- `scripts/verify_rehydration_pack.py`
- `REHYDRATION_PACK/MANIFEST.yaml` (mode-aware)
- templates for run outputs

**Done looks like**
- Missing required pack files cause clear failures in strict mode (build mode only).

---

### F04 — Reference indexing + plan normalization ✅ DONE
**Goal**
- Import/normalize plan docs and vendor reference docs into a predictable library.

**Key deliverables**
- `reference/` structure + registries
- `docs/REGISTRY.md` updated after imports

**Done looks like**
- `reference/_generated/reference_registry.json` exists and parses.
- Plan docs are accessible via `docs/INDEX.md` and `docs/REGISTRY.md`.

---

### F05 — Policy + template hardening + living docs set ✅ DONE
**Goal**
- Lock in how AI agents must work (policies, templates, living docs set).

**Key deliverables**
- `docs/98_Agent_Ops/Policies/` hardened
- templates finalized
- living docs set defined and linked

**Done looks like**
- Living docs exist and are referenced in the rehydration pack.
- Agents have clear templates and update rules.

---

### F06 — Foundation readiness + plan→checklist extraction ✅ DONE
**Goal**
- Prepare for build mode by making readiness explicit and extracting a consolidated plan checklist.

**Key deliverables**
- `docs/00_Project_Admin/Build_Mode_Activation_Checklist.md`
- `REHYDRATION_PACK/FOUNDATION_STATUS.md`
- `scripts/regen_plan_checklist.py` + generated outputs
- canonical vs legacy redirect map clarified

**Done looks like**
- `python scripts/verify_plan_sync.py` passes
- `python scripts/regen_plan_checklist.py` produces consistent outputs
- legacy redirect folders contain only stubs (no duplicate canonical content)

---

### F07 — Doc hygiene cleanup (strict-ready) ✅ DONE
**Goal**
- Remove ambiguous placeholders (`...` and `…`) from INDEX-linked canonical docs so AI retrieval remains deterministic and token-efficient.

**Key deliverables**
- Replaced ellipsis-style placeholders with explicit placeholders (e.g., `<tag>`, `<TRACE_ID>`, `<RUN_ID>`, `<ISO_TIMESTAMP>`) across core docs.
- Ensured examples use explicit placeholder markers rather than truncation artifacts.
- Updated rehydration pack state to reflect Wave F07 completion.

**Done looks like**
- `python scripts/verify_doc_hygiene.py` passes with **no warnings**
- `python scripts/verify_plan_sync.py` passes after regeneration

---



### F08 — Registry sync + schedule clarity
**Goal**
- Ensure generated registries stay in sync with discovered docs.
- Remove confusion between legacy “Wave 00–10” drafts and the current **F/B** schedule.
- Reduce drift by converting legacy governance files into explicit redirect stubs.

**Key deliverables**
- `scripts/verify_plan_sync.py` shows a clear diff when registries drift (missing/extra paths).
- `docs/00_Project_Admin/Wave_Naming_and_Mapping.md` explains F/B/C waves + where **B00** fits.
- `docs/00_Project_Admin/Progress_Wave_Schedule.md` updated to point to rehydration schedule.
- Legacy governance docs in `docs/10_Governance_Continuous_Improvement/` are redirect stubs.
- `docs/_generated/doc_registry.json` regenerated and matches discovered docs.

**Done looks like**
- `python scripts/verify_plan_sync.py` passes (no docs registry mismatch).
- “Where does B00 fit?” is answered by canonical schedule docs.
- Legacy redirects prevent accidental edits in the wrong place.

---



### F09 — Foundation Definition of Done + schedule mapping ✅ DONE
**Goal**
- Remove ambiguity about what “foundation complete” means and where Build waves begin.

**Key deliverables**
- `docs/00_Project_Admin/Definition_of_Done__Foundation.md`
- `docs/00_Project_Admin/Wave_Naming_and_Mapping.md`
- Clarified schedule docs:
  - `REHYDRATION_PACK/WAVE_SCHEDULE.md`
  - `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md`

**Done looks like**
- Foundation completion is measurable (validators passing).
- B00 is clearly positioned as the first Build wave and is optional until implementation begins.

---

### F10 — Build-mode readiness pack ✅ DONE
**Goal**
- Make the repo immediately ready to switch to build mode with minimal friction and no drift.

**Key deliverables**
- PM prompt helpers:
  - `REHYDRATION_PACK/PM_INITIAL_PROMPT.md`
  - `REHYDRATION_PACK/PM_REHYDRATION_PROMPT.md`
- Build run scaffolding:
  - `scripts/new_run_folder.py`
  - `REHYDRATION_PACK/RUNS/README.md`
  - cleaned templates under `REHYDRATION_PACK/_TEMPLATES/` (no ambiguous placeholders)
- GitHub/repo ops governance:
  - `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`
  - `docs/08_Engineering/GitHub_Workflow_and_Repo_Standards.md`
  - `.github/` issue + PR templates

**Done looks like**
- PM can rehydrate deterministically using the provided prompts.
- A new run set can be created in seconds (`python scripts/new_run_folder.py --now`).
- Cursor agents have a clear policy for branches/commits/docs/tests/traceability.


## Phase B — Build (mode: build)

> Build waves are a plan. Actual ordering can change based on discoveries and integration constraints.
> Always reflect changes in `Decision_Log.md`, `Progress_Log.md`, and `CHANGELOG.md`.

### F11 — Multi-agent GitHub Ops hardening ✅ DONE
**Goal:** Eliminate common multi-agent GitHub failure modes (merge conflicts, branch explosion, stale main, accidental deletes, CI red loops).

**Done looks like:**
- GitHub ops policy is explicit and enforceable (`POL-GH-001`)
- Git run planning template exists (`GIT_RUN_PLAN.md`) and is included in run scaffolding
- Protected delete guard exists (`scripts/check_protected_deletes.py`)
- Branch budget helper exists (`scripts/branch_budget_check.py`)
- Single entrypoint for CI-equivalent checks exists (`scripts/run_ci_checks.py`)
- REHYDRATION_PACK includes `GITHUB_STATE.md` and `DELETE_APPROVALS.yaml`

---

### F12 — GitHub defaults locked + branch protection settings ✅ DONE
**Goal:** Lock final GitHub decisions and remove remaining ambiguity before build mode.

**Key deliverables**
- GitHub settings doc exists and is canonical:
  - `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md`
- Locked defaults recorded in rehydration pack + PM prompts:
  - main protected (PR required + required status checks)
  - merge commit
  - `gh` available
  - sequential default
- Protected delete guard does not silently skip when commit-range diffs are unavailable.

**Done looks like**
- `python scripts/run_ci_checks.py` passes locally (no confusing skip warnings for protected delete checks)
- `REHYDRATION_PACK/OPEN_QUESTIONS.md` has no GitHub-decision gaps

---

### B00 — Build kickoff + CI baseline
**Goal**
- Switch to build mode and establish a minimal CI pipeline.

**Key deliverables**
- `REHYDRATION_PACK/MODE.yaml` switched to `build`
- CI pipeline stub (GitHub Actions recommended)
- first `RUN_<...>/` folder with A/B/C artifacts (even if minimal)

**Done looks like**
- `verify_rehydration_pack.py --strict` passes
- first run artifacts are present and usable by PM

---

### B01 — Infra baseline (AWS CDK)
**Goal**
- Create foundational infrastructure stacks and environments.

**Key deliverables**
- CDK app scaffolding (`infra/`)
- dev/staging/prod environment configuration approach
- secrets baseline (AWS Secrets Manager)

**Done looks like**
- CDK synth/deploy works in at least a dev environment
- env vars and secrets are documented and referenced

---

### B02 — Ingest pipeline (webhook → queue → worker)
**Goal**
- Implement ingestion with ACK-fast and durable queueing.

**Key deliverables**
- webhook receiver + signature validation (if applicable)
- enqueue to SQS
- worker skeleton reading from queue

**Done looks like**
- End-to-end ingestion test evidence exists in `qa/test_evidence/`

---

### B03 — Richpanel integration (API client + tags/teams mapping)
**Goal**
- Implement Richpanel API client and canonical mapping logic.

**Key deliverables**
- Richpanel API client module
- tenant/team/tag config handling
- safe retries/backoff patterns

**Done looks like**
- Integration tests pass with sandbox/tenant setup (as possible)

---

### B04 — LLM router + safety gates
**Goal**
- Implement router that classifies intent and routes to dept or automation.

**Key deliverables**
- prompt + schema contract enforcement
- confidence scoring and gating
- safe mode / kill switch behavior

**Done looks like**
- eval harness can run a small golden set and produce metrics

---

### B05 — FAQ automation module
**Goal**
- Implement automation for core FAQ and order status flows.

**Key deliverables**
- template selection and response formatting
- guardrails against hallucination
- fallback to human when low confidence

**Done looks like**
- test evidence shows correct behavior for key scenarios

---

### B06 — Eval harness + datasets
**Goal**
- Build repeatable evaluation with datasets and regression tracking.

**Key deliverables**
- datasets storage format
- evaluation runner
- reporting outputs

**Done looks like**
- “golden set” evaluation is reproducible and tracked

---

### B07 — Observability + audit trail
**Goal**
- Build dashboards, tracing, and audit trail for decisions/actions.

**Key deliverables**
- structured logs and metrics
- dashboards (CloudWatch or chosen tooling)
- audit trail persistence

**Done looks like**
- issues can be debugged from logs + traces + audit trail

---

### B08 — Security/compliance hardening
**Goal**
- Harden IAM, network controls, retention, and data handling.

**Key deliverables**
- IAM baseline
- PII redaction verification
- retention controls

**Done looks like**
- security checklist items are checked off with evidence

---

### B09 — Reliability + load tests
**Goal**
- Verify SLOs and load behavior; improve resilience.

**Key deliverables**
- load tests
- backpressure handling
- retry policies

**Done looks like**
- documented SLOs with evidence from tests

---

### B10 — Release + runbooks + training
**Goal**
- Prepare production release and operational readiness.

**Key deliverables**
- deployment runbook
- incident response runbook
- support training materials

**Done looks like**
- ops can run the system safely with documented procedures



Wave F13 — CR-001 No-tracking delivery estimates + controlled auto-close whitelist

Objective:
- Add a deterministic no-tracking ETA response path to reduce order-status tickets.
- Update the auto-close policy from “never” to “whitelisted only” (reply-to-reopen).

Deliverables:
- New docs: CR-001 + No-Tracking Delivery Estimate Automation spec
- Updated: Order Status Automation, playbooks, templates, gating, test cases
- Rehydration pack updated with CR-001 scope + open questions
