# Progress Log

Last verified: 2026-01-11 - RUN_20260111_2301Z.

This is the canonical **long-lived** progress record for the project.

- For **current snapshot state** (token-efficient), see: REHYDRATION_PACK/02_CURRENT_STATE.md
- For large structural changes, see CHANGELOG.md and wave logs.

## Phases
- **Phase F (Foundation):** file/folder structure + documentation OS + indexing/chunking + policies/templates
- **Phase B (Build):** implementation runs (Cursor agents), tests, deployments, and releases

## Timeline

### 2026-01-11 - RUN_20260111_2301Z (Richpanel outbound smoke proof)
- Source: REHYDRATION_PACK/RUNS/RUN_20260111_2301Z
- Hardened outbound smoke CLI (test-ticket guardrails, AWS profile, PII-safe proof) and produced PASS proof using DEV ticket `api-scentimenttesting3300-41afc455-345e-4c18-b17f-ee0f0e9166e0`; ingress 200, Dynamo evidence present, Richpanel tags applied (status OPEN). CI-equivalent checks passed.

### 2026-01-11 - RUN_20260111_0532Z (LLM rewriter rebase + GPT-5 defaults)
- Source: REHYDRATION_PACK/RUNS/RUN_20260111_0532Z
- Rebased PR #72 onto latest main; preserved fail-closed reply rewriter (feature-flagged/off by default) and GPT-5.2 chat defaults.
- Kept shared Richpanel TicketMetadata helper (no shadowing) and PII-safe idempotency fingerprints.
- Regenerated run artifacts; CI-equivalent checks rerun.

### 2026-01-11 - RUN_20260111_0357Z (CI coverage + lint enforcement docs)
- Source: REHYDRATION_PACK/RUNS/RUN_20260111_0357Z
- Added complete CI workflow with lint checks (ruff, black, mypy as advisory), coverage collection with unittest discover, and Codecov upload.
- Added CI runbook Section 9 documenting Codecov phased rollout plan.
- Added CI runbook Section 10 documenting lint/type enforcement roadmap (Phase 1: advisory → Phase 2: fix+enforce → Phase 3: mypy).
- Updated runbook Section 1 with new CI workflow steps (lint, coverage, Codecov).
- Supersedes PR #74 due to merge conflicts; new PR #76 created.

### 2026-01-10 - RUN_20260110_1638Z (WaveAudit reply-after-close semantics + escalation tags)
- Source: REHYDRATION_PACK/RUNS/RUN_20260110_1638Z
- Added Richpanel `get_ticket()` helper and enforced read-before-write on outbound replies.
- Reply-after-close and follow-up cases now route to Email Support with `mw-followup-escalation`, `mw-route-email-support`, and skip-reason tags (no duplicate auto-replies).
- Updated tests, docs, and changelog; CI run/report captured for the run.

### 2026-01-10 - RUN_20260110_0244Z (Run-report enforcement + prompt archive + checklist hygiene)
- Source: REHYDRATION_PACK/RUNS/RUN_20260110_0244Z
- CI now fails in build mode if the latest run is missing or under-reported (RUN_REPORT.md required + min non-empty line counts).
- scripts/new_run_folder.py now generates RUN_REPORT.md for A/B/C and creates C/AGENT_PROMPTS_ARCHIVE.md by copying REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md.
- Updated RUNS README and refreshed Task Board + Master Checklist with shipped vs roadmap labels and a progress dashboard (no unverified env claims).

### 2026-01-10 - RUN_20260110_0019Z (Audit remediation: reply-after-close + status read-before-write)
- Source: REHYDRATION_PACK/RUNS/RUN_20260110_0019Z
- Implemented outbound read-before-write ticket status check + reply-after-close skip (route to Email Support when already closed).
- Implemented follow-up policy: if ticket already has `mw-auto-replied`, skip auto-reply and apply `route-email-support-team`.
- Added unit tests + docs update; added run report artifacts.


### 2026-01-05 - RUN_20260105_2221Z (mypy config for generated CDK assets)
- Source: REHYDRATION_PACK/RUNS/RUN_20260105_2221Z
- Added repo-root `mypy.ini` that scopes checking to `backend/src` + `scripts` and excludes generated CDK assets and archives to stop Cursor/mypy from scanning `asset.<hash>` folders.
- Documented the asset error and cleanup step (`infra/cdk/cdk.out` deletion) in the CI runbook.

