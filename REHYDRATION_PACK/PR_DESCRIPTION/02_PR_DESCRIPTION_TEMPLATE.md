# PR Description Template

Use this template verbatim. Replace placeholders.

> **Rule:** The PR description must be **complete before requesting review**.
> If something is pending, include a **link to the pending run**.

---

## Standard template (risk:R1–R4)

**Run ID:** `RUN_YYYYMMDD_HHMMZ`  
**Agents:** A / B / C (or single agent)  
**Risk:** `risk:R#`  
**Claude gate:** (Haiku / Sonnet 4.5 / Opus 4.5)  

### 1) Summary
- 
- 
- 

### 2) Why
- **Problem / risk:**
- **Pre-change failure mode:**
- **Why this approach:**

### 3) Expected behavior & invariants
**Must hold (invariants):**
- 
- 
- 

**Non-goals (explicitly not changed):**
- 

### 4) What changed
**Core changes:**
- 

**Design decisions (why this way):**
- 

### 5) Scope / files touched
**Runtime code:**
- `path/to/file.py`

**Tests:**
- `path/to/test_file.py`

**CI / workflows:**
- `path/to/workflow.yml`

**Docs:**
- `docs/...`

### 6) Test plan
**Local:**
- `python scripts/run_ci_checks.py --ci`
- 

**CI:**
- (list relevant workflows)

### 7) Results & evidence
**CI:** <GitHub Actions run link>  
**Codecov:** <Codecov PR link or checks page link>  
**Bugbot:** <Bugbot comment link OR "pending" + link to the PR comment that triggers it>  

**Artifacts / proof:**
- `REHYDRATION_PACK/.../RUN_REPORT.md`
- `REHYDRATION_PACK/.../TEST_MATRIX.md`
- `REHYDRATION_PACK/.../EVIDENCE/...json`

### 8) Risk & rollback
**Risk rationale:** (why this is R#)
- 

**Failure impact:**
- 

**Rollback plan:**
- Revert this PR.
- Cleanup: (if applicable)

### 9) Reviewer + tool focus
**Please double-check:**
- 
- 

**Please ignore:**
- Generated registries / line number shifts unless CI fails.
- Rehydration pack artifacts except for referenced proof files.

---

## R0 compact template (docs-only)

**Risk:** `risk:R0` (docs only)  

### Summary
- 

### Why
- 

### Invariants
- No runtime code changes.
- No production behavior changes.

### Scope
- Docs: `docs/...`

### Evidence
- Doc hygiene: <CI link>
- Registry regen: `docs/_generated/...`

### Reviewer focus
- Confirm doc accuracy and that no code paths were modified.

