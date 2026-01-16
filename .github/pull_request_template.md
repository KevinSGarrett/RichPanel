# Summary

- RUN_ID: `RUN_<YYYYMMDD>_<HHMMZ>`
- Task IDs: `TASK-###, ...`

## Risk classification (required)

Select exactly one and apply the matching PR label:

- [ ] `risk:R0-docs` — docs/comments only, no runtime impact
- [ ] `risk:R1-low` — low risk (minor behavior changes, non-critical paths)
- [ ] `risk:R2-medium` — medium risk (core logic / integrations)
- [ ] `risk:R3-high` — high risk (security, PII, production safety, infra)
- [ ] `risk:R4-critical` — critical (auth, secrets, compliance, payment-like flows)

## PR health check (required before merge)

- [ ] Bugbot review completed and triaged
- [ ] Codecov statuses reviewed (`codecov/patch` and `codecov/project` if present)
- [ ] Gates are fresh (no `gates:stale` label)

## Claude review (if required)

Claude review is optional until enabled and should only run when the PR is labeled
`gate:claude`. If the workflow runs and fails, address the findings.

- Claude review status: <FILL_ME> (PASS/CONCERNS/FAIL or "not run")

## Gated checks policy (how to run heavy tools)

This repo intentionally does **not** run Bugbot/Codecov/Claude on every commit.

When the diff is stable and ready for deep validation, apply label:

- `gates:ready`

That triggers:

- Codecov coverage upload (risk >= R2)
- Claude review (risk >= R2, if enabled)
- Bugbot trigger (risk >= R2)

If new commits are pushed after gates, the repo will label the PR `gates:stale`.
Remove staleness by re-running gates (apply `gates:ready` again after it is removed).

## What changed

- <FILL_ME>

## Why it changed

- <FILL_ME>

## Files/areas touched

- <FILL_ME>

## Tests and evidence

- Tests run:
  - <FILL_ME>
- Evidence location:
  - `qa/test_evidence/<RUN_ID>/...` (or CI link)

## Security / privacy checklist

- [ ] No secrets added to repo
- [ ] No PII/sensitive data logged
- [ ] External calls have timeouts and retries where appropriate
- [ ] Idempotent handling for worker/pipeline flows

## Docs updated

- `CHANGELOG.md`: yes/no
- Living docs updated (list):
  - <FILL_ME>

## Risks / rollback

- Risk level: <FILL_ME> (should match risk label)
- Rollback plan:
  - <FILL_ME>
