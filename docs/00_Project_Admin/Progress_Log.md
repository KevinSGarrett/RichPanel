# Progress Log

Last verified: 2026-01-21 - RUN_20260121_1440Z.

This is the canonical **long-lived** progress record for the project.

- For **current snapshot state** (token-efficient), see: REHYDRATION_PACK/02_CURRENT_STATE.md
- For large structural changes, see CHANGELOG.md and wave logs.

## Phases
- **Phase F (Foundation):** file/folder structure + documentation OS + indexing/chunking + policies/templates
- **Phase B (Build):** implementation runs (Cursor agents), tests, deployments, and releases

## Timeline
### 2026-01-21 - RUN_20260121_1440Z (B50: gate:claude enforcement + PR description template lock-in)
- Source: REHYDRATION_PACK/RUNS/RUN_20260121_1440Z
- PR #136: https://github.com/KevinSGarrett/RichPanel/pull/136
- Enforced `gate:claude` label in the risk workflow; fails closed if missing while keeping exactly-one risk rule.
- Hardened Claude gate workflow to fail when skip!=false or response_id/model missing; logs gate status.
- Updated PR template and Cursor agent prompts (plus new short prompt) to require PR_DESCRIPTION self-scores and gate checklist.
- Added run artifacts (A/B/C) and recorded Claude response_id msg_013JdPWAb8ZrVPzkK6NTkDWi; Bugbot neutral (1 potential issue).

### 2026-01-21 - RUN_20260121_0354Z (B49: Claude Gate Hardening + PR Metadata Audit)
- Source: REHYDRATION_PACK/RUNS/RUN_20260121_0354Z
- PR #133: https://github.com/KevinSGarrett/RichPanel/pull/133
- Required Anthropic response ID + `model_used` outputs in Claude gate; fail-closed on skip/missing response id.
- Updated PR templates + PR_DESCRIPTION docs to require labels, self-scores, and Claude model/response id fields.
- Added run artifacts for A/B/C folders to satisfy build-mode verification.

### 2026-01-20 - RUN_20260120_2350Z (B48: OpenAI Evidence in Order Status Proof)
- Source: REHYDRATION_PACK/RUNS/RUN_20260120_2350Z
- Added OpenAI routing + rewrite evidence to dev_e2e_smoke proof JSON and require-openai flags
- Captured response_id metadata in llm_routing + llm_reply_rewriter; worker persists openai_rewrite evidence to state/audit
- Updated CI_and_Actions_Runbook.md with OpenAI evidence requirements
- Tests: python scripts/test_e2e_smoke_encoding.py

### 2026-01-20 - RUN_20260120_0221Z (B46: Order Status PASS_STRONG + Follow-up Routing Proofs)
- Source: REHYDRATION_PACK/RUNS/RUN_20260120_0221Z
- Enforced PASS_STRONG for order_status scenarios to require actual closure + follow-up routing evidence
- Updated pipeline close payloads and follow-up routing logic (route to Email Support Team without auto-reply)
- Added harness waits for closure + loop-prevention tag prior to follow-up
- Proofs: PASS_STRONG for order_status_no_tracking_short_window and order_status_tracking (dev sandbox only)
- Docs: updated CI_and_Actions_Runbook.md for PASS_STRONG + follow-up requirements
- Run artifacts: RUN_REPORT/RUN_SUMMARY/TEST_MATRIX/FIX_REPORT/STRUCTURE_REPORT/DOCS_IMPACT_MAP in A/B/C folders

### 2026-01-19 - RUN_20260119_2109Z (B46: Harden Claude PR Gate with Audit Evidence)
- Source: REHYDRATION_PACK/RUNS/RUN_20260119_2109Z
- PR #126: https://github.com/KevinSGarrett/RichPanel/pull/126
- Made Claude gate mandatory and unskippable via auto-apply gate:claude label
- Updated model strategy: R2/R3/R4 now use Opus 4.5 (claude-opus-4-5-20251101)
- Added Anthropic response ID and token usage to PR comments for audit trail
- Fixed Bugbot-identified race conditions in label application and concurrent label creation
- Added comprehensive unit tests: scripts/test_claude_gate_review.py (30+ tests)
- Updated CI_and_Actions_Runbook.md with proof requirements and unskippable gate documentation
- Commits: cd82003 (initial), a412bf1 (Bugbot fixes), 4276a93, 7030728, 6da4816, 66fbdb4, 210562d, 3ccdda6
- Run artifacts: Complete A/ folder with RUN_REPORT, TEST_MATRIX, FIX_REPORT, STRUCTURE_REPORT, DOCS_IMPACT_MAP

