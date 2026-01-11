# Next 10 Suggested Items

Last updated: 2026-01-11
Status: Living list (emerging priorities)

Each item uses ID N10-### with short context, effort, dependencies, and status.

## Current Next 10

1. **N10-001** — Harden Codecov gating (Phase 2)
   - Context: Move Codecov from advisory to enforced once stable.
   - Effort: Small; Dependencies: stable CI uploads; Status: Proposed.

2. **N10-002** — Bugbot quota monitoring
   - Context: Detect quota exhaustion early and surface manual-review fallback.
   - Effort: Medium; Dependencies: Bugbot API/metrics; Status: Proposed.

3. **N10-003** — CloudWatch dashboards for middleware
   - Context: E2E smoke expects dashboards; provision via CDK.
   - Effort: Medium; Dependencies: infra/cdk; Status: Proposed.

4. **N10-004** — CloudWatch alarms for DLQ/worker/ingress
   - Context: Add alarms surfaced in E2E summaries (dlq-depth, worker-errors, throttles, ingress-errors).
   - Effort: Medium; Dependencies: dashboards (N10-003); Status: Proposed.

5. **N10-005** — Run artifact schema validation in CI
   - Context: Enforce structure/required fields beyond placeholder checks.
   - Effort: Medium; Dependencies: none; Status: Proposed.

6. **N10-006** — Optional dev E2E auto-trigger for PRs touching automation
   - Context: Reduce misses by auto-running dev E2E on scoped PRs.
   - Effort: Large; Dependencies: fast/flaky-safe E2E; Status: Proposed.

7. **N10-007** — Pre-commit hooks for Python lint/format
   - Context: Catch ruff/black issues before CI.
   - Effort: Small; Dependencies: none; Status: Proposed.

8. **N10-008** — Credential rotation runbook (Shopify/ShipStation)
   - Context: Document rotation steps to avoid expiry incidents.
   - Effort: Small; Dependencies: Secrets policy; Status: Proposed.

9. **N10-009** — Local coverage option in run_ci_checks
   - Context: Allow optional coverage run locally to see gaps before push.
   - Effort: Small; Dependencies: none; Status: Proposed.

10. **N10-010** — Bugbot workflow-dispatch alternative
    - Context: Provide workflow trigger when comments are throttled or disabled.
    - Effort: Small; Dependencies: Bugbot workflow; Status: Proposed.

## How to use
- Agents: add new items with N10 IDs when you discover follow-ups; keep concise.
- PM: review regularly, promote to task board when prioritized, mark done/deferred.
- Reviewers: reference this list for upcoming work and suggest removals of stale items.
