# Branch Protection and Merge Settings

Last verified: 2025-12-29 — Wave B00 (Build kickoff + Cursor agent takeover).
Status: Canonical

This document defines the **required GitHub repository settings** that make this project safe to run with:
- ChatGPT as PM
- 3 Cursor agents (A/B/C)

These settings prevent:
- stale `main`
- accidental destructive changes to critical docs/structure
- merge conflicts and branch explosion
- bypassing CI

Related:
- `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`
- `docs/08_Engineering/Multi_Agent_GitOps_Playbook.md`
- `docs/08_Engineering/CI_and_Actions_Runbook.md`

---

## 1) Required repo settings (Settings → General → Pull Requests)

### Merge methods
**Required (current state)**
- ✅ **Allow merge commits** — the only enabled merge strategy
- ⛔ **Squash merging** — disabled
- ⛔ **Rebase merging** — disabled

Rationale:
- Merge commits keep a clear audit trail per `RUN_ID`.

### Auto-delete branches
**Required**
- ✅ **Automatically delete head branches**

Rationale:
- Prevents “branch explosion” (50–100 remote branches).

---

## 2) Required branch protection rule for `main`

Path: **Settings → Branches → Branch protection rules → Add rule**

### Rule target
- Branch name pattern: `main`

> Source of truth for the rule snapshot: `branch_protection_main.json`

### Pull request requirement
**Required (current state)**
- ✅ Require a pull request before merging
- ✅ Require approvals: **0** (automation-friendly; CI + conversation resolution act as the guardrails)
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require conversation resolution before merging

### Status checks
**Required**
- ✅ Require status checks to pass before merging
- ✅ Required checks must include the repo CI workflow/job

This repo’s baseline workflow + job:
- `.github/workflows/ci.yml` → workflow name: `CI`, job: **`validate`** (strict/up-to-date = **true**)

Important:
- GitHub only lets you select required checks after the workflow has run at least once.
- Create a small PR to trigger CI, then return here and select the check(s) from the list.

Recommended
- ✅ Require branches to be up to date before merging

### Admin / destructive controls
**Required**
- ✅ Include administrators
- ⛔ Allow force pushes: **OFF**
- ⛔ Allow deletions: **OFF**

Rationale:
- Agents must not be able to bypass the same safety gates as humans.

---

## 3) Verification checklist (do once)

1) Create a PR from a run branch (example): `run/RUN_20251229_2315Z` → `main`
2) Confirm the PR cannot merge until:
   - `CI / validate` (or the equivalent check name in your repo) is green
   - approvals are present
3) Merge using **merge commit**
4) Confirm the head branch was auto-deleted

---

## 4) Optional automation (advanced)

If your token has **admin** permissions, you can set protection via API.
This is optional; the safest path is to configure in the GitHub UI.

Example (outline only):
- Use `gh api` with `repos/{owner}/{repo}/branches/main/protection`
- Apply:
  - required status checks
  - required PR reviews
  - force push + deletion disabled

If you automate this, record:
- the exact command(s)
- the resulting configuration
in `docs/00_Project_Admin/Decision_Log.md`.