### 2026-01-19 - RUN_20260119_0255Z (B41: Secrets + Environments Documentation)
- Source: REHYDRATION_PACK/RUNS/RUN_20260119_0255Z
- Created canonical secrets documentation: docs/08_Engineering/Secrets_and_Environments.md
- Documented AWS Secrets Manager paths for all environments (dev/staging/prod)
- Documented GitHub Actions secrets guidance (dev/staging only, never prod)
- Added environment variable overrides, security constraints, and code references with validated line numbers
- Verified CI_and_Actions_Runbook.md already references new doc (section 1.5)
- Verified REHYDRATION_PACK templates already include "Secrets consulted" sections
- Run artifacts: RUN_REPORT/RUN_SUMMARY/TEST_MATRIX/DOCS_IMPACT_MAP/STRUCTURE_REPORT in C folder (A/B placeholders)

### 2026-01-18 - RUN_20260118_1717Z (B41: Order-status missing-context gate + evidence)
- Source: REHYDRATION_PACK/RUNS/RUN_20260118_1717Z
- Added order-context gate to fail closed when order_id/created_at/tracking-or-shipping are missing.
- Updated no-tracking fallback copy, added unit tests, and refreshed order-status docs.
- Regenerated doc registries and captured run artifacts for the PR workflow.

### 2026-01-18 - RUN_20260118_1628Z (B41 corrective: PR gate bug fixes)
- Source: REHYDRATION_PACK/RUNS/RUN_20260118_1628Z
- Fixed PR gate workflows: enforce exactly one risk label, require PASS word boundary, and scan issue/review comments + review submissions.
- Added corrective run artifacts and updated evidence for PR #118 successor.

### 2026-01-18 - RUN_20260118_1526Z (PR Risk Labels + Claude Gate Enforcement)
- Source: REHYDRATION_PACK/RUNS/RUN_20260118_1526Z
- Added PR workflows enforcing required risk labels and label-driven Claude PASS gates.
- Updated CI runbook with Risk Labels + Claude Gate section and merge safety reminders.
- Updated rehydration templates to capture risk label, gate:claude status, and Claude PASS evidence.
- Regenerated doc registries and plan checklist outputs.
- PR #118: Codecov + Bugbot + new gate workflows green; Claude PASS comment posted.

### 2026-01-17 - RUN_20260117_1751Z (Agent A B40: Order Status Ops + Docs)
- Source: REHYDRATION_PACK/RUNS/RUN_20260117_1751Z
- Docs-only PR to make Order Status operationally shippable.
- NEW: docs/08_Engineering/Prod_ReadOnly_Shadow_Mode_Runbook.md (628 lines) — zero-write production validation procedures.
- UPDATED: docs/08_Engineering/CI_and_Actions_Runbook.md (+89 lines) — Order Status proof canonical requirements (tracking + no-tracking + follow-up scenarios).
- UPDATED: docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md (+165 lines) — CHK-012A Order Status Deployment Readiness epic with 7 checklist categories.
- All 126 CI checks passed; docs registry regenerated (403 docs, 640 checklist items).
- Run artifacts: RUN_REPORT/RUN_SUMMARY/TEST_MATRIX/DOCS_IMPACT_MAP/STRUCTURE_REPORT in A/B/C folders (B/C stubs).

### 2026-01-17 - RUN_20260117_0511Z (Order-status tracking + no-tracking PASS_STRONG + follow-up)
- Sources: `REHYDRATION_PACK/RUNS/RUN_20260117_0510Z` (tracking ticket fingerprint 00037f39cf87) and `REHYDRATION_PACK/RUNS/RUN_20260117_0511Z` (no-tracking ticket fingerprint 0d21ae129a64).
- Middleware outbound enabled; automation on; both runs PASS_STRONG with mw-auto-replied + mw-order-status-answered tags and auto-close applied.
- Follow-up webhooks sent; no duplicate replies; route-to-support tag not added (routed_to_support=false) but no skip/escalation tags.
- Proofs PII-safe and include DynamoDB/log links and follow-up evidence.
- Run artifacts: RUN_REPORT/RUN_SUMMARY/TEST_MATRIX/STRUCTURE_REPORT/DOCS_IMPACT_MAP in each run folder (A/B/C).
### 2026-01-17 - RUN_20260117_0212Z (B40 read-only shadow mode closeout)
- Source: REHYDRATION_PACK/RUNS/RUN_20260117_0212Z
- Added run artifacts and evidence for B40: shadow reads via `MW_ALLOW_NETWORK_READS`, Richpanel write block via `RICHPANEL_WRITE_DISABLED`/`RichpanelWriteDisabledError`, pipeline `allow_network` propagation.
- CI: `python scripts/run_ci_checks.py --ci` passing on clean tree; Codecov patch and Cursor Bugbot green on PR #113.
- Docs impact: regenerated registries only; Progress_Log updated.

