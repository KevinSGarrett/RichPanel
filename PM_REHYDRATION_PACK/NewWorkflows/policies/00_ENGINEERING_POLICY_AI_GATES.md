# Engineering Policy — AI‑Only Development With Quality Gates

**Status:** Canonical / Non‑Negotiable  
**Applies to:** All PRs, all branches that target `main`, all Cursor agent runs

This policy defines the minimum standards for building RichPanel using an **AI‑only workflow** (no human coding and no human review work), while still maintaining:

- repeatability
- auditability
- safety/security posture
- correctness and regression control
- cost/rate-limit discipline for AI review tools

---

## 1) Definitions

### 1.1 Roles

**Project Manager (PM) — ChatGPT**
- Creates objectives, decomposes tasks, generates Cursor prompts for Agent A/B/C.
- Assigns **risk level** and required gates for each run/PR.
- Owns the final decision to merge (within policy constraints).

**Cursor Agents (A/B/C)**
- Implement code, tests, docs, and operational scripts.
- Create PRs and keep CI green.
- Produce run artifacts and evidence.

**Assistant Manager (AM) — ChatGPT**
- Reviews each agent run and scores 0–100.
- A run is only considered complete when score **≥ 95** *and* all required gates/evidence are satisfied.

**Bugbot (Cursor)**
- An AI reviewer that posts PR findings (logic bugs, edge cases, suspicious patterns).

**Codecov**
- Coverage reporting with PR status checks for patch/project coverage.

**Claude Review (Semantic Review Agent / SRA)**
- A Claude-based review pass focused on correctness, security, and “meaning” (not style).

---

## 2) Core principle: Risk determines gates

We **do not** run every expensive gate on every micro-commit.

Instead:
- Every PR must be assigned a **risk level**
- The risk level drives:
  - which gates are required
  - when gates are run
  - what evidence must exist before merge
- Gates are evaluated at the **PR level**, not at “each local commit”.

See: `policies/01_RISK_CLASSIFICATION.md` and `policies/02_GATE_MATRIX.md`

---

## 3) Units of work

### 3.1 A “Run” is the unit of accountability
A **run** is one Cursor agent execution, tied to:
- one `RUN_ID`
- one branch (usually `run/<RUN_ID>_<short_slug>`)
- one PR (preferred)

### 3.2 A “PR” is the unit of enforcement
Branch protection and automation act on PRs.
Gates should be triggered when a PR is:
- “ready for gates” (stable diff + CI green)
- “ready for merge”

---

## 4) The “shippable” definition

A PR is **mergeable** only when it is:

1. **Policy compliant**
   - risk level declared + labels applied
   - required checklists completed
   - waivers documented if used

2. **CI compliant**
   - required GitHub checks green (e.g., `validate`)
   - local CI-equivalent run recorded (`python scripts/run_ci_checks.py --ci`)

3. **Gate compliant** (per risk level)
   - Bugbot satisfied (or waiver)
   - Codecov satisfied (or waiver)
   - Claude review satisfied (or waiver)
   - E2E evidence present when required

4. **Auditable**
   - evidence links recorded in PR description and/or run artifacts
   - no placeholders (“<FILL_ME>”, “TODO”, “TBD”) in required artifacts

---

## 5) Default merge policy

- Merge method: **merge commit only**
- Auto-merge is required for normal merges:
  - `gh pr merge --auto --merge --delete-branch`
- Squash merges are disallowed unless explicitly permitted as a one-off waiver.

Rationale: merge commits preserve traceability across runs/PRs and support audit evidence mapping.

---

## 6) Required artifacts (evidence)

Every run must produce:
- a run report (`RUN_REPORT.md`) in the run artifact area
- proof of local CI-equivalent run
- proof of PR checks / status rollup
- Bugbot/Codecov/Claude outputs (or waivers)

See: `policies/04_EVIDENCE_AND_AUDIT.md`

---

## 7) Waivers are allowed, but controlled

Waivers exist because external services fail (Codecov outage, Bugbot quota, Claude API errors).

Rules:
- Waivers are **time-bounded** and **explicit**
- Waivers require alternate evidence or alternate gates (e.g., replace Bugbot with Claude security review + extra tests)
- Waivers must be recorded in:
  - PR description (Waiver section)
  - run report (Findings/Waiver section)

See: `policies/03_WAIVERS_AND_EXCEPTIONS.md`

---

## 8) Enforcement: how this policy becomes real

This policy is enforced through:
1. **AM scoring gate** (95+ requires evidence)
2. **Repo branch protection** (required checks)
3. (Recommended) **Policy Gate** workflow that verifies:
   - labels/risk declaration
   - required gate artifacts exist
   - staleness rules (if new commits since last gate run)

See:
- `policies/06_REPO_POLICY_BRANCH_PROTECTION.md`
- `tooling/COST_CONTROLS.md`

---

## 9) Non-compliance outcomes

If any of the policy requirements are not met:
- AM score must be **< 95**
- PM must treat the run as **incomplete**
- PR must not be merged

