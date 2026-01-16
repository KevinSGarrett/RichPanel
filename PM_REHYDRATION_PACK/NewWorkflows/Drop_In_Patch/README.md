# RichPanel Drop-in Patch Pack (Bugbot + Codecov + Claude Review)

This patch pack adds a **risk-based, label-triggered** strategy for running:

- **Bugbot** (via `@cursor review` comment)
- **Codecov** (coverage upload)
- **Claude review** (Claude Code GitHub Action `/review`)

The goal is that these expensive / noisy gates **do not run on every tiny commit**, but still become **machine-enforceable** when a PR is ready to merge.

---

## What this pack changes

### 1) CI no longer uploads to Codecov on every PR commit
- Existing `.github/workflows/ci.yml` is modified to remove the Codecov upload step.
- A new workflow runs Codecov only when gated.

### 2) New workflows

- `.github/workflows/gated-quality.yml`
  - Trigger: PR label **`gates:ready`** (or manual `workflow_dispatch`)
  - Runs:
    - `coverage-codecov` (risk ≥ R2)
    - `claude-review` (risk ≥ R3) using `anthropics/claude-code-action@v1`
    - `bugbot-trigger` (risk ≥ R3) posts `@cursor review`
  - Adds labels:
    - `gates:passed` on success
    - `gates:failed` on failure
    - removes `gates:ready` automatically so it can be re-added later

- `.github/workflows/gates-staleness.yml`
  - Trigger: new commits on a PR (`pull_request.synchronize`)
  - If the PR had `gates:passed` or `gates:failed`, it removes them and adds `stale:gates`.

- `.github/workflows/policy-gate.yml`
  - Trigger: all PR updates
  - Enforces required checks based on `risk:R*` labels.

- `.github/workflows/seed-gate-labels.yml`
  - Trigger: manual
  - Creates/updates the labels used by this system.

### 3) New root file
- `CLAUDE.md` — guidance file used by Claude Code review.

### 4) Updated PR template
- `.github/pull_request_template.md` updated to include risk labels + gated strategy.

---

## Prerequisites

### Secrets

1) `CODECOV_TOKEN` (already in your repo today)
2) `ANTHROPIC_API_KEY` (new)
   - This is a **Claude API key** (Console key), used by GitHub Actions.

> Note: Claude Pro subscription does not typically provide an API key automatically; Actions automation usually requires a Console API key.

### Claude GitHub App

For best results, install the official Claude GitHub App and follow Anthropic’s GitHub Actions setup guidance.

---

## Install / Apply

### Option A (recommended): copy the `drop_in/` tree

Copy the contents of `drop_in/` into your repo root.

### Option B: use patches

Apply patches in order:

```bash
git apply patches/*.patch
```

---

## One-time setup

1) Run the **Seed Gate Labels** workflow:
   - Actions → **Seed Gate Labels** → Run workflow

2) Update branch protection for `main` to require the **Policy Gate** check.
   - In GitHub UI: Settings → Branches → Branch protection rules
   - Add required check: `policy-gate`

---

## Day-to-day usage (AI-only workflow)

1) PM opens PR and applies a single risk label: `risk:R0`..`risk:R4`
2) Agents iterate normally (CI runs on each commit)
3) When the diff is stable, PM applies **`gates:ready`**
4) Gated Quality runs and posts:
   - Codecov upload (R2+)
   - Claude review (R3+)
   - Bugbot trigger (R3+)
5) If agents push new commits after gates, PR becomes `stale:gates` and must be re-gated.

---

## Files included

- `drop_in/.github/workflows/ci.yml`
- `drop_in/.github/workflows/gated-quality.yml`
- `drop_in/.github/workflows/gates-staleness.yml`
- `drop_in/.github/workflows/policy-gate.yml`
- `drop_in/.github/workflows/seed-gate-labels.yml`
- `drop_in/.github/pull_request_template.md`
- `drop_in/CLAUDE.md`


- `drop_in/branch_protection_main.json` (updated snapshot recommending required check `policy-gate`)
- `drop_in/docs/08_Engineering/Branch_Protection_and_Merge_Settings.md` (updated to mention `policy-gate`)
