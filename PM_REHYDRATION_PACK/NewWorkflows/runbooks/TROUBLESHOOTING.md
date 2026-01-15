# Troubleshooting: Bugbot + Codecov + Claude review

This runbook is for when gates fail due to tooling rather than code.

---

## 1) CI (`validate`) is failing

### Symptoms
- Required check red
- PR blocked from merge

### Fix
- Run local CI-equivalent:
  - `python scripts/run_ci_checks.py --ci`
- Fix failures
- Re-push coherent commit

---

## 2) Codecov is failing

### A) Coverage upload failed
**Possible causes**
- missing/invalid Codecov token
- network error
- Codecov outage

**Fix**
- Re-run workflow
- Confirm `CODECOV_TOKEN` secret is present (if required)
- If outage: apply waiver and store coverage artifact + summary

### B) Patch coverage failed
**Fix**
- Add tests for changed logic
- Avoid excluding files incorrectly
- If change is non-testable:
  - justify and apply waiver
  - add alternate validation evidence

---

## 3) Bugbot didn’t respond

### Causes
- Bugbot quota exhausted
- Cursor service delay
- comment trigger not recognized

### Fix
- Ensure the trigger comment matches your configured phrase (e.g., `@cursor review`).
- Re-trigger via workflow dispatch.
- If quota/exhausted:
  - waiver + Claude semantic review + extra tests

---

## 4) Claude review workflow fails

### A) Authentication error
- Verify `ANTHROPIC_API_KEY` secret exists
- Verify the workflow is allowed to access secrets (fork PRs cannot)

### B) Diff too large
- Chunk diff by:
  - limiting to critical files
  - splitting PR
  - running multiple passes and combining results in run report

### C) Claude output not valid JSON (custom workflow)
- Strengthen prompt: “Return ONLY JSON”
- Add a fallback parser:
  - find first JSON fenced block
  - re-ask Claude to reformat

---

## 5) Gates are stale

### Symptom
- `gates:stale` label present
- AM refuses ≥ 95

### Fix
- Re-run required gates (Bugbot/Claude/coverage) after last commit
- Re-apply `gates:passed` label only after completion

---

## 6) Status checks missing / stuck “Expected”

### Cause
- Branch protection requires checks that are not being produced
- Workflows skipped due to path filters

### Fix
- Align required checks with actual workflow names
- Prefer required checks: `validate` + `policy-gate`

