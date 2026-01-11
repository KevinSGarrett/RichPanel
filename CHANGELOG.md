# Changelog

## 2026-01-11 - RUN_20260111_1638Z (PR Health Check + E2E routine enforcement)
- Updated Cursor Agent Prompt template with comprehensive PR Health Check requirements (CI, Codecov, Bugbot, E2E tests).
- Updated Agent Run Report template with PR Health Check section (structured fields for all evidence).
- Added section 10 to CI and Actions Runbook: PR Health Check (required before every merge).
- Created E2E Test Runbook (docs/08_Engineering/E2E_Test_Runbook.md) with detailed procedures for dev/staging/prod E2E smoke tests.
- Created NEXT_10 suggested items list (REHYDRATION_PACK/09_NEXT_10_SUGGESTED_ITEMS.md) to track emerging priorities.
- Linked NEXT_10 from TASK_BOARD.md; now visible as emerging priorities tracker.
- Evidence: REHYDRATION_PACK/RUNS/RUN_20260111_1638Z/A/, CI checks pass (python scripts/run_ci_checks.py --ci)

## 2026-01-10 - RUN_20260110_1638Z (WaveAudit reply-after-close semantics)
- Added Richpanel client/executor get_ticket() helper to enforce read-before-write before outbound replies.
- Order-status automation now routes closed/follow-up tickets to Email Support with escalation + skip-reason tags instead of auto-replying.
- Updated docs/tests/progress log/run artifacts for the new safety semantics.

## 2025-12-29 — Wave F13 (CR-001 No-tracking delivery estimates)
- Added CR-001 change request and FAQ spec for SLA-based delivery estimates when tracking does not exist yet.
- Added new Tier 2 template `t_order_eta_no_tracking_verified` and updated playbooks/gating/test cases.
- Updated auto-close policy from “never” to “whitelisted only” (reply-to-reopen required).

## 2025-12-29 — Wave F12 (GitHub defaults locked + branch protection + protected delete guard)
- Added canonical GitHub settings guide: `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md`
- Improved `scripts/check_protected_deletes.py` to work locally (staged/working) and in CI (commit range), without confusing skip warnings.
- Updated CI entrypoint to pass `--ci` to protected delete checks when applicable.
- See `WAVE_F12_CHANGELOG.md`.

This is the **canonical** chronological log of meaningful changes to the repository:
structure, documentation, policies, automation, and implementation.

## How to use this changelog (AI-first)
- **Every meaningful change** (docs, code, infra, configs, policies) should add an entry.
- Keep entries **short and chunkable** and link to deeper evidence (diffs, test output, artifacts).
- Prefer referencing dedicated wave logs (`WAVE_Fxx_CHANGELOG.md`) when a change set is large.

## Entry template
- **Date:** YYYY-MM-DD
- **Wave/Run:** e.g., `Wave F06` or `RUN_YYYYMMDD_HHMMZ`
- **Summary:** 3–8 bullets
- **Evidence:** links/paths to artifacts, test output, CI logs

---


## 2025-12-29 — Wave F07 (Doc hygiene cleanup)
- Removed ambiguous ellipsis placeholders (`...` and `…`) from INDEX-linked canonical docs, replacing them with explicit placeholders (e.g., `<tag>`, `<TRACE_ID>`, `<RUN_ID>`).
- `python scripts/verify_doc_hygiene.py` now passes with **no warnings**.
- Updated rehydration pack state + wave schedule to reflect Wave F07.
- See `WAVE_F07_CHANGELOG.md`.

## 2025-12-29 — Wave F06 (Foundation readiness + plan checklist extraction)
- Added build-mode activation criteria and foundation readiness snapshots.
- Standardized legacy redirect folders (MOVED.md stubs) and clarified canonical vs legacy paths.
- Added automated plan→checklist extraction (generated outputs + script) and wired into validations.
- Cleaned up core navigation docs (INDEX/CODEMAP/ROADMAP) and removed ambiguous placeholders.
- See `WAVE_F06_CHANGELOG.md`.