### 2026-01-03 - RUN_20260103_2300Z (E2E evidence hardening + prod readiness checklist)
- Dev/Staging smoke job summaries now include explicit confirmations for idempotency, conversation state, and audit records, plus derived CloudWatch dashboard/alarm names.
- CI runbook evidence steps updated to require the new summary fields and to enumerate the dashboard/alarm names per environment.
- Prod promotion checklist restated to require human go/no-go plus captured `deploy-prod` and `prod-e2e-smoke` run URLs before enabling prod.

### 2026-01-03 - RUN_20260103_1640Z (Persistence validation hardening)
- Added offline persistence/pipeline tests covering kill-switch caching, idempotency writes, conversation-state/audit persistence, and ingress envelope sanitization.
- Extended dev_e2e_smoke.py to assert idempotency + conversation_state + audit trail records and emit console links into job summaries.
- Wired the new persistence test script into scripts/run_ci_checks.py and extended Dev/Staging smoke workflows (derived-only evidence, no secrets).
- Hardened E2E smoke evidence expectations to explicitly record idempotency + conversation state + audit confirmations and capture CloudWatch dashboards/alarms when present.
- Updated prod promotion checklist to require a human go/no-go plus recorded `deploy-prod` and `prod-e2e-smoke` workflow run URLs before enabling prod.

### 2026-01-03 - Docs heartbeat + anti-drift enforcement
- Added CI gate scripts/verify_admin_logs_sync.py to enforce that the latest RUN_ID is referenced in Progress_Log.md.
- Wired the new check into scripts/run_ci_checks.py.
- Updated Progress_Log, Issue_Log, and Decision_Log with entries for recent runs.

### 2026-01-02 - RUN_20260102_2148Z (Build mode)
- Added Dev E2E smoke test script (scripts/dev_e2e_smoke.py) and workflow (.github/workflows/dev-e2e-smoke.yml).
- Added Staging E2E smoke workflow (.github/workflows/staging-e2e-smoke.yml).
- Updated CI runbook with Dev E2E smoke workflow instructions.

### 2025-12-30 - RUN_20251230_1444Z (Build mode kickoff)
- Activated build mode in REHYDRATION_PACK/MODE.yaml.
- Added deploy workflows for dev (.github/workflows/deploy-dev.yml) and staging (.github/workflows/deploy-staging.yml).
- Created run folder structure under REHYDRATION_PACK/RUNS/.

### 2025-12-29 - Wave F13 (CR-001 No-tracking delivery estimates)
- Added CR-001 change request and FAQ spec for SLA-based delivery estimates.
- Added new Tier 2 template and updated playbooks/gating/test cases.

### 2025-12-29 - Wave F12 (GitHub defaults + branch protection)
- Locked GitHub merge settings (merge commits only, auto-delete branches).
- Added canonical branch protection rule for main with required status checks.
- Added auto-merge policy documentation.

### 2025-12-29 - Wave F07
- Doc hygiene cleanup: removed ambiguous ellipsis placeholders from INDEX-linked canonical docs.
- python scripts/verify_doc_hygiene.py now passes cleanly.

### 2025-12-29 - Wave F06
- Foundation readiness scaffolding added (build-mode activation checklist + foundation status snapshot).
- Plan -> checklist extraction automation added (script + generated outputs).

### 2025-12-29 - Wave F05
- Living docs set created (API refs, issues log, progress log, test evidence, env config, system matrix, user manual scaffolds).
- Policies/templates hardened to enforce continuous documentation.

### 2025-12-29 - Wave F04
- Vendor/reference indexing + plan normalization (see WAVE_F04_CHANGELOG.md).

### 2025-12-29 - Wave F03
- Pack automation hardening + mode-aware manifest validation (see WAVE_F03_CHANGELOG.md).

### 2025-12-29 - Wave F02
- Docs indexing/navigation hardening (see WAVE_F02_CHANGELOG.md).

### 2025-12-29 - Wave F01c
- Mode clarification between foundation vs build (see WAVE_F01C_CHANGELOG.md).
