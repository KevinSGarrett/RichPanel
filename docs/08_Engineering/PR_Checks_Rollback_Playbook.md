# PR Checks Rollback Playbook

Last updated: 2026-02-12
Status: Canonical

This playbook covers how to quickly disable (rollback) or re-enable the deterministic PR check suite without reverting code.

---

## Overview

All new/tightened PR checks respect a single GitHub Actions **variable**:

- **Name:** `PR_CHECKS_ROLLBACK_MODE`
- **Location:** GitHub repo Settings > Secrets and variables > Actions > Variables
- **Values:**
  - `0` (default) = **normal enforcement** — all checks run and block merges if they fail
  - `1` = **rollback mode** — new checks report SUCCESS without enforcement

### What rollback mode does

When `PR_CHECKS_ROLLBACK_MODE=1`:

| Check | Normal behavior | Rollback behavior |
|-------|----------------|-------------------|
| `Architecture Boundaries / import-linter` | Fails on forbidden imports | Passes without running import-linter |
| `CodeQL / analyze` | Runs full CodeQL analysis | Passes without running CodeQL |
| `validate` (Ruff) | Runs (advisory, continue-on-error) | Runs (advisory, continue-on-error) |
| `validate` (Mypy) | Runs (advisory, continue-on-error) | Runs (advisory, continue-on-error) |
| `validate` (compileall) | Fails on compile errors | Runs but does not block (continue-on-error) |
| `validate` (tests/coverage) | Always runs | Always runs (unchanged) |
| `PR Agent (advisory)` | Posts advisory comment | Skips silently |

**Important:** Required check contexts (`validate`, `Architecture Boundaries / import-linter`, `CodeQL / analyze`) still report **SUCCESS** in rollback mode. They are never skipped entirely, so branch protection required checks remain satisfied.

---

## A) Fast Rollback (no code revert)

**When:** New checks are causing unexpected failures and blocking PRs.

**Steps:**
1. Go to GitHub repo Settings > Secrets and variables > Actions > Variables
2. Find or create variable `PR_CHECKS_ROLLBACK_MODE`
3. Set value to `1`
4. Re-run failing PR checks — they will pass without enforcement

**Outcome:** All required check contexts still report green, but enforcement is relaxed. PRs can merge.

---

## B) Re-enable Enforcement

**When:** Issues are resolved and you want to restore blocking checks.

**Steps:**
1. Go to GitHub repo Settings > Secrets and variables > Actions > Variables
2. Set `PR_CHECKS_ROLLBACK_MODE` to `0` (or delete the variable; default is `0`)
3. Re-run checks on open PRs to confirm they pass with enforcement

---

## C) Hard Rollback (full code revert)

**When:** You want to completely remove the new checks and revert to the previous CI state.

**WARNING:** If you have already added new contexts (`Architecture Boundaries / import-linter`, `CodeQL / analyze`) to Branch Protection required checks:
- **DO NOT** delete the workflow files first
- Deleting a workflow while its check is still required will strand all PRs (missing required check = unmergeable)

**Safe sequence:**
1. First, set `PR_CHECKS_ROLLBACK_MODE=1` (fast rollback) to unblock any stuck PRs
2. Go to Branch Protection settings and **remove** the new check contexts from the required list
3. **Then** revert the PR that introduced the new workflows
4. Optionally remove the `PR_CHECKS_ROLLBACK_MODE` variable

**Alternative:** Keep the workflows in place and just use rollback mode (`PR_CHECKS_ROLLBACK_MODE=1`) indefinitely. The workflows will pass as no-ops.

---

## D) Bugbot Restore Option

Cursor Bugbot was deprecated because it was an external, non-deterministic service. The in-repo PR-Agent advisory review (`pr-agent.yml`) replaces it.

If you ever want to restore Bugbot:
1. Revert the commit that deprecated `.github/workflows/bugbot-review.yml`
2. The workflow will again post `@cursor review` comments via workflow dispatch
3. The PR-Agent workflow can coexist — it uses a different comment marker

---

## E) Safe Rollout Guidance

When introducing new required checks:

1. **Merge the PR** introducing new workflows + rollback mode
2. **Open a small test PR** to confirm new checks appear and are green
3. **Verify check context names** match exactly what you plan to require:
   - `Architecture Boundaries / import-linter`
   - `CodeQL / analyze`
4. **Then** update Branch Protection to add these as required checks
5. Keep `PR_CHECKS_ROLLBACK_MODE=0` (or unset) for normal enforcement

**Never add a check context to Branch Protection until it has run successfully at least once.**

---

## Required Check Contexts (for Branch Protection)

### Required (blocking)
- `validate` — CI job (ci.yml)
- `risk-label-check` — PR risk label required (pr_risk_label_required.yml)
- `claude-gate-check` — Claude gate required (pr_claude_gate_required.yml)
- `Architecture Boundaries / import-linter` — Import boundary check (architecture-boundaries.yml)
- `CodeQL / analyze` — Vulnerability scanning (codeql.yml)
- `codecov/patch` — Codecov patch coverage gate (external Codecov check)

### Advisory only (NOT required)
- `PR Agent (advisory)` — Advisory AI review comment (pr-agent.yml)
