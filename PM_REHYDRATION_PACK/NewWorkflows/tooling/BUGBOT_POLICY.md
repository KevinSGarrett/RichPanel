# Bugbot policy (Cursor)

Bugbot is a PR review gate that catches:
- logic errors and edge cases
- missing null checks / assumptions
- error handling gaps
- suspicious patterns

Bugbot is **not** a substitute for:
- tests
- threat modeling
- coverage discipline
- explicit design review

It is a “high-signal lead generator” that must be triaged.

---

## 1) How Bugbot is triggered in RichPanel today

Your repo already includes a workflow:

- `.github/workflows/bugbot-review.yml`

That workflow is a **manual trigger** (`workflow_dispatch`) that posts a PR comment (default body: `@cursor review`) to trigger Bugbot.

This is a good foundation because:
- you can choose when to run it (avoids waste on tiny commits)
- you can run it only for R2+ risk PRs

---

## 2) When Bugbot must be run (policy)

### Required
Bugbot is **required** when:
- risk is **R2+**, OR
- risk is R1 but the PR touches critical zones (see risk policy)

### Optional
Bugbot is optional when:
- risk is R1 and changes are localized and non-critical

### Not required
Bugbot is not required when:
- risk is R0 docs-only

---

## 3) When to run Bugbot (timing)

To avoid running it on every micro-commit:

1) Stabilize the PR locally (run local CI-equivalent).
2) Push only “coherent” commits.
3) Wait for CI `validate` to pass.
4) Apply label `gates:ready`.
5) Trigger Bugbot once.

### Rerun rules
Rerun Bugbot when:
- new commits change logic after Bugbot ran (staleness)
- the diff changes materially (large delta, new files, new flows)
- PM/AM flags uncertainty

---

## 4) How to trigger Bugbot (operational)

### Option A — via GitHub UI (workflow_dispatch)
- Actions → “Bugbot Review Trigger”
- Input: PR number
- (Optional) comment body

### Option B — via GitHub CLI (preferred for agents)
```bash
gh workflow run bugbot-review.yml -f pr_number=<PR_NUMBER> -f comment_body="@cursor review"
```

---

## 5) Findings policy (what is blocking)

Bugbot findings are classified into:

### Blocking (must fix or waive)
- correctness bugs (wrong branch, wrong value, missing update)
- concurrency / idempotency issues
- broken error handling / retries
- data corruption potential
- security or privacy issues
- missing validation for external inputs

### Non-blocking (should fix if cheap)
- style/readability
- low-confidence speculative warnings
- refactor suggestions without correctness impact

---

## 6) Triage workflow (required)

Bugbot output must be triaged in the run report:

For each finding:
- ✅ Fixed (link to commit or code change)
- ✅ False positive (explain why)
- ✅ Deferred (requires waiver + follow-up issue)

If Bugbot produces **no findings**, record:
- “No findings (triaged)”
- Link to comment

---

## 7) Cost controls

To prevent waste:
- Never run Bugbot before the PR is stable.
- Avoid running Bugbot on WIP or “half-built” branches.
- Use the staleness label workflow to prevent unnecessary reruns:
  - rerun only when stale, not on every commit.

---

## 8) Failure modes and fallback strategy

### Bugbot quota exceeded / unavailable
Allowed waiver reason (R2+ requires alternate evidence):
- Run Claude semantic review + security prompt (if R3+)
- Run additional targeted tests
- Record waiver

See: `policies/03_WAIVERS_AND_EXCEPTIONS.md`

