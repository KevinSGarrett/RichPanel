# Operations handbook

Last updated: 2025-12-22

This handbook describes **day-2 operations** for the Richpanel Routing + FAQ Automation Middleware.

Scope (Wave 10):
- on-call responsibilities and escalation paths
- standard operating procedures (SOPs) and cadences
- incident runbooks (routing, automation, vendor failures, backlog, cost)
- support-team training (how to interpret routing tags, overrides, and feedback signals)

Non-goals:
- This does **not** replace the Wave 06 security runbooks or Wave 07 reliability tuning playbook; it **links** to them.
- This is **not** a “how to build” guide; it is a “how to operate” guide.

---

## Quick links

- [Operator quick start](../08_Observability_Analytics/Operator_Quick_Start_Runbook.md)
- [Runbook index](Runbook_Index.md)
- [Runbook quick mapping](Runbook_Index.md#quick-mapping-dashboards--levers--smoke-tests)
- [Smoke test pack](../08_Testing_Quality/Smoke_Test_Pack_v1.md)

**Emergency levers (do these first if customers are being harmed)**
- [Kill switch and safe mode](../06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md)
- [Tuning playbook and degraded modes](../07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md)
- [Operator quick start](../08_Observability_Analytics/Operator_Quick_Start_Runbook.md)

**Release/rollback**
- [First production deploy runbook](../09_Deployment_Operations/First_Production_Deploy_Runbook.md)
- [Release and rollback](../09_Deployment_Operations/Release_and_Rollback.md)

**Runbooks**
- [Runbook index](Runbook_Index.md)

**Training**
- [Training guide for support teams](Training_Guide_for_Support_Teams.md)

---

## Operating principles

1. **Fail closed**  
   When uncertain, the middleware must prefer **route-only** or **human escalation** over risky automation.

2. **Policy engine is authoritative**  
   LLM outputs are advisory; Tier policies and deterministic-match requirements are enforced by code/config.

3. **No customer harm**  
   If we suspect wrong auto-replies, PII leaks, or systemic misroutes:
   - enable `safe_mode=true` or `automation_enabled=false` immediately
   - then investigate

4. **Small changes, reversible releases**  
   Prompts/templates/schemas are versioned artifacts and released with gates.

5. **Minimize PII exposure**  
   Logs and analytics are sanitized; raw message bodies are not stored by default.

---

## Roles and responsibilities (v1 recommended)

These roles can be held by the same person early on, but we document them separately.

### On-call operator
Primary responsibilities:
- respond to alerts and incident pages
- apply emergency levers (safe mode / automation off)
- coordinate with Support Ops for customer-facing actions
- document incident timeline and handoff notes

### Support Operations (Support Ops)
Primary responsibilities:
- macro/template review and approvals (Wave 05 artifacts)
- feedback signal adoption (Wave 08 feedback macros/tags)
- agent training and playbook compliance
- monitoring “quality signals” (automation complaints, misroutes)

### Engineering owner
Primary responsibilities:
- vendor integration issues (Richpanel/Shopify/OpenAI)
- infrastructure failures (AWS)
- bug fixes and hotfix releases
- post-incident remediation

### Business owner / leadership escalation
Primary responsibilities:
- approve customer-impacting communications (major incidents)
- approve policy changes (automation enablement scope)
- decide on refunds/credits when automation caused harm

---

## Severity levels (suggested)

- **SEV-0:** customer harm ongoing at scale (wrong replies / PII risk / chargeback mishandling)  
  Immediate action: enable safe mode or disable automation.
- **SEV-1:** major functional outage (no routing, backlog growing rapidly, DLQ exploding)
- **SEV-2:** partial degradation (slow routing, higher error rates, vendor throttling)
- **SEV-3:** minor issue / localized edge cases / cosmetic problems

---

## Standard operating procedures

### Daily (weekday) checklist (10–15 min)
- confirm no sustained backlog / oldest message age within target
- review error spikes (Richpanel 4xx/5xx, OpenAI errors, Shopify errors)
- review automation volume + complaint signals (if any)
- confirm safe mode is OFF (unless intentionally enabled)
- spot-check 10 random routed tickets for correctness (route-only baseline)

### Weekly checklist (30–60 min)
- run weekly eval (Wave 08 EvalOps) and review drift
- review Tier 0 false-negative report (must be 0 in golden set gates)
- review cost report and token usage distribution
- confirm secrets rotation schedule (tokens/keys)
- review “top misroutes” and propose taxonomy/template adjustments

### Monthly checklist (60–120 min)
- perform access review (Wave 06)
- calibrate thresholds if drift detected (Wave 04/08)
- review playbooks and refresh training if workflows changed
- backlog: close out postmortems and verify action items completed

See also:
- [Security monitoring, alarms and dashboards](../06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md)
- [Reliability capacity plan and SLOs](../07_Reliability_Scaling/Capacity_Plan_and_SLOs.md)

---

## Operational “stop the bleeding” actions

If you are unsure what to do, do these in order:

1. Enable **route-only**:
   - `safe_mode=true`
2. If customers are receiving wrong/unsafe messages:
   - `automation_enabled=false`
3. If routing actions are also causing harm (rare):
   - temporarily disable outbound actions while keeping ingestion
4. Start the relevant runbook and document timestamps.

---

## Documentation discipline

Every real incident must produce:
- an incident log entry (ticket or doc)
- a postmortem for SEV-0/1 and repeated SEV-2
- 1–3 remediation tasks with owners and deadlines

Templates:
- [Incident comms templates](templates/Incident_Comms_Templates.md)
- [Postmortem template](templates/Postmortem_Template.md)
---

## After mitigation: verify and restore

Any time you:
- disable automation (`automation_enabled=false`)
- enable safe mode (`safe_mode=true`)
- change thresholds / templates / prompts
- change concurrency limits

Then you must **verify** behavior before restoring normal operation.

Minimum verification steps:
1) Run the relevant cases in: `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
2) Confirm queue age is decreasing and DLQ is stable.
3) Confirm vendor 429/error rates have returned to baseline.
4) Only then:
   - exit safe mode (`safe_mode=false`)
   - re-enable automation (`automation_enabled=true`) progressively (Wave 09 rollout).

