<!--
Required: follow REHYDRATION_PACK/PR_DESCRIPTION/ for policy, scoring, and formatting.
Minimum score gate:
- R0/R1: title >=95, body >=95
- R2: title >=95, body >=97
- R3/R4: title >=95, body >=98
Required labels: risk:R#, gate:claude
Claude gate model + Anthropic response id must be filled (or "pending — <link>") after the gate runs.
-->

# PR Description Template (Copy/Paste)

Use this template verbatim. Replace placeholders. Do **not** leave `???`, `TBD`, or empty sections.

> Rule: the PR description must be **complete before requesting review**.  
> If something is pending, include a **link to the pending run**.

---

## Standard template (risk:R1–R4)

```html
<!-- PR_QUALITY: title_score=__/100; body_score=__/100; rubric_title=07; rubric_body=03; risk=risk:R#; p0_ok=true; timestamp=YYYY-MM-DD -->
```

**Run ID:** `RUN_YYYYMMDD_HHMMZ`  
**Agents:** A / B / C (or single agent)  
**Labels:** `risk:R#`, `gate:claude`  
**Risk:** `risk:R#`  
**Claude gate model (used):** `claude-...` (Haiku/Sonnet/Opus 4.5 by risk)  
**Anthropic response id:** `msg_...` (or `pending — <link>` until gate runs)  

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
- 

### 4) What changed
**Core changes:**
- 
- 
- 

**Design decisions (why this way):**
- 
- 

### 5) Scope / files touched
**Runtime code:**
- `path/to/file.py`
- 

**Tests:**
- `path/to/test_file.py`
- 

**CI / workflows:**
- (None) or list files
- 

**Docs / artifacts:**
- `REHYDRATION_PACK/RUNS/.../RUN_REPORT.md`
- 

### 6) Test plan
**Local / CI-equivalent:**
- `python scripts/run_ci_checks.py --ci`
- (List the exact commands you ran)

**E2E / proof runs (redact ticket numbers in PR body if claiming PII-safe):**
- `python scripts/dev_e2e_smoke.py ... --ticket-number <redacted> ...`

### 7) Results & evidence
**CI:** pending — `<link>`  
**Codecov:** pending — `<direct Codecov PR link>`  
**Bugbot:** pending — `<PR link>` (trigger via `@cursor review`)  

**Artifacts / proof:**
- `REHYDRATION_PACK/RUNS/.../e2e_outbound_proof.json`
- 

**Proof snippet(s) (PII-safe):**
```text
<minimal lines proving the claim; no raw ticket bodies/emails>
```

### 8) Risk & rollback
**Risk rationale:** `risk:R#` — (one crisp sentence explaining why)

**Failure impact:** (what breaks if wrong)

**Rollback plan:**
- Revert PR
- Any cleanup/redeploy steps
- Re-run the minimal proof to confirm rollback

### 9) Reviewer + tool focus
**Please double-check:**
- 
- 

**Please ignore:**
- Generated registries / line number shifts unless CI fails.
- Rehydration pack artifacts except referenced proof files.

---

## R0 compact template (docs-only)

```html
<!-- PR_QUALITY: title_score=__/100; body_score=__/100; rubric_title=07; rubric_body=03; risk=risk:R0; p0_ok=true; timestamp=YYYY-MM-DD -->
```

**Labels:** `risk:R0`, `gate:claude`  
**Risk:** `risk:R0` (docs-only)  
**Claude gate model (used):** `claude-...` (Haiku 4.5 for R0)  
**Anthropic response id:** `msg_...` (or `pending — <link>` until gate runs)  

### Summary
- 

### Why
- 

### Invariants
- No runtime behavior changed.
- No secrets/PII included.

### Scope
- Docs touched:
  - `docs/...`

### Evidence
- CI: N/A or pending — `<link>` (use checks link if it will run)
- Codecov: N/A
- Bugbot: N/A (unless requested)

### Reviewer focus
- Double-check:
  - doc correctness and links
- Ignore:
  - generated registries unless CI fails
# Summary

- RUN_ID: `RUN_<YYYYMMDD>_<HHMMZ>`
- Task IDs: `TASK-###, ...`

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

## Docs updated
- `CHANGELOG.md`: yes/no
- Living docs updated (list):
  - <FILL_ME>

## Risks / rollback
- Risk level: low/med/high
- Rollback plan:
  - <FILL_ME>
