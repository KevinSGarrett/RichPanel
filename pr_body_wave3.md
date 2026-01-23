<!-- PR_QUALITY: title_score=95/100; body_score=95/100; rubric_title=07; rubric_body=03; risk=risk:R2; p0_ok=true; timestamp=2026-01-23 -->

# Claude Review Gap Filler: Wave 3 - Calibration Harness + Novelty Controls

**Base:** `main`  
**Branch:** `claude-review-gap-filler/wave3-calibration`  
**PR type:** Draft until CI is green  
**Merge:** Squash merge after approval + green CI  

## 1) Summary
- Add offline calibration harness with KPI scoreboard output.
- Add KPI snapshot script + parser tests.
- Inject failed check summary into the Claude prompt to avoid duplicate bot findings.

## 2) Preconditions
- Waves 0-2 merged and stable: **Not verified here** (please confirm on main).
- CI green on main: **Not verified here** (please confirm on main).
- Shadow PR samples >= 10: **Pending** (plan below).

## 3) Step 0 plan (recommended items)
- Collect at least 10 PRs using `CLAUDE_REVIEW_MODE=shadow`, then run:
  `python scripts/claude_review_kpi_snapshot.py --repo <owner/repo> --since-days 14`
- Paste the snapshot into `docs/98_Agent_Ops/CLAUDE_REVIEW_NOISE_KPI_SCOREBOARD.md`.

## 4) Evidence / Proof (tests + dry-run + CI)
**Unit tests (required):**
```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.015s

OK
```

**Calibration harness (5 fixtures):**
```
Action Required rate: 60% (3/5)
Token/PR median (input+output): 144
Duplicate rate (finding_id): 0% (0/3)
```

**Sample KPI snapshot output (redacted, offline fixture):**
```
## Claude Review KPI Snapshot
- Repo: `sample/repo`
- PRs sampled: `101`
- Sample size (canonical comments parsed): `1`
- Missing canonical comments: `0`

| Metric | Value |
|---|---|
| Action Required rate | 100% (1/1) |
| Action Required per run (median / p90) | 1 / 1 |
| Token/PR median (input+output) | 19,120 (n=1) |
| Structured parse failure rate | 0% (0/1) |
| Mode breakdown | STRUCTURED=1 |
```

**CI link:**
- N/A (no GitHub access in this environment; run CI after push)

## 5) KPI impact statement (expected)
- Token/PR: +0 to +50 tokens expected due to short failed-check summary injection.
- Duplicate rate: expected to decrease (prompt explicitly asks for novel insights only).
- AR-rate: expected neutral or slightly lower; harness baseline is 60% (3/5 fixtures).
- False positive proxy: expected neutral; harness labeled FP proxy is 0% (0/3).

## 6) Risk & rollback
- Backout plan: set `CLAUDE_REVIEW_MODE=legacy` or revert this PR (single revert).
- Stop condition: if calibration shows no clear benefit, do not merge.

## 7) Optional prompt caching
- Not implemented (no cache hit/miss signals available).

## 8) Blocked / N-A
- CI run link: blocked pending GitHub access.
- Real PR KPI snapshot: blocked pending GitHub token + PR numbers.
