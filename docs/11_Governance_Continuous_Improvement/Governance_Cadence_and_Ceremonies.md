# Governance Cadence and Ceremonies

Last updated: 2025-12-22

Governance needs a schedule so improvements happen consistently without requiring “hero effort.”

---

## Recommended cadence (v1)

### Daily (Ops quick check) — 5–10 min
Owner: Engineering Owner (or on-call)
- check queue backlog / DLQ
- check error spikes
- confirm automation rate is within expected range
- confirm no “wrong reply / PII risk” incidents

(Uses Wave 10 Operator Quick Start + runbooks.)

> See also: `docs/11_Governance_Continuous_Improvement/Governance_Audit_Checklist.md` for the monthly governance audit.

### Weekly (Quality triage) — 30–45 min
Owners: Quality/Eval Owner + Support Ops Owner
Inputs:
- top misroutes by impact (e.g., escalations, returns, chargebacks)
- top override tags/macros
- intent distribution drift (Wave 08)
Outputs:
- ticket list of top issues + fix plan (threshold/prompt/taxonomy/training)

### Bi-weekly (Change review) — 30 min
Owners: Engineering Owner + Support Ops Owner
- review pending template/prompt changes
- approve staging releases
- review rollback outcomes

### Monthly (Calibration run) — 60–90 min
Owners: Quality/Eval Owner
- label a new sample (dual-label + adjudication)
- run golden set regression
- propose threshold or prompt updates
- produce a short calibration report

### Quarterly (Governance review) — 60 min
Owners: Leadership + Engineering + Support Ops
- review KPI scorecard trends
- review incident trends
- approve major roadmap changes (new channels, new automation types)

---

## Meeting templates
- Weekly triage template: “Top issues, top root causes, top fixes”
- Monthly calibration report: “What drift we saw and what we changed”
- Quarterly review: “KPIs, risks, roadmap”

(Templates live in `Governance_Meeting_Templates.md`.)

