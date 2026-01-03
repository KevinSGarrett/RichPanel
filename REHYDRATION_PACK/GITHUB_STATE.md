# GitHub State

Last updated: 2025-12-29 (Wave B00 — Build kickoff + Cursor agent takeover)

## Repo
- GitHub repo: `KevinSGarrett/RichPanel`
- URL: https://github.com/KevinSGarrett/RichPanel
- Default branch: `main`

## Local workspace
- Preferred local root: `C:\RichPanel_GIT`
- Legacy/non-git folder observed earlier: `C:\RichPanel` (treat as backup; avoid doing work there)

## Merge settings (repo-level)
Configured so history is consistent and PRs stay bounded per run:
- Merge commits: **enabled (single allowed method)**
- Squash merge: **disabled**
- Rebase merge: **disabled**
- Auto-delete branch on merge: **enabled**

## Branch protection: `main`
Configured so merges are gated by CI and conversations are resolved:
- Require pull requests before merge: **true** (merge-commit only)
- Required status check: **`validate`** (strict/up-to-date: **true**)
- Require conversation resolution: **true**
- Enforce for admins: **true**
- Force pushes: **disabled**
- Deletions: **disabled**
- PR reviews: **enabled** with approvals required: **0** (single-owner automation-friendly; bot-friendly but still enforces conversation resolution)

## How to verify (PowerShell)
```powershell
# Repo merge settings
gh api repos/KevinSGarrett/RichPanel --jq '{allow_merge_commit,allow_squash_merge,allow_rebase_merge,delete_branch_on_merge}'

# Branch protection
gh api repos/KevinSGarrett/RichPanel/branches/main/protection --jq '{required_status_checks,required_pull_request_reviews,enforce_admins,required_conversation_resolution,allow_force_pushes,allow_deletions}'

# Latest CI runs (shell-safe; no jq piping)
gh run list -L 5 --workflow CI --json databaseId,conclusion,event,headBranch,displayTitle --jq '.[] | "\(.databaseId) | \(.conclusion) | \(.event) | \(.headBranch) | \(.displayTitle)"'
```

## PR merge process (non-negotiable)
- Always use `gh pr merge --auto --merge --delete-branch`.
- Wait for `validate` to pass; auto-merge queues the merge commit and deletes the branch on success.
- Manual merges in the UI or CLI are disallowed because they bypass the hardened loop.

## Notes
- The required status check name is **`validate`** (the job name), not `CI`.
- If running `python scripts/run_ci_checks.py --ci` locally, keep the tree clean (or ensure scratch files are ignored).
