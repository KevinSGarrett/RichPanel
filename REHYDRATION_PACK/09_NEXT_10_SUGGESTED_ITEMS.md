# Next 10 Suggested Items

Last updated: 2026-01-11  
Status: Living (updated as priorities shift)

This file captures the **next 10 high-priority items** identified during agent runs, PM reviews, or operational incidents. Items here are candidates for promotion to `05_TASK_BOARD.md` once scoped and prioritized.

---

## Purpose

- **Capture emerging priorities** that don't yet fit into the formal task board
- **Surface technical debt** discovered during implementation
- **Track follow-up work** deferred from recent runs
- **Maintain a backlog** of improvements that would make the system safer/faster/better

---

## Format

Each item should include:
- **Item ID**: N10-### (for tracking)
- **Title**: Short, actionable description
- **Context**: Why this matters (1-2 sentences)
- **Effort**: Rough estimate (small/medium/large)
- **Dependencies**: Blockers or prerequisites
- **Proposed by**: Agent/PM name + run ID or date

---

## Current Next 10 (prioritized)

### N10-001: Harden Codecov to hard gate (Phase 2)
- **Context**: Codecov is currently advisory (`fail_ci_if_error: false`). Once stable for 2-3 PRs, make it a hard requirement.
- **Effort**: Small
- **Dependencies**: 2-3 successful PRs with Codecov uploads
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Observation (Phase 1 active)

### N10-002: Add Bugbot quota monitoring
- **Context**: When Bugbot quota exhausts, we fall back to manual review. Need a way to track quota usage and alert before exhaustion.
- **Effort**: Medium
- **Dependencies**: Bugbot API access (if available)
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Proposed

### N10-003: Add CloudWatch dashboards to CDK stack
- **Context**: E2E smoke tests surface "no dashboards/alarms surfaced" — we should provision them via CDK.
- **Effort**: Medium
- **Dependencies**: None
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Proposed

### N10-004: Add CloudWatch alarms to CDK stack
- **Context**: E2E smoke tests expect `rp-mw-<env>-dlq-depth`, `rp-mw-<env>-worker-errors`, etc., but these aren't defined yet.
- **Effort**: Medium
- **Dependencies**: CloudWatch dashboards (N10-003)
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Proposed

### N10-005: Automate run artifact validation in CI
- **Context**: CI checks for placeholders in run artifacts, but doesn't validate structure or required fields. Add schema validation.
- **Effort**: Medium
- **Dependencies**: None (can use JSON schema or custom Python validator)
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Proposed

### N10-006: Add E2E smoke test to PR CI workflow (dev only)
- **Context**: Currently E2E tests are manual/workflow-dispatch. Consider auto-triggering dev E2E on PRs that touch automation paths.
- **Effort**: Large (requires careful scoping to avoid flaky tests blocking PRs)
- **Dependencies**: Stable dev stack, fast E2E tests (<2 min)
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Proposed (needs PM review)

### N10-007: Add pre-commit hooks for Python formatting/linting
- **Context**: CI catches black/ruff issues, but would be faster to catch locally before push.
- **Effort**: Small
- **Dependencies**: None (use `pre-commit` framework)
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Proposed

### N10-008: Document Shopify/ShipStation integration credentials rotation
- **Context**: API tokens expire; need a runbook for rotation without downtime.
- **Effort**: Small
- **Dependencies**: Secrets Management Policy (already exists)
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Proposed

### N10-009: Add coverage reporting to local CI checks
- **Context**: `python scripts/run_ci_checks.py` doesn't run coverage locally (only in CI). Would be useful for agents to see coverage gaps before pushing.
- **Effort**: Small
- **Dependencies**: None (coverage already installed)
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Proposed

### N10-010: Investigate Bugbot workflow dispatch alternative
- **Context**: Current Bugbot trigger requires PR comments. Workflow dispatch is available but may have different behavior.
- **Effort**: Small
- **Dependencies**: Access to Bugbot workflow dispatch endpoint
- **Proposed by**: Agent A, RUN_20260111_1638Z
- **Status**: Proposed

---

## Completed (moved to task board or shipped)

None yet.

---

## Deferred (not prioritized yet)

None yet.

---

## How to use this file

### For agents
1. When you discover follow-up work during a run, add it here with an N10-### ID
2. Include enough context that PM/other agents can evaluate priority
3. Reference this file in your RUN_SUMMARY.md under "Follow-ups"

### For PM
1. Review this file weekly (or after major runs)
2. Promote high-priority items to `05_TASK_BOARD.md` with proper scoping
3. Mark completed items (move to "Completed" section)
4. Defer low-priority items (move to "Deferred" section)

### For reviewers
1. Use this file to understand upcoming work and context
2. Suggest new items during code review or incident triage
3. Challenge items that seem stale or no longer relevant
