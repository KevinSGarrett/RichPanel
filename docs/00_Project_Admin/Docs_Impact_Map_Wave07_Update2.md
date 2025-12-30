# Docs Impact Map — Wave 07 Update 2

Date: 2025-12-22  
Wave: 07 (Reliability/Scaling) — Update 2 (closeout)

This file lists **what changed** and **why it matters**.

---

## High impact changes

### 1) Canonical parameter defaults (new YAML)
Files:
- `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
- `docs/07_Reliability_Scaling/Parameter_Defaults_Appendix.md`

Impact:
- Gives a single source of truth for runtime knobs (concurrency, retries, timeouts, DLQ rules).
- Reduces config drift and makes tuning decisions auditable.

### 2) Operator runbooks for tuning and degraded modes
Files:
- `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`

Impact:
- Defines deterministic actions for backlog, 429 storms, vendor outages, and cost spikes.
- Aligns reliability actions with Wave 06 kill switch (safe mode / disable automation).

### 3) Backlog catch-up and replay strategy
Files:
- `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`

Impact:
- Prevents “blast drain” incidents that cause rate-limit storms, duplicate replies, and runaway cost.
- Makes DLQ replay controlled and safe.

---

## Supporting updates
- Wave 07 marked complete in:
  - `docs/Waves/Wave_07_Reliability_Scaling_Capacity/Wave_Notes.md`
  - `docs/00_Project_Admin/Progress_Wave_Schedule.md`
- Navigation updated:
  - `docs/INDEX.md`
  - `docs/REGISTRY.md`

---

## What to read first
If you read only 3 files from this update:
1) `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
2) `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`
3) `docs/07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md`