## 2025-12-29 — Wave F05 (Policy + template hardening, living docs set)
- Added/standardized the living documentation set and enforced update policies/templates.
- See `WAVE_F05_CHANGELOG.md`.

## 2025-12-29 — Wave F04 (Reference indexing + plan normalization)
- Added curated vendor/reference indexes and machine registries.
- See `WAVE_F04_CHANGELOG.md`.

## 2025-12-29 — Wave F03 (Pack automation hardening)
- Added mode-aware rehydration pack validation automation.
- See `WAVE_F03_CHANGELOG.md`.

## 2025-12-29 — Wave F02 (Docs indexing + navigation hardening)
- Added/strengthened docs registries, outlines, and heading-level indexes.
- See `WAVE_F02_CHANGELOG.md`.

## 2025-12-29 — Wave F01c (Mode clarification)
- Split foundation vs build workflows and made REHYDRATION_PACK mode-aware.
- See `WAVE_F01C_CHANGELOG.md`.

## 2025-12-29 — Wave F08 — Registry sync + schedule clarity

- Fixed docs registry drift (docs registry now matches discovered docs; `verify_plan_sync.py` passes).
- Converted legacy governance docs in `docs/10_Governance_Continuous_Improvement/` into explicit redirect stubs pointing to canonical `docs/11_Governance_Continuous_Improvement/`.
- Added wave naming/mapping clarification doc: `docs/00_Project_Admin/Wave_Naming_and_Mapping.md` (includes where **B00** fits).
- Updated `Progress_Wave_Schedule.md` to point to rehydration pack schedule as the authoritative source.
- Improved `scripts/verify_plan_sync.py` failure output to include missing/extra doc paths (faster debugging).

## 2025-12-29 — Wave F10 — Build-mode readiness pack

- Added PM prompt helpers:
  - `REHYDRATION_PACK/PM_INITIAL_PROMPT.md`
  - `REHYDRATION_PACK/PM_REHYDRATION_PROMPT.md`
- Added build-mode run scaffolding:
  - `scripts/new_run_folder.py`
  - `REHYDRATION_PACK/RUNS/README.md`
- Added GitHub/repo ops governance:
  - `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`
  - `docs/08_Engineering/GitHub_Workflow_and_Repo_Standards.md`
  - `.github/` issue + PR templates
- Cleaned build-mode templates to avoid ambiguous placeholder punctuation.

- See `WAVE_F10_CHANGELOG.md`.


## 2025-12-29 — Wave F11 — Multi-agent GitHub Ops hardening
- Expanded GitHub ops policy to prevent merge conflicts, branch explosion, stale main, and accidental deletes.
- Added CI-equivalent entrypoint (`scripts/run_ci_checks.py`) and Git safety scripts:
  - `scripts/check_protected_deletes.py`
  - `scripts/branch_budget_check.py`
- Added multi-agent GitOps playbook and CI runbook under `docs/08_Engineering/`.
- Added `REHYDRATION_PACK/GITHUB_STATE.md` and `REHYDRATION_PACK/DELETE_APPROVALS.yaml`.
- Added a minimal GitHub Actions workflow (`.github/workflows/ci.yml`) to keep validations green.


## 2025-12-29 — Wave F09 — Foundation/Build clarity + Foundation DoD

- Clarified that Build kickoff (**B00**) is not required to complete the documentation OS (Foundation).
- Added a formal Foundation Definition of Done:
  - `docs/00_Project_Admin/Definition_of_Done__Foundation.md`
- Updated schedules and mapping docs to reflect the legacy Wave 00–10 schedule vs current Foundation/Build phases:
  - `REHYDRATION_PACK/WAVE_SCHEDULE.md`
  - `REHYDRATION_PACK/WAVE_SCHEDULE_FULL.md`
  - `docs/00_Project_Admin/Wave_Naming_and_Mapping.md`
- Updated task board priorities to focus on Foundation acceptance/freeze (build activation is optional later):
  - `REHYDRATION_PACK/05_TASK_BOARD.md`
- See `WAVE_F09_CHANGELOG.md`.

