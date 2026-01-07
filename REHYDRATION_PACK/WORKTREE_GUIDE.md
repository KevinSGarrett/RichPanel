# Git Worktrees — Avoiding "Already Done" Loops

Last updated: 2026-01-06  
Status: Canonical

This guide explains what git worktrees are, how to use them correctly in Cursor, and why "No changes detected" happens when you're in the wrong folder.

---

## What are worktrees?

Git worktrees allow you to check out **multiple branches simultaneously** in different directories, all from the same repository.

### Main worktree
- **Location:** `C:\RichPanel_GIT` (the original repo clone)
- **Current branch:** Changes based on what you're working on
- **When to use:** Most work; this is your primary workspace

### Linked worktrees
- **Location:** Typically in `C:\Users\kevin\.cursor\worktrees\RichPanel_GIT\<id>`
- **Purpose:** Cursor creates these automatically when you switch between branches
- **Current branch:** Each worktree is locked to a specific branch
- **When to use:** Rarely; mainly for parallel work on different branches

### Check current worktrees
```powershell
git worktree list
```

Example output:
```
C:/RichPanel_GIT                                    c65edf6 [run/B21_checklist_alignment_20260106]
C:/Users/kevin/.cursor/worktrees/RichPanel_GIT/qvi  b4a4618 [run/B21_openai_routing_advisory_20260106]
C:/Users/kevin/.cursor/worktrees/RichPanel_GIT/rav  23f097d [run/B21_bugbot_fixes_20260106]
```

---

## How to pick the correct folder in Cursor

### Rule of thumb
**Always work in the main worktree unless you have a specific reason not to.**

Main worktree: `C:\RichPanel_GIT`

### How to verify you're in the right place

1. **Check Cursor's workspace root**
   - Look at the folder path in Cursor's title bar or sidebar
   - Should be: `C:\RichPanel_GIT`
   - Should NOT be: `C:\Users\kevin\.cursor\worktrees\...`

2. **Check current working directory in terminal**
   ```powershell
   pwd
   ```
   Should output: `C:\RichPanel_GIT`

3. **Check current branch**
   ```powershell
   git branch --show-current
   ```
   Should match the branch you intend to work on.

### If you're in the wrong worktree

**Symptoms:**
- Changes you make don't appear in `git status`
- CI runs show "No changes detected"
- You see commits that should already be merged
- Files you edited appear unchanged

**Fix:**
1. Close the Cursor window
2. Open Cursor and select the main worktree: `C:\RichPanel_GIT`
3. Verify you're on the correct branch with `git branch --show-current`
4. If not on the correct branch, switch with `git checkout <branch-name>`

---

## Why "No changes detected" happens

### Common causes

1. **Wrong worktree (most common)**
   - You edited files in `C:\RichPanel_GIT`
   - But Cursor opened a terminal in `C:\Users\kevin\.cursor\worktrees\RichPanel_GIT\xyz`
   - Solution: Always verify `pwd` before committing

2. **Wrong branch**
   - You edited files while on `main`
   - But you meant to be on `run/B21_my_feature`
   - Solution: Check `git branch --show-current` before starting work

3. **Already committed/merged**
   - The changes were already committed to the branch
   - Or the PR was already merged to main
   - Solution: Check `git log --oneline -5` and GitHub PR status

4. **Stashed or unstaged changes**
   - Changes exist but aren't staged
   - Solution: Check `git status` and `git stash list`

### Diagnostic checklist

When you see "No changes detected":

```powershell
# 1. Where am I?
pwd

# 2. What branch am I on?
git branch --show-current

# 3. What's the repo state?
git status

# 4. What was recently committed?
git log --oneline -5

# 5. What worktrees exist?
git worktree list

# 6. What's the PR status?
gh pr view <number>
```

---

## Worktree best practices

### DO
✅ Work in the main worktree (`C:\RichPanel_GIT`) for all normal work  
✅ Verify `pwd` before making commits  
✅ Check `git branch --show-current` before starting work  
✅ Clean up stale worktrees periodically with `git worktree prune`  
✅ Use `git worktree list` to see what branches are checked out where  

### DON'T
❌ Create worktrees manually unless you have a specific parallel-work need  
❌ Edit files in one worktree and commit from another  
❌ Assume Cursor's working directory matches the open folder  
❌ Ignore "Already up to date" messages from git pull  
❌ Work in Cursor-managed worktrees (`C:\Users\kevin\.cursor\worktrees\...`)  

---

## Cleaning up worktrees

### List all worktrees
```powershell
git worktree list
```

### Remove a specific worktree
```powershell
git worktree remove <path-to-worktree>
```

Example:
```powershell
git worktree remove C:/Users/kevin/.cursor/worktrees/RichPanel_GIT/qvi
```

### Prune deleted worktrees
If worktrees were deleted manually (not with `git worktree remove`):
```powershell
git worktree prune
```

### Check for prunable worktrees
```powershell
git worktree list
# Look for entries marked "prunable"
```

---

## Integration with GITHUB_STATE.md

The canonical list of:
- Which PRs are open/merged
- Which branches exist
- Which worktree has which branch checked out (if known)

lives in:
- `REHYDRATION_PACK/GITHUB_STATE.md`

Always update that file when:
- You create a new branch
- You open a PR
- You merge or close a PR
- You discover worktree state that affects merge/CI status

---

## Related documentation

- `REHYDRATION_PACK/GITHUB_STATE.md` — GitHub/PR/branch state
- `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md` — Git/GitHub operations policy
- `docs/08_Engineering/CI_and_Actions_Runbook.md` — CI contract and self-fix runbook

---

## Examples

### Example 1: Starting new work
```powershell
# 1. Ensure you're in main worktree
cd C:\RichPanel_GIT

# 2. Check current branch
git branch --show-current

# 3. Create and switch to feature branch
git checkout -b run/B22_my_feature

# 4. Verify
pwd  # Should be C:\RichPanel_GIT
git branch --show-current  # Should be run/B22_my_feature

# 5. Make changes and commit
# ...
git add .
git commit -m "feat: add my feature"
git push -u origin run/B22_my_feature
```

### Example 2: Recovering from wrong worktree
```powershell
# You realize you're in the wrong place
pwd
# Output: C:/Users/kevin/.cursor/worktrees/RichPanel_GIT/xyz

# 1. Close Cursor

# 2. Re-open Cursor, select folder: C:\RichPanel_GIT

# 3. Verify you're in the right place
pwd
# Output: C:\RichPanel_GIT

# 4. Check your branch
git branch --show-current

# 5. If wrong branch, switch
git checkout run/B22_my_feature

# 6. Continue work
```

### Example 3: Investigating "No changes detected"
```powershell
# CI says "No changes detected" but you made changes

# 1. Where am I?
pwd
# Expected: C:\RichPanel_GIT
# Actual: C:/Users/kevin/.cursor/worktrees/RichPanel_GIT/abc

# 2. Aha! Wrong worktree. Let me check what's there:
git status
# Output: nothing to commit, working tree clean

# 3. Switch to main worktree
cd C:\RichPanel_GIT

# 4. Check status there
git status
# Output: Changes not staged for commit:
#   modified: backend/src/...

# 5. Now commit from the correct location
git add .
git commit -m "fix: my changes"
```

---

## Summary

- **Main worktree** (`C:\RichPanel_GIT`) is your primary workspace
- **Linked worktrees** (`.cursor\worktrees\...`) should generally be avoided
- **Always verify** `pwd` and `git branch --show-current` before committing
- **"No changes detected"** usually means wrong worktree or wrong branch
- **Keep GITHUB_STATE.md updated** with PR/branch/worktree state

