# Evidence and audit policy

In an AI-only workflow, correctness depends on **evidence**, not “confidence”.

This policy defines:
- where evidence lives
- what must be recorded
- how evidence links are written so AM can verify quickly

---

## 1) Evidence principles

1) Evidence must be **linkable**
- CI run links
- PR comment permalinks
- file paths in repo

2) Evidence must be **stable**
- store artifacts in repo folders where applicable (docs/run reports)
- do not rely on ephemeral terminal output unless it is pasted into the run report

3) Evidence must be **complete**
- include both “what was run” and “what happened”
- include failures and how they were resolved

---

## 2) Required identifiers

### 2.1 RUN_ID
All PRs created by Cursor agents must include:
- `RUN_ID: RUN_<YYYYMMDD>_<HHMMZ>` (UTC)

### 2.2 Agent identifier
Every run report must state:
- Agent: A/B/C

### 2.3 PR number + URL
Run report must include:
- PR number
- PR link

---

## 3) Evidence locations

### 3.1 Preferred locations

**A) Run report (required)**
- Stored in run artifact directory (your existing structure typically under `REHYDRATION_PACK/RUNS/<RUN_ID>/<AGENT>/`)
- Must include:
  - CI evidence
  - gate evidence
  - waiver evidence (if any)

**B) Test evidence folder (optional but recommended)**
- `qa/test_evidence/<RUN_ID>/`
- For E2E logs, screenshots, CLI transcripts

**C) PR description**
- Must include gate status summary + links (especially for R2+)

---

## 4) Minimum evidence per risk level

### R0 / R1
- PR template filled
- CI link (if required)
- Local CI-equivalent run log snippet (recommended)

### R2+
- Everything above, plus:
  - Bugbot comment link (or waiver)
  - Codecov status result summary (or waiver)
  - Claude review output link (or waiver)
  - E2E evidence if required

### R3 / R4
- Explicit rollback plan
- Explicit monitoring/verification plan (post-merge)

---

## 5) Evidence formatting rules (so AM can score fast)

### 5.1 File references
Use explicit paths + line refs when possible:

- `backend/src/foo/bar.py:L120-L168`
- `infra/cdk/lib/stack.ts:L44-L101`

### 5.2 Links
Prefer permalinks:
- GitHub Actions run link
- PR comment permalink

### 5.3 “No placeholders”
Do not leave:
- `<FILL_ME>`
- `TODO`
- `TBD`

in the final run report or PR description.

---

## 6) Evidence checklist snippet (copy/paste)

- [ ] CI: `validate` green (link)
- [ ] Local: `python scripts/run_ci_checks.py --ci` PASS (snippet)
- [ ] Codecov: patch/project status recorded (or N/A/waiver)
- [ ] Bugbot: comment link + triage recorded (or waiver)
- [ ] Claude: verdict + link recorded (or waiver)
- [ ] E2E: evidence folder created and linked (if required)
- [ ] PR description is complete and risk label applied

