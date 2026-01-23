# Claude Review Noise KPI Scoreboard

This scoreboard tracks Claude Review noise metrics during shadow/structured calibration.

## Latest KPI Snapshot (last 14 days) — 2026-01-23

## Claude Review KPI Snapshot

- Repo: `KevinSGarrett/RichPanel`
- PRs sampled: `154, 155, 153, 141, 143, 142, 152, 151, 146, 144, 148, 147, 149, 150, 145, 140, 139, 138, 137, 136, 135, 134, 133, 132, 131, 130, 129, 128, 127, 126, 125, 124, 123, 122, 120, 121, 119, 118, 117, 77, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 83, 84, 82, 81, 79, 80, 78, 75, 72, 74, 76, 73, 71, 70, 69, 68, 67, 66, 65, 64`
- Sample size (canonical comments parsed): `6`
- Missing canonical comments: `86`

| Metric | Value |
| --- | --- |
| Action Required rate | 50% (3/6) |
| Action Required per run (median / p90) | 1 / 1 |
| Token/PR median (input+output) | 18,864 (n=6) |
| Structured parse failure rate | 50% (3/6) |
| Mode breakdown | SHADOW=5, UNKNOWN=1 |

## Targets (what "good" looks like)

| KPI | Target |
| --- | --- |
| Action Required rate | `<20%` (non-R4) |
| Action Required per run (median / p90) | `median <=1`, `p90 <=2` |
| False positive rate (Action Required) | `<10%` |
| Duplicate rate vs Bugbot/Codecov | `<20%` |
| JSON parse failure rate | `0%` |
| Diff truncation rate | `<10%` |
| Token / PR (median input+output) | budgeted by risk |

## Current measurement (shadow mode)

- Sample size: `6` (insufficient sample)
- Action Required rate: `N/A`
- Action Required per run (median / p90): `N/A`
- False positive rate (Action Required): `N/A`
- Duplicate rate vs Bugbot/Codecov: `N/A`
- JSON parse failure rate: `N/A`
- Diff truncation rate: `N/A`
- Token / PR (median input+output): `N/A`

## Latest snapshot (paste output below)

Use:
`python scripts/claude_review_kpi_snapshot.py --repo <owner/repo> --prs 123,124`

```markdown
## Claude Review KPI Snapshot
- Repo: `KevinSGarrett/RichPanel`
- PRs sampled: `154, 155, 153, 141, 143, 142, 152, 151, 146, 144, 148, 147, 149, 150, 145, 140, 139, 138, 137, 136, 135, 134, 133, 132, 131, 130, 129, 128, 127, 126, 125, 124, 123, 122, 120, 121, 119, 118, 117, 77, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 83, 84, 82, 81, 79, 80, 78, 75, 72, 74, 76, 73, 71, 70, 69, 68, 67, 66, 65, 64`
- Sample size (canonical comments parsed): `6`
- Missing canonical comments: `86`

| Metric | Value |
| --- | --- |
| Action Required rate | 50% (3/6) |
| Action Required per run (median / p90) | 1 / 1 |
| Token/PR median (input+output) | 18,864 (n=6) |
| Structured parse failure rate | 50% (3/6) |
| Mode breakdown | SHADOW=5, UNKNOWN=1 |
```

## Calibration harness snapshots

Use:
`python scripts/claude_review_calibration_harness.py --fixtures legacy_small,structured_small`
