# End-to-end example (R2 medium PR)

This example shows how a typical medium-risk PR should flow without wasting Bugbot/Codecov/Claude cycles on tiny commits.

---

## Scenario
- RUN_ID: `RUN_20260115_1800Z`
- Change: adjust routing logic for a webhook
- Risk: `risk:R2-medium`
- Gates required: CI + Codecov patch + Bugbot + Claude semantic review

---

## Step 1 — Agent works locally

1) Implement change
2) Run local CI-equivalent until PASS:
```bash
python scripts/run_ci_checks.py --ci
```

3) Commit locally as needed (multiple commits ok)

4) Push only when coherent:
```bash
git push -u origin run/RUN_20260115_1800Z_webhook_routing_fix
```

---

## Step 2 — Create PR and apply labels

```bash
gh pr create --fill
gh pr edit <PR#> --add-label "risk:R2-medium"
```

---

## Step 3 — Wait for CI

```bash
gh pr checks <PR#>
```

Once `validate` is green:

```bash
gh pr edit <PR#> --add-label "gates:ready"
```

---

## Step 4 — Run gates

### Bugbot
```bash
gh workflow run bugbot-review.yml -f pr_number=<PR#> -f comment_body="@cursor review"
```

### Claude (example: workflow_dispatch custom)
```bash
gh workflow run claude-review.yml -f pr_number=<PR#>
```

---

## Step 5 — Triage findings and update run report

Run report must include:
- CI link + local run evidence snippet
- Codecov patch result
- Bugbot permalink + summary
- Claude permalink + verdict + actions taken

---

## Step 6 — Merge readiness

AM verifies:
- score ≥ 95
- gates are not stale
- required evidence is present

PM merges:
```bash
gh pr merge --auto --merge --delete-branch <PR#>
```

---

## Why this avoids waste

- You did not run Bugbot/Claude during local iteration.
- You did not push micro-commits repeatedly.
- Heavy gates ran only once, on a stable diff.