### 2026-01-14 - RUN_20260114_0707Z (Dev outbound toggle workflow + auto-revert)
- Source: REHYDRATION_PACK/RUNS/RUN_20260114_0707Z
- Added a DEV-only GitHub Actions workflow to toggle `RICHPANEL_OUTBOUND_ENABLED` on `rp-mw-dev-worker` with OIDC + auto-revert, plus operator runbook guidance and run artifacts.

### 2026-01-14 - RUN_20260114_0100Z (Order-status follow-up: reply evidence + coverage)
- Source: REHYDRATION_PACK/RUNS/RUN_20260114_0100Z
- Strengthened reply evidence (message/metadata/tag-based), added diagnostics/apply coverage tests to satisfy Codecov, and prepared follow-up PR for 95+ scoring.

### 2026-01-13 - RUN_20260113_2219Z (Order-status PASS_STRONG via nested ticket.state)
- Source: REHYDRATION_PACK/RUNS/RUN_20260113_2219Z
- Diagnostics proved Richpanel requires `{"ticket": {"state": "closed"}}` (status/state top-level rejected); middleware now uses nested ticket payload with tags/comment.
- Dev smoke proof (ticket 1001) PASS_STRONG: status open→closed, reply evidence via state change metadata, PII-safe proof JSON, no apply override.

### 2026-01-13 - RUN_20260113_2132Z (Order-status PASS_STRONG diagnostic + payload fix)
- Source: REHYDRATION_PACK/RUNS/RUN_20260113_2132Z
- Identified Richpanel ticket update schema requiring `{"ticket": {"state": "<status>"}}`; added diagnostics + apply option to dev_e2e_smoke and updated middleware to use nested ticket state with comment/tags.
- Delivered PASS_STRONG dev proof (ticket 1035) with PII-safe evidence (closed status + applied diagnostic payload); updated CI runbook criteria and proof classification.

### 2026-01-13 - RUN_20260113_1839Z (PR wait-for-green hardening + Next 10 sync)
- Source: REHYDRATION_PACK/RUNS/RUN_20260113_1839Z
- Hardened templates and CI runbook to require waiting for Codecov + Bugbot to finish (120–240s poll loop) before claiming a run/merge; added wait-for-green evidence section to Run Report template.
- Synced repo Next 10 list with PM pack priorities (10 items, updated statuses/owners).

### 2026-01-13 - RUN_20260113_1450Z (Order-status repair: loop prevention + strict PASS)
- Source: REHYDRATION_PACK/RUNS/RUN_20260113_1450Z
- Restored loop-prevention guard for order-status replies (route follow-ups to Email Support when `mw-auto-replied` already present) and serialized deduped tags as sorted lists.
- Tightened smoke PASS: fail when any skip/escalation tag is added; PASS requires resolved/closed or a success middleware tag added in the run (routing tags alone insufficient).
- Captured DEV proof (ticket 1035) with `mw-order-status-answered:RUN_20260113_1450Z` added and no skip tags added; updated CI runbook criteria.

### 2026-01-13 - RUN_20260113_1309Z (Order-status proof fix v3: encoded reads + real middleware tag)
- Source: REHYDRATION_PACK/RUNS/RUN_20260113_1309Z
- Re-ran order_status proof with canonical ID resolution + URL-encoded reads/writes; ensured deduped tags serialize as JSON lists.
- Tightened PASS logic to ignore historical skip/escalation tags; only fail on skip tags added this run.
- Captured PASS proof with `mw-order-status-answered:RUN_20260113_1309Z` and no skip tags added; status read no longer fails.

### 2026-01-13 - RUN_20260113_0528Z (Order-status proof fix v2: real resolve + client crash fix)
- Source: REHYDRATION_PACK/RUNS/RUN_20260113_0528Z
- Fixed Richpanel client crash when `ticket` is non-dict (Bugbot Medium) with type checks and new unit tests.
- Applied URL encoding to ticket reads as well as writes; ensured safe metadata fetches.
- Tightened order_status PASS criteria: skip/error tags no longer count; PASS requires resolve/close or valid reply tag.
- Added coverage for PII guard, Decimal sanitization, and skip-tag rejection; Codecov patch green target.

### 2026-01-13 - RUN_20260113_0433Z (Order-status E2E smoke proof mode + URL encoding fix)
- Source: REHYDRATION_PACK/RUNS/RUN_20260113_0433Z
- Fixed Richpanel middleware write operations: URL-encode email-based conversation IDs before building API paths (root cause: special chars @, <, >, + were causing 200 responses but no state mutation).
- Added order_status scenario to dev_e2e_smoke.py with deterministic seeded tracking payload and middleware-attributable PASS criteria (resolved/closed or mw-* tag beyond smoke).
- Added unit tests for URL encoding enforcement and scenario payload validation; wired into CI checks.
- Dev proof run delivered PASS with middleware tags applied (mw-routing-applied, mw-intent-order_status_tracking).

