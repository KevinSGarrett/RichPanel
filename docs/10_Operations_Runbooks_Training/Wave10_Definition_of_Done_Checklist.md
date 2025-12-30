# Wave 10 definition of done checklist

Last updated: 2025-12-22

Wave 10 focuses on Operations / Runbooks / Incident Response / Training.

This checklist is used to mark Wave 10 complete in:
- `docs/Waves/Wave_10_Operations_Runbooks/Wave_Notes.md`
- `docs/00_Project_Admin/Progress_Wave_Schedule.md`

---

## Documentation deliverables
- [x] Operations handbook is present and linked from `docs/INDEX.md`
- [x] Runbook index is present and linked
- [x] At least 10 high-signal runbooks exist for the most likely failure modes
- [x] Training guide exists for support teams (routing + overrides + feedback)
- [x] Incident comms templates exist
- [x] Postmortem template exists
- [x] On-call and escalation policy exists
- [x] Operational cadence checklists exist (daily/weekly/monthly)

## Cross-wave alignment checks
- [x] Runbooks reference kill switch / safe mode correctly (Wave 06)
- [x] Runbooks reference tuning playbook / degraded modes correctly (Wave 07)
- [x] Runbooks reference observability dashboards/queries correctly (Wave 08)
- [x] Release runbooks align to Wave 09 go/no-go and rollback strategies

## “Ready for implementation” checks
- [x] Operator levers are clearly documented (safe_mode, automation_enabled, template enablement)
- [x] Feedback tags/macros are documented and have an adoption plan
- [x] Chargebacks/disputes process is documented with a human-only policy
- [x] Shipping exceptions process is documented with intake automation policy

## Status
- Target: **Wave 10 complete** when all boxes above are checked.
