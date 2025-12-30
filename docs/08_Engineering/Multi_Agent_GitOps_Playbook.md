# Multi‑Agent GitOps Playbook

Last updated: 2025-12-29  
Status: Canonical

This playbook explains the **exact Git/GitHub operating model** for a project built by:

- ChatGPT (PM) in a browser window
- 3 Cursor agents (A/B/C) doing **all** implementation work

Goals:
- avoid merge conflicts
- keep branch counts low
- keep `main` continuously updated
- keep CI green, with agents self-fixing failures
- prevent accidental deletions of critical docs/structure

> Policy reference: `docs/98_Agent_Ops/Policies/POL-GH-001__GitHub_and_Repo_Operations_Policy.md`

Required repo settings:
- `docs/08_Engineering/Branch_Protection_and_Merge_Settings.md`

---

## 1) Terminology

- **RUN_ID**: the identifier for a coordinated batch of agent work (one PM cycle)
- **Run branch**: `run/<RUN_ID>`
- **Agent branches** (parallel mode only): `run/<RUN_ID>-A`, `run/<RUN_ID>-B`, `run/<RUN_ID>-C`
- **Integrator**: the agent responsible for merging to `main`, fixing CI, and deleting branches

---

## 2) Decision: sequential vs parallel

### Sequential mode (default)
Use when:
- agents touch shared docs
- agents touch shared schemas/config
- risk of overlap is non-trivial

Outcome:
- 1 branch per run (`run/<RUN_ID>`)
- very low merge conflict probability

### Parallel mode (only when scopes are disjoint)
Use when:
- PM can guarantee disjoint file/path scopes
- each agent edits separate modules/files

Outcome:
- 3 agent branches + 1 run branch (max 4)
- Integrator merges agent branches into run branch

---

## 3) Run kickoff checklist (PM responsibility)

PM must create/update:
- `REHYDRATION_PACK/RUNS/<RUN_ID>/RUN_META.md`
- `REHYDRATION_PACK/RUNS/<RUN_ID>/GIT_RUN_PLAN.md`

**GIT_RUN_PLAN.md** must include:
- mode: sequential or parallel
- integrator: A/B/C
- branch names
- merge order
- allowed paths + locked paths for each agent
- “protected paths” reminder

---

## 4) Commands: sequential mode

All agents work on the same branch.

### Agent A (first)
```bash
git checkout main
git pull --rebase
git checkout -b run/<RUN_ID>
# implement tasks
python scripts/run_ci_checks.py
git add -A
git commit -m "RUN:<RUN_ID> A <short summary>"
git push -u origin run/<RUN_ID>
```

### Agent B (second)
```bash
git checkout run/<RUN_ID>
git pull --rebase
# implement tasks
python scripts/run_ci_checks.py
git add -A
git commit -m "RUN:<RUN_ID> B <short summary>"
git push
```

### Agent C (third)
Same pattern as Agent B.

### Integrator merge
Integrator merges to main and cleans branches (see section 6).

---

## 5) Commands: parallel mode

Each agent works on their own branch.

### Each agent
```bash
git checkout main
git pull --rebase
git checkout -b run/<RUN_ID>-A   # or -B / -C
# implement tasks (ONLY within assigned scope)
python scripts/run_ci_checks.py
git add -A
git commit -m "RUN:<RUN_ID> A <short summary>"
git push -u origin run/<RUN_ID>-A
```

### Integrator integrates
```bash
git checkout main
git pull --rebase
git checkout -b run/<RUN_ID>
git merge --no-ff run/<RUN_ID>-A
git merge --no-ff run/<RUN_ID>-B
git merge --no-ff run/<RUN_ID>-C
python scripts/run_ci_checks.py
git push -u origin run/<RUN_ID>
```

Then merge to main (section 6).

---

## 6) Merging to main + branch cleanup (Integrator)

### Preferred: PR based (with `gh`)
```bash
gh pr create --base main --head run/<RUN_ID> --fill
gh pr merge --merge --delete-branch
```

Delete agent branches:
```bash
git push origin --delete run/<RUN_ID>-A
git push origin --delete run/<RUN_ID>-B
git push origin --delete run/<RUN_ID>-C
```

### Fallback: direct merge
```bash
git checkout main
git pull --rebase
git merge --no-ff run/<RUN_ID>
python scripts/run_ci_checks.py
git push origin main
git push origin --delete run/<RUN_ID>
```

### Record “main updated”
Update:
- `REHYDRATION_PACK/GITHUB_STATE.md` (commit hash + branch cleanup record)

---

## 7) What to do if CI fails

Follow:
- `docs/08_Engineering/CI_and_Actions_Runbook.md`

Minimum: open issue entry + fix + add test evidence.

---

## 8) What *not* to do
- Do not create ad-hoc branches.
- Do not force-push to main.
- Do not delete protected docs/packs.
- Do not merge without running `scripts/run_ci_checks.py`.
