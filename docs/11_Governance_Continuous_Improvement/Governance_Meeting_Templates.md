# Governance Meeting Templates

Last updated: 2025-12-22

Use these templates to keep governance meetings short and high-signal.

---

## Weekly Quality Triage (30–45 min)

**Attendees:** QO, SO, EO (optional)  
**Inputs:** dashboards, override tags, misroute samples

Agenda:
1. Metrics snapshot (5 min)
   - routing accuracy trend
   - override rate trend
   - automation rate trend (Tier 1 / Tier 2)
2. Top 5 misroutes by impact (15–20 min)
   - What happened?
   - Which rule failed? (taxonomy vs threshold vs mapping)
   - Immediate mitigation?
3. Decisions (10 min)
   - Threshold adjustment?
   - Prompt/taxonomy change proposal?
   - Training/macro update?
4. Assign owners + due dates (5 min)

Outputs:
- issue list + owners
- any decisions logged

---

## Monthly Calibration (60–90 min)

Agenda:
1. Drift signals review (10 min)
2. New labeled sample summary (10 min)
3. Confusion matrix review (15–20 min)
4. Proposed changes (threshold/prompt/taxonomy/templates) (20–30 min)
5. Rollout plan + monitoring plan (10 min)

Outputs:
- calibration report (1–2 pages)
- updated golden set baseline (if changes approved)

---

## Quarterly Governance Review (60 min)

Agenda:
1. KPI scorecard review (15 min)
2. Safety/privacy incident review (10 min)
3. Reliability and cost review (10 min)
4. Roadmap review (15 min)
5. Risk acceptance decisions (10 min)

Outputs:
- approved roadmap changes
- documented risk decisions

