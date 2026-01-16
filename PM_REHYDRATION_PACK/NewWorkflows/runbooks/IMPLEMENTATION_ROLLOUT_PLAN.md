# Rollout plan (recommended)

This plan lets you adopt the full strategy without breaking your workflow.

---

## Phase 0 — Align policy and templates (same day)
- Copy PR template from `templates/.github/pull_request_template.md` into repo
- Create labels:
  - `risk:*`
  - `gates:*`
  - `waiver:active`
- Update PM/AM prompts to require risk + gate plan

Success criteria:
- Every new PR has a risk label and gate plan.

---

## Phase 1 — Stop wasting runs (process change)
- Update Cursor agent instructions:
  - commit locally, push only when stable
  - do not trigger Bugbot/Claude until CI green and `gates:ready`
- Keep existing CI.

Success criteria:
- CI runs drop significantly per PR.
- Bugbot runs occur ~1x per medium/high PR.

---

## Phase 2 — Add Claude review (manual → automated)
Start with Mode A (manual) to validate prompts and output formatting, then move to Mode B/C.

Success criteria:
- R2+ PRs include Claude verdict + link in run report.

---

## Phase 3 — Automate staleness labels
- Add “Gates Staleness” workflow
- Ensure new commits force `gates:stale`

Success criteria:
- No PR merges with stale gates.

---

## Phase 4 — Add required `policy-gate` check (enforcement)
- Add Policy Gate workflow
- Update branch protection to require:
  - `validate`
  - `policy-gate`

Success criteria:
- GitHub blocks merges missing risk labels or missing required gates for R2+.

---

## Phase 5 — Tune thresholds and cost
- Add `codecov.yml` with thresholds
- Tune Claude model selection and max tokens by risk
- Add concurrency limits

Success criteria:
- Stable, predictable gate costs without quality regressions.

