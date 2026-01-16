# Gate matrix (what runs, when, and how it is verified)

This document is the **source of truth** for:

- which gates are required for each risk level
- when those gates should run (to avoid waste)
- what evidence is required to prove the gates were satisfied
- how staleness is handled

---

## 1) Gate definitions

### 1.1 CI / `validate` (required check)
- Meaning: repo baseline checks are green (lint, unit tests, basic build)
- Source of truth: GitHub required status check `validate` (plus local `python scripts/run_ci_checks.py --ci` evidence)

### 1.2 Codecov
- Meaning: coverage signals did not regress unacceptably
- Primary signals:
  - **patch coverage** (coverage on changed lines)
  - **project coverage** (overall)
- Source of truth:
  - Codecov PR checks (`codecov/patch`, `codecov/project`) *if enabled*
  - coverage artifacts in CI (fallback)

### 1.3 Bugbot (Cursor)
- Meaning: a second set of eyes has flagged likely defects / edge cases
- Source of truth:
  - A Bugbot PR comment exists and has been triaged
  - Findings are recorded in run report (even if “no findings”)

### 1.4 Claude review (Semantic Review Agent)
- Meaning: semantic/correctness/security review of the diff
- Source of truth:
  - A Claude review comment / check exists with a structured verdict
  - Any “CONCERNS/FAIL” items are either fixed or waived

### 1.5 E2E proof (conditional)
- Meaning: change was validated in a way that approximates production behavior
- Source of truth:
  - test evidence folder + logs + screenshots (if UI) or recorded outputs

---

## 2) Gate requirements by risk level

### 2.1 Matrix (requirements)

| Risk | CI validate | Local CI-equiv evidence | Codecov | Bugbot | Claude review | E2E proof |
|------|-------------|-------------------------|---------|--------|--------------|----------|
| R0 docs | Optional* | Optional* | Not required | Not required | Not required | Not required |
| R1 low | Required | Required | Advisory (patch) | Optional** | Optional | Conditional |
| R2 med | Required | Required | **Required (patch)** | **Required** | **Required** | Conditional |
| R3 high | Required | Required | **Required (patch)** + project target | **Required** (stale-rerun) | **Required** (stale-rerun) + security prompt | **Required if outbound/automation** |
| R4 critical | Required | Required | **Required (patch + project)** | **Required** | **Required** + double-review strategy | **Required** |

\* R0 docs: if CI is mandatory due to repo settings, it still must be green, but Codecov/Bugbot/Claude are waived by default.  
\** Bugbot becomes required in R1 if critical zones are touched.

---

## 3) When gates should run (cost-aware strategy)

### 3.1 Two-phase approach (recommended)

**Phase A: Build & stabilize**
- Cursor agent iterates locally.
- Runs `python scripts/run_ci_checks.py --ci` locally until green.
- Commits locally as needed.
- Pushes to GitHub only when the diff is “coherent” (reduces CI/Codecov runs).

**Phase B: Gate execution**
- When CI is green and the PR is stable, apply label: `gates:ready`.
- Heavy gates run once per stable PR state:
  - Bugbot (if required)
  - Claude review (if required)
  - Coverage gating (if required)

This is how you avoid running Bugbot/Claude on every micro-commit.

---

## 4) Staleness (the fail-safe)

### 4.1 What makes gates stale?
If the PR receives new commits after:
- Bugbot review output
- Claude review output
- “gates:passed” label

Then gates are stale.

### 4.2 Policy rule
A PR with stale gates:
- must be labeled `gates:stale`
- must not be merged until gates are re-run and `gates:passed` is restored

### 4.3 Implementation (recommended automation)
- A lightweight workflow runs on `pull_request` `synchronize` events.
- It removes `gates:passed` and applies `gates:stale`.
- Another workflow (or the gate workflow itself) adds `gates:passed` only when:
  - required gates succeed
  - staleness checks are satisfied

This converts “policy” into a machine-enforced state machine.

---

## 5) Evidence checklist per gate

### 5.1 CI evidence
Required in run report:
- local command: `python scripts/run_ci_checks.py --ci`
- outcome (PASS)
- link to CI run or `gh pr checks` output snippet

### 5.2 Codecov evidence
Required in run report:
- Codecov patch status: PASS/FAIL/N/A
- Codecov project status: PASS/FAIL/N/A
- If N/A, state why (docs-only, or Codecov skipped by policy)
- If FAIL, include:
  - what coverage dropped
  - remediation or waiver

### 5.3 Bugbot evidence
Required in run report:
- Bugbot triggered: yes/no
- Link to Bugbot comment
- Findings summary + triage:
  - fixed
  - false positive (with justification)
  - deferred (requires waiver)

### 5.4 Claude evidence
Required in run report:
- Claude triggered: yes/no
- Link to Claude output (comment or check)
- Verdict: PASS/CONCERNS/FAIL
- Actions taken (fixes or waiver)

### 5.5 E2E evidence
Required in run report if E2E required:
- what environment
- what scenario
- artifacts (logs/screenshots)
- outcome

---

## 6) Merge readiness rule

A PR is merge-ready only when:
- CI required checks green
- required gates satisfied and non-stale
- waivers documented (if any)
- AM score ≥ 95 and references evidence

