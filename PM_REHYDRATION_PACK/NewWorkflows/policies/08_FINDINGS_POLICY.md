# Findings policy (Bugbot + Codecov + Claude)

This policy standardizes:
- how findings are classified
- what is blocking
- how triage is recorded
- how waivers apply

---

## 1) Finding severities

### BLOCKER (must fix or waive)
A finding is a BLOCKER if it could cause:
- incorrect behavior in production
- data corruption or loss
- security/privacy exposure
- silent failures (hard to detect)
- broken idempotency / retries
- broken authz/authn assumptions

### HIGH (treat as blocker for R3/R4)
- likely bug or reliability hazard
- potential escalation path
- high operational cost if wrong

### MEDIUM (must address for R2+ if cheap; otherwise justify)
- plausible bug but depends on context
- missing validation
- confusing behavior

### LOW / INFO
- style/readability
- refactor suggestions
- optional performance improvements

---

## 2) Source-specific mapping

### Bugbot findings
- Often come as natural language suggestions.
- If Bugbot indicates “this could crash” or “this could be wrong for null/empty”, treat as MEDIUM/HIGH and validate.

### Codecov findings
- Patch coverage failure is typically a BLOCKER for R2+.
- Project coverage regression is HIGH for R3/R4.

### Claude findings
- Claude outputs should already be grouped into blocking/non-blocking.
- If Claude returns `CONCERNS`, treat as HIGH until resolved.

---

## 3) Triage outcomes (required recording)

For every finding:

1) **Fixed**
- link to commit/code

2) **False positive**
- explain why it is safe
- if possible, add a regression test anyway (optional)

3) **Deferred**
- requires waiver
- requires follow-up issue

---

## 4) Where triage must be recorded

- Run report (required)
- PR comment thread or PR description (recommended)

---

## 5) Staleness rule

If findings were triaged but new commits landed:
- re-evaluate findings for new code
- rerun gates if required

---

## 6) AM scoring implication

Any untriaged BLOCKER:
- AM score must be < 95

Any waived BLOCKER without alternate evidence:
- AM score must be < 95

