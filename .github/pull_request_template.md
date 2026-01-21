<!--
Follow REHYDRATION_PACK/PR_DESCRIPTION/ for policy, template, and scoring.
Apply labels now: risk:R# and gate:claude.
Self-score using rubrics 07 (title) and 03 (body); meet gates:
- R0/R1: title >=95, body >=95
- R2: title >=95, body >=97
- R3/R4: title >=95, body >=98
Claude gate must run and produce response_id; Bugbot + Codecov must be green.
Do not leave ???, TBD, or empty sections.
-->

```html
<!-- PR_QUALITY: title_score=__/100; body_score=__/100; rubric_title=07; rubric_body=03; risk=risk:R#; p0_ok=true; timestamp=YYYY-MM-DD -->
```

**Run ID:** `RUN_YYYYMMDD_HHMMZ`  
**Agents:** A / B / C (or single agent)  
**Labels:** `risk:R#`, `gate:claude`  
**Risk:** `risk:R#`  
**Claude gate model (used):** `claude-...` (Haiku/Sonnet/Opus 4.5 by risk)  
**Anthropic response id:** `msg_...` (or `pending — <link>` until gate runs)  
**Spec:** See `REHYDRATION_PACK/PR_DESCRIPTION/`  

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

### Gate & quality checklist
- [ ] PR body follows `REHYDRATION_PACK/PR_DESCRIPTION/` sections + links
- [ ] Claude gate ran, PASSed, and shows `response_id` (link to comment)
- [ ] Bugbot ✅ (or findings triaged with links)
- [ ] Codecov ✅ (project + patch links)

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
