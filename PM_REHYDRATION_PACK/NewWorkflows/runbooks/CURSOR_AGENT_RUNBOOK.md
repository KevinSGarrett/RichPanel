# Runbook — Cursor Agents (A/B/C)

This runbook is the operational standard for agents implementing changes.

The goal:
- produce coherent PRs
- minimize wasted CI/Codecov runs
- run Bugbot/Claude only when it matters
- leave behind complete evidence so AM can score ≥ 95

---

## 1) Before you code

### 1.1 Read the objective + stop conditions
If unclear, assume:
- keep diff minimal
- do not scope creep

### 1.2 Create/checkout branch
Preferred:
- `run/<RUN_ID>_<short_slug>`

---

## 2) Implementation loop (local first)

### 2.1 Make changes
- keep changes focused
- avoid huge refactors

### 2.2 Run local CI-equivalent
Required before push:
```bash
python scripts/run_ci_checks.py --ci
```

If it fails:
- fix
- rerun
- repeat until PASS

### 2.3 Commit locally
You may create multiple local commits.

### 2.4 Push policy (critical)
Do not push every micro-change.
Push only when:
- local CI-equivalent is PASS
- you have a coherent change set

Rationale:
- every push triggers CI and Codecov

---

## 3) PR creation

### 3.1 Create PR (GitHub CLI preferred)
Example:
```bash
gh pr create --fill --base main --head <branch>
```

### 3.2 Apply required labels
- risk label (exactly one)
- domain labels (optional)

Example:
```bash
gh pr edit <PR#> --add-label "risk:R2-medium"
```

---

## 4) Gate execution (only after CI green)

### 4.1 Wait for CI `validate` to pass
Check:
```bash
gh pr checks <PR#>
```

### 4.2 Apply `gates:ready`
```bash
gh pr edit <PR#> --add-label "gates:ready"
```

### 4.3 Trigger Bugbot (if required)
Your repo has `bugbot-review.yml` (workflow_dispatch). Trigger via CLI:

```bash
gh workflow run bugbot-review.yml -f pr_number=<PR#> -f comment_body="@cursor review"
```

### 4.4 Trigger Claude review (if required)
Depends on implementation:
- Path 1 (Claude Code Action): label triggers or `@claude /review`
- Path 2 (custom): `gh workflow run claude-review.yml -f pr_number=<PR#>`

---

## 5) After gates run

### 5.1 Triage findings
- Fix blockers
- Justify false positives
- Use waiver template if deferring

### 5.2 Update run report
Run report must include:
- CI evidence
- Codecov summary
- Bugbot link + summary
- Claude link + verdict + actions

---

## 6) Merge readiness

Do not merge directly.
PM will merge using auto-merge once:
- CI green
- gates satisfied
- AM score ≥ 95

---

## 7) Common mistakes (avoid)

- pushing repeatedly during local iteration
- running Bugbot/Claude before CI is green
- not recording evidence links
- leaving gates stale after additional commits

