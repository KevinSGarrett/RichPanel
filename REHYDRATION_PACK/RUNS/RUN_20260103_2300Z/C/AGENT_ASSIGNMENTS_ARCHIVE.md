# Archive — prior `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` content

This file preserves the previous contents of `REHYDRATION_PACK/06_AGENT_ASSIGNMENTS.md` before it was converted to **prompt-only** format.

---

# Cursor Agent Assignments

Wave: **WAVE_B00 — Build Kickoff (Cursor takeover)**

Owner intent: **minimize manual work**. From this point forward:
- Cursor agents do the GitOps (branches/commits/PRs/merges) and repo changes.
- The human only supplies required external inputs (credentials, business decisions) and runs Cursor.

## Global rules (all agents)
- **Never push directly to `main`.** Always use a PR.
- Create branches as: `run/<SHORT>_<YYYYMMDD_HHMM>` (example: `run/B00_PACKSYNC_20251230_1040`).
- Before pushing: run `python scripts/run_ci_checks.py`.
- Merge via standard path; if checks are pending, use auto-merge:
  - `gh pr merge --auto --merge --delete-branch`
- If `run_ci_checks.py --ci` reports dirty generated files, commit the regen outputs.

## Sequence
To avoid merge conflicts, run agents **sequentially** in this order:
1. Agent 1 → merge PR
2. Agent 2 → merge PR
3. Agent 3 → merge PR

---

## Agent 1 — Pack Sync + GitHub Settings Documentation

### Goal
Bring “living docs” and rehydration packs into alignment with the now-stable GitHub + CI state and mark the repo as build-ready.

### Tasks
1. Update:
   - `REHYDRATION_PACK/MODE.yaml` (mode/build + current wave)
   - `REHYDRATION_PACK/GITHUB_STATE.md`
   - `REHYDRATION_PACK/FOUNDATION_STATUS.md`
   - `REHYDRATION_PACK/WAVE_SCHEDULE*.md`
   - `REHYDRATION_PACK/LAST_*.md`
2. Update `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md` so it matches the actual GitHub configuration (required check is `validate`, merge-commit-only, delete-branch-on-merge, etc.).
3. Run `python scripts/run_ci_checks.py` and commit regen outputs.
4. PR + merge.

### Acceptance criteria
- `python scripts/run_ci_checks.py` passes locally.
- GitHub Actions `validate` is green on the PR.

---

## Agent 2 — Sprint 0: Access + Secrets Inventory

### Goal
Unblock Build Mode by capturing the *minimum required* external access/credentials needed for upcoming sprints.

### Tasks
1. Create or update a single source of truth doc (suggested):
   - `docs/06_Security_Secrets/Access_and_Secrets_Inventory.md`
2. Include:
   - AWS account/role requirements (dev/prod separation assumptions)
   - Richpanel API key(s) + where stored
   - ShipStation / marketplace credentials
   - Email provider (SES/SMTP/etc.)
   - Any webhook endpoints + signing secrets
3. Update `config/.env.example` **only** with safe, non-secret variables (leave secrets empty).
4. Run `python scripts/run_ci_checks.py` and commit.
5. PR + merge.

### Acceptance criteria
- No secrets committed.
- The new doc is referenced from `docs/INDEX.md` if appropriate.
- `python scripts/run_ci_checks.py` passes.

---

## Agent 3 — Developer Ergonomics for Build Mode

### Goal
Make Build Mode runs “one command” and PowerShell-friendly, reducing manual friction for operators.

### Tasks (choose the smallest that helps)
1. Add a PowerShell helper: `scripts/ci.ps1` that runs `python scripts/run_ci_checks.py` and prints the git status on failure.
2. Add a PowerShell helper: `scripts/gh_ci_latest.ps1` that prints the latest CI run id + conclusion using `gh run list --json ... --jq ...` (no fragile quoting).
3. Ensure `.gitignore` covers local scratch artifacts (e.g., `branch_protection_*.json`, `_tmp_branch_protection_*.json`) so CI cleanliness checks aren’t tripped.
4. Run `python scripts/run_ci_checks.py` and commit.
5. PR + merge.

### Acceptance criteria
- Helpers run on Windows PowerShell.
- `python scripts/run_ci_checks.py` passes.

---

## Human inputs needed soon (not for agents)
- AWS account/role setup (or confirm you want local-only scaffolding first)
- Richpanel API key(s)
- Marketplace/ShipStation credentials
- Confirm whether `C:\RichPanel_GIT` becomes the canonical workspace path


