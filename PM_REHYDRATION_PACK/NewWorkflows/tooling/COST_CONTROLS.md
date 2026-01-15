# Cost controls and “don’t run gates on tiny commits”

This document is the practical playbook that prevents:
- Bugbot on every micro-commit
- Codecov upload on every tiny diff
- Claude review spam / token burn

---

## 1) The root problem

In GitHub, every push to a PR triggers workflows.
If agents push every tiny step, you get:
- constant CI runs
- constant coverage uploads
- constant “expected checks” noise
- wasted compute and AI tokens

---

## 2) The core solution

### 2.1 Make “push” a deliberate action
Cursor agents should:
- commit locally as much as needed
- push only when:
  - local CI-equivalent is green
  - there is a coherent diff
  - the PR is ready for CI feedback

This is the single biggest lever.

### 2.2 Heavy gates run only on “gates:ready”
Bugbot and Claude review should run:
- once per stable PR state
- not on every synchronize event

---

## 3) Tool-by-tool cost controls

### 3.1 Bugbot
- Trigger only after CI green.
- Rerun only when PR becomes stale (new commits after review).
- Avoid WIP bugbot runs.

### 3.2 Codecov
- Split CI into:
  - Fast CI (no coverage upload)
  - Coverage gate (upload to Codecov)
- Trigger coverage gate only on:
  - label `gates:ready`, or
  - R2+ PRs, or
  - nightly schedule

### 3.3 Claude review
- Trigger only when PR is stable:
  - CI green
  - `gates:ready` applied
- Enforce diff size limits:
  - if > N files or > X LOC, split review into chunks
- Use cheaper model for R2; stronger model for R3/R4
- Constrain output to JSON to reduce token length

---

## 4) Staleness automation (prevents rerun spam)

Implement a workflow that:
- on `pull_request` synchronize:
  - remove `gates:passed`
  - add `gates:stale`

Then gates run only when:
- PM/agent re-adds `gates:ready`

This turns gate reruns into an explicit, controlled action.

---

## 5) Concurrency controls (avoid parallel waste)

Set concurrency on heavy workflows:

```yaml
concurrency:
  group: claude-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

This ensures only the latest request runs.

---

## 6) Observability and budgeting

Track:
- number of Bugbot runs per week
- Claude tokens spent per PR
- CI minutes used per PR

Adjust:
- when gates run
- which PR sizes are allowed
- model selection thresholds

---

## 7) Recommended defaults (starting point)

- R0: no heavy gates
- R1: heavy gates only if “critical zones” or uncertainty
- R2: run Bugbot + Claude once on `gates:ready`
- R3/R4: run Bugbot + Claude + E2E; require re-run on staleness

