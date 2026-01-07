# GitHub State

Last updated: 2026-01-07 (Merge hygiene + single source of truth status refresh)

## Repo
- GitHub repo: `KevinSGarrett/RichPanel`
- URL: https://github.com/KevinSGarrett/RichPanel
- Default branch: `main`

## Local workspace
- Preferred local root: `C:\RichPanel_GIT` (main worktree)
- Legacy/non-git folder observed earlier: `C:\RichPanel` (treat as backup; avoid doing work there)

### Worktree awareness
Git worktrees allow multiple branches to be checked out simultaneously in different directories.

**Main worktree:**
- Path: `C:\RichPanel_GIT`
- Purpose: Primary workspace for all normal work

**Linked worktrees (Cursor-managed):**
- Path pattern: `C:\Users\kevin\.cursor\worktrees\RichPanel_GIT\<id>`
- Purpose: Cursor creates these automatically; **avoid working in these**
- Risk: Easy to edit files in main worktree but commit from wrong worktree → "No changes detected"

**Always verify before committing:**
```powershell
pwd  # Should be C:\RichPanel_GIT
git branch --show-current  # Should match your intended branch
```

See `REHYDRATION_PACK/WORKTREE_GUIDE.md` for detailed guidance.

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

## Active PRs (as of 2026-01-07)

| PR # | Title | Branch | State | CI (validate) | Worktree (if known) | Notes |
|------|-------|--------|-------|---------------|---------------------|-------|
| #51 | B21: Align checklist with reality + mypy/Cursor noise hardening | `run/B21_checklist_alignment_20260106` | OPEN | ✅ pass | Unknown | Validate run: `https://github.com/KevinSGarrett/RichPanel/actions/runs/20769206306` |
| #50 | feat(automation): OpenAI routing classifier in advisory mode | `run/B21_openai_routing_advisory_20260106` | OPEN | ✅ pass | `C:/Users/kevin/.cursor/worktrees/RichPanel_GIT/qvi` (linked) | Validate run: `https://github.com/KevinSGarrett/RichPanel/actions/runs/20770618716` |
| #49 | Fix fraud routing and Shopify order fields | `run/B21_bugbot_fixes_20260106` | OPEN | ⚠️ missing | `C:/Users/kevin/.cursor/worktrees/RichPanel_GIT/rav` (linked; local head diverged) / `C:/Users/kevin/.cursor/worktrees/RichPanel_GIT/zbl` (linked; contains PR head `07ec6d4`) | No `validate` run is recorded on the PR (only Bugbot). PR head is `07ec6d4` (`origin/run/B21_bugbot_fixes_20260106`), but local `run/B21_bugbot_fixes_20260106` is currently at `23f097d` (diverged). If you need CI, push a no-op commit to `run/B21_bugbot_fixes_20260106` to trigger CI on this branch. |

### Recent merged PRs
| PR # | Title | Branch | Merged date |
|------|-------|--------|-------------|
| #54 | Fix order status fallback draft reply | `fix/missing-draft-reply` | 2026-01-07 |
| #53 | ops/set runtime flags | `ops/set-runtime-flags` | 2026-01-07 |
| #41 | docs: refresh Richpanel UI configuration runbook | `docs/richpanel-runbook-refresh` | 2026-01-07 |
| #40 | docs: PowerShell-safe ops + extensions not CLI | `agent3-ps-safe-ops` | 2026-01-07 |
| #35 | Docs: refresh Richpanel config runbook (no UI changes) | `docs/richpanel-config-runbook` | 2026-01-07 |
| #52 | docs: Worktree guide + agent summary protocol (Agent 2) | `docs/worktree-summary-protocol-20260106` | 2026-01-07 |
| #48 | fix(routing): Correct fraud vs chargeback routing + add Shopify fields for delivery estimates | `run/B21_bugbot_fixes_184913` | 2026-01-07 |

**How to refresh this table:**
```powershell
# List recent PRs with state
gh pr list --state all --limit 10 --json number,title,state,headRefName

# Check worktree state
git worktree list
```

---

## Notes
- The required status check name is **`validate`** (the job name), not `CI`.
- If running `python scripts/run_ci_checks.py --ci` locally, keep the tree clean (or ensure scratch files are ignored).
- **Before committing:** Always verify you're in the correct worktree with `pwd` and on the correct branch with `git branch --show-current`.
- See `REHYDRATION_PACK/WORKTREE_GUIDE.md` for troubleshooting "No changes detected" issues.
