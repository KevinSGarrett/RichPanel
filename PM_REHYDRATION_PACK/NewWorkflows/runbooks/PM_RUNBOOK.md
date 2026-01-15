# Runbook — Project Manager (ChatGPT)

This runbook tells the PM exactly how to operate the workflow so Bugbot/Codecov/Claude are used **correctly and efficiently**.

---

## 0) PM’s responsibilities (non-negotiable)

1) Create a clear objective and stop conditions.
2) Assign risk level (`risk:*`) for the PR/run.
3) Decide required gates using the gate matrix.
4) Issue prompts for Agent A/B/C that:
   - enforce local CI-equivalent checks before push
   - enforce gate triggering only at the right time
5) Verify evidence exists before declaring “ready to merge”.

---

## 1) PM workflow (step-by-step)

### Step 1 — Define the unit of work
- Assign `RUN_ID`
- Define:
  - objective
  - scope boundaries
  - stop conditions

### Step 2 — Risk classify
Use `policies/01_RISK_CLASSIFICATION.md`.

Output must be explicit:
- Risk label: `risk:R?_...`
- Why
- Critical zones touched (if any)

### Step 3 — Select required gates
Use `policies/02_GATE_MATRIX.md`.

Write the gate plan:
- CI: required
- Codecov: required/advisory/N/A
- Bugbot: required/optional/N/A
- Claude: required/optional/N/A
- E2E: required/conditional/N/A

### Step 4 — Generate Cursor prompts (Agents A/B/C)

Your prompts must include:

**Process constraints**
- Commit locally as needed, but **push only when stable**.
- Run local CI-equivalent before pushing:
  - `python scripts/run_ci_checks.py --ci`
- Keep PR diff minimal and focused.

**Gate constraints**
- Do **not** trigger Bugbot/Claude until:
  - CI is green
  - PR is stable
  - label `gates:ready` applied

**Evidence constraints**
- Update run report template section:
  - Codecov, Bugbot, Claude evidence fields

### Step 5 — Merge readiness decision
PM must verify:

- CI `validate` green
- Gate evidence present and non-stale (per risk)
- Waivers (if any) documented and justified
- AM score ≥ 95 and references evidence

Only then:
- `gh pr merge --auto --merge --delete-branch`

---

## 2) PM checklist (copy/paste)

- [ ] RUN_ID assigned
- [ ] Risk label chosen and applied in PR
- [ ] Gate plan written (per matrix)
- [ ] Agent prompts include: local CI before push + gate timing
- [ ] PR template is complete
- [ ] CI validate green
- [ ] Codecov status recorded (or N/A/waiver)
- [ ] Bugbot output triaged (or waiver)
- [ ] Claude verdict PASS or waived with alternate evidence
- [ ] E2E proof present if required
- [ ] AM score ≥ 95 with evidence links
- [ ] Auto-merge enabled (merge commit)

---

## 3) PM “do not do” list

- Do not run Bugbot/Claude on unstable/WIP diffs.
- Do not accept “we ran it earlier” if PR is stale.
- Do not merge without evidence just because “it looks fine”.

---

## 4) Suggested automation (optional but recommended)

- Add policy-gate workflow required in branch protection.
- Add staleness label workflow.
- Add label-triggered Bugbot + Claude workflows.

This makes PM’s job easier because GitHub enforces the rules.