### 2026-01-13 - RUN_20260113_0122Z (Order lookup numeric tracking polish)
- Source: REHYDRATION_PACK/RUNS/RUN_20260113_0122Z
- Added numeric tracking handling for nested payloads (int/float) without dict stringification; added numeric tracking unit test; kept payload-first behavior intact.
- CI-equivalent and Codecov patch green; Bugbot remained green on PR #92.

### 2026-01-12 - RUN_20260112_2212Z (Order lookup nested tracking string fix)
- Source: REHYDRATION_PACK/RUNS/RUN_20260112_2212Z
- Fixed nested tracking string extraction (tracking under order payload) without reintroducing dict stringification; added nested tracking string unit test and resolved Bugbot Medium finding.
- Kept payload-first behavior, Codecov patch green, and CI-equivalent checks clean for PR #92.

### 2026-01-12 - RUN_20260112_2112Z (Order lookup payload fix + patch green)
- Source: REHYDRATION_PACK/RUNS/RUN_20260112_2112Z
- Fixed tracking dict handling in order lookup to avoid stringified dicts and added targeted tests for tracking dict/id, orders list payloads, shipment dicts, and fulfillment signals.
- Achieved Codecov patch green with new coverage; CI-equivalent and Bugbot checks passed for the follow-up PR.

### 2026-01-12 - RUN_20260112_1819Z (OpenAI model default enforcement)
- Source: REHYDRATION_PACK/RUNS/RUN_20260112_1819Z
- Added `scripts/verify_openai_model_defaults.py` to fail CI if GPT-4 family defaults appear in backend/src or config; wired into `run_ci_checks.py`.
- Fixed mojibake/encoding artifacts and updated `docs/08_Engineering/OpenAI_Model_Plan.md` to call out the new CI guard; refreshed checklist references.

### 2026-01-12 - RUN_20260112_1444Z (Worker flag coverage determinism)
- Source: REHYDRATION_PACK/RUNS/RUN_20260112_1444Z
- Made worker flag wiring test sys.path setup deterministic to close a Codecov patch miss; coverage now 100% on the file.
- Captured new run artifacts (A/B idle, C recorded coverage fix), ran coverage + CI-equivalent checks locally.

### 2026-01-12 - RUN_20260112_0408Z (E2E proof PII sanitization)
- Source: REHYDRATION_PACK/RUNS/RUN_20260112_0408Z
- Fixed PII leak in dev E2E smoke proof JSON (Bugbot finding from PR #82).
- Added path redaction (`_redact_path()`, `_sanitize_tag_result()`) to prevent ticket ID leakage.
- Added PII safety assertion (`_check_pii_safe()`) that scans for `%40`, `mail.`, `@`, etc. before writing proof JSON.
- Regenerated clean proof with `tags_added` including `mw-smoke:RUN_20260112_0408Z` and redacted paths.
- Repaired RUN_20260112_0259Z/B artifacts with real PR #82 data.
- Added PII-safe proof note to `docs/08_Engineering/CI_and_Actions_Runbook.md`.

### 2026-01-12 - RUN_20260112_0259Z (PR Health Check gates: Bugbot + Codecov + E2E enforcement)
- Source: REHYDRATION_PACK/RUNS/RUN_20260112_0259Z
- Enforced PR Health Check gates (Bugbot/Codecov/E2E proof) in templates and runbooks to ensure agents cannot claim PRs as "done" without evidence.
- Updated `REHYDRATION_PACK/_TEMPLATES/Cursor_Agent_Prompt_TEMPLATE.md` with required PR Health Check section (Bugbot review, Codecov status, E2E proof when applicable).
- Created `REHYDRATION_PACK/_TEMPLATES/Run_Report_TEMPLATE.md` with explicit Bugbot/Codecov/E2E findings sections.
- Updated `docs/08_Engineering/CI_and_Actions_Runbook.md` with comprehensive Section 4 "PR Health Check" including CLI-first commands for viewing Bugbot output, Codecov status, and running E2E smoke tests.
- Updated `docs/00_Project_Admin/To_Do/MASTER_CHECKLIST.md` with CHK-009B (PR Health Check gates shipped).
- Updated `REHYDRATION_PACK/05_TASK_BOARD.md` to reflect shipped process gate (TASK-252).

### 2026-01-12 - RUN_20260112_0054Z (Worker flag wiring + CI proof)
- Source: REHYDRATION_PACK/RUNS/RUN_20260112_0054Z
- Forwarded worker `allow_network`/`outbound_enabled` flags into `plan_actions`, added an offline-safe wiring unit test (now in `run_ci_checks.py`), and captured run artifacts. Local CI-equivalent checks passed for PR #78.
 
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
