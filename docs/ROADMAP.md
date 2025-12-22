# Roadmap (High-Level)

Last updated: 2025-12-22

This is the high-level wave roadmap. For detailed tracking see:
- `docs/00_Project_Admin/Progress_Wave_Schedule.md`

---

## Waves (status)
- Wave 00: Folder structure + roadmap + rehydration ✅
- Wave 01: Discovery & requirements baseline ✅
- Wave 02: System architecture & infrastructure decisions ✅
- Wave 03: Richpanel integration & configuration design ✅ (tenant verification deferred)
- Wave 04: LLM routing design + confidence scoring + safety ✅
- Wave 05: FAQ automation design (templates + playbooks + macros) ✅
- Wave 06: Security / Privacy / Compliance ✅ (complete; Update 3 closeout)
- Wave 07: Reliability / scaling / capacity ⏳
- Wave 08: Observability / analytics / eval ops ⏳
- Wave 09: Testing / QA / release strategy ⏳
- Wave 10: Operations / runbooks ⏳
- Wave 11: Governance / continuous improvement ⏳
- Wave 12: Execution packs (build-ready tickets) ⏳

---

## Next wave focus (Wave 07)
With Wave 06 closed, Wave 07 will focus on:
- SLO targets and failure-mode hardening
- retry/backoff tuning and queue behavior
- cost guardrails and scaling posture
- DR posture (single-region multi-AZ now; multi-region later if needed)

