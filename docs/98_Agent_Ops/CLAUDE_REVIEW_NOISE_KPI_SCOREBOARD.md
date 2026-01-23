# Claude Review Noise KPI Scoreboard

This scoreboard tracks Claude Review noise metrics during shadow/structured calibration.

## Targets (what "good" looks like)
| KPI | Target |
|---|---|
| Action Required rate | `<20%` (non-R4) |
| Action Required per run (median / p90) | `median <=1`, `p90 <=2` |
| False positive rate (Action Required) | `<10%` |
| Duplicate rate vs Bugbot/Codecov | `<20%` |
| JSON parse failure rate | `0%` |
| Diff truncation rate | `<10%` |
| Token / PR (median input+output) | budgeted by risk |

## Current measurement (shadow mode)
- Sample size: `0` (insufficient sample)
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

## Calibration harness snapshots
Use:
`python scripts/claude_review_calibration_harness.py --fixtures legacy_small,structured_small`
