# Repo policy and branch protection

This document defines repo-level settings that support an AI-only workflow without chaos.

---

## 1) Required checks strategy (why you should not “require everything”)

If you make these required at the branch protection level:
- `codecov/patch`
- `codecov/project`

then GitHub will expect them on **every** PR update. That forces Codecov to run on every tiny push.

Similarly, if you try to require Bugbot or Claude by required checks, you will get:
- noisy blocking on tiny PRs
- “Expected — waiting for status” states
- wasted tokens and CI minutes

### Recommended strategy
1) Keep **one stable required CI check** (your existing `validate`)
2) Add **one custom required check**: `policy-gate`
3) Let `policy-gate` enforce:
   - which gates are required based on risk label
   - whether those gates were run recently enough (staleness)

This provides dynamic enforcement without forcing heavy tools to run on every commit.

---

## 2) Branch protection: recommended baseline for `main`

### Must have
- Require status checks: `validate` and `policy-gate`
- Require conversation resolution: ON
- Require linear history: optional (merge commits are allowed)
- Require signed commits: optional (but helpful)
- Allow force pushes: OFF
- Allow deletions: OFF

### Optional hardening
- Require pull request reviews:
  - In AI-only workflow, you may set this to 0
  - Or require 1 “approval” that is provided by a bot account / gatekeeper check (preferred)
- Restrict who can push to matching branches: ON

---

## 3) Merge policy

- Merge commit only (preferred)
- Auto-merge must be used:
  - `gh pr merge --auto --merge --delete-branch`

Rationale: consistent traceability + fewer “oops merged early” events.

---

## 4) Required labels policy

Every PR must have exactly one `risk:*` label.

Optional but recommended labels:
- `gates:ready`
- `gates:passed`
- `gates:stale`
- `waiver:active`

See: `policies/07_LABEL_TAXONOMY.md`

---

## 5) Workflow triggers policy (avoid wasted runs)

### CI
- Trigger on PR open/synchronize/reopen
- Use `paths-ignore` to skip CI for docs-only (if acceptable)

### Heavy gates
- Trigger on:
  - label `gates:ready`, or
  - workflow_dispatch from PM tooling, or
  - scheduled nightly (optional)

Avoid auto-triggering heavy gates on every `synchronize` event.

---

## 6) Permissions policy for review automation

Claude/Bugbot workflows should default to:
- `contents: read`
- `pull-requests: write` (only if posting comments/reviews)
- `issues: write` (only if posting to issues)

Avoid giving write permissions unless the workflow must commit changes.

---

## 7) Bot identity + traceability

For any automation that comments or posts reviews:
- Use a consistent bot identity
- Include a machine-readable stamp in comments, e.g.:

`<!-- claude-review: sha=<HEAD_SHA> run=<RUN_ID> -->`

This enables the `policy-gate` workflow to verify freshness.

