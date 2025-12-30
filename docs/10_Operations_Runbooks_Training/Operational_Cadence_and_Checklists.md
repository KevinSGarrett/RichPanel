# Operational cadence and checklists

Last updated: 2025-12-22

This document defines “maintenance rhythms” so the system stays healthy over time.

---

## Daily checklist (10–15 minutes)
1. Check backlog health
   - SQS oldest message age within target
   - no sustained DLQ growth
2. Check error health
   - worker error rate
   - vendor 429/5xx
3. Check automation safety
   - automation volume within expected band
   - no spike in override/complaint tags
4. Spot-check sample outcomes
   - 5–10 tickets across channels
   - verify primary team/tag mapping is correct
5. Verify levers are in the intended state
   - `safe_mode=false`
   - `automation_enabled=true` (unless intentionally disabled)

Reference dashboards:
- [Dashboards, alerts, and reports](../08_Observability_Analytics/Dashboards_Alerts_and_Reports.md)
- [Security monitoring alarms and dashboards](../06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md)

---

## Weekly checklist (30–60 minutes)
1. Run weekly eval + review drift
   - compare against last “golden set” baseline
2. Review misroute clusters
   - top confusion pairs
   - identify taxonomy updates or threshold changes
3. Review top templates by volume
   - ensure copy still matches policy
4. Review cost and token usage
   - investigate outliers and sampling changes
5. Verify secrets rotation plan
   - ensure rotation runbook remains feasible

References:
- [EvalOps scheduling and runbooks](../08_Observability_Analytics/EvalOps_Scheduling_and_Runbooks.md)
- [LLM regression gates checklist](../08_Testing_Quality/LLM_Regression_Gates_Checklist.md)

---

## Monthly checklist (60–120 minutes)
1. Access review + break-glass verification
2. Review incident trends and close remediation tasks
3. Calibration review
   - thresholds and template enablement
4. Training refresh
   - update support training based on top failure modes
5. Run a tabletop drill (optional but recommended)
   - simulate “wrong replies” and “vendor outage” scenarios

References:
- [IAM access review and break glass](../06_Security_Privacy_Compliance/IAM_Access_Review_and_Break_Glass.md)
- [Threat model](../06_Security_Privacy_Compliance/Threat_Model_STRIDE.md)

---

## Quarterly checklist
- review vendor posture (OpenAI/Richpanel/Shopify) and limits
- review SLO/SLA alignment with business expectations
- rotate long-lived secrets and audit IAM boundaries
- update runbooks based on new failure modes

---

## The “two-lane” work queue (recommended)
To avoid mixing urgent operations with long-term improvements, maintain two lanes:
- **Ops lane:** incidents, runbook fixes, urgent threshold changes
- **Improvement lane:** taxonomy refinements, better templates, eval set growth, deeper analytics

If something from Ops lane repeats twice in a month, it becomes an Improvement lane project.
