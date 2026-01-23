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
- Waves 0-2 merged and stable: **Confirmed on main** (wave changelog artifacts present: `WAVE01_CHANGELOG.md`, `WAVE_F02_CHANGELOG.md`, `WAVE_F03_CHANGELOG.md`).
- CI green on main: **Confirmed** — https://github.com/KevinSGarrett/RichPanel/actions/runs/21277465360
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

**KPI snapshot output (real PR sample, last 14 days):**
```
## Claude Review KPI Snapshot
- Repo: `KevinSGarrett/RichPanel`
- PRs sampled: `153, 141, 143, 142, 152, 151, 146, 144, 148, 147, 149, 150, 145, 140, 139, 138, 137, 136, 135, 134, 133, 132, 131, 130, 129, 128, 127, 126, 125, 124, 123, 122, 120, 121, 119, 118, 117, 77, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 83, 84, 82, 81, 79, 80, 78, 75, 72, 74, 76, 73, 71, 70, 69, 68, 67, 66, 65, 64`
- Sample size (canonical comments parsed): `3`
- Missing canonical comments: `87`

| Metric | Value |
|---|---|
| Action Required rate | 67% (2/3) |
| Action Required per run (median / p90) | 1 / 1 |
| Token/PR median (input+output) | 20,883 (n=3) |
| Structured parse failure rate | 67% (2/3) |
| Mode breakdown | SHADOW=2, UNKNOWN=1 |
```

**CI link:**
- https://github.com/KevinSGarrett/RichPanel/actions/runs/21290446257 (in progress)

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
- None
