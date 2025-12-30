# Docs Impact Map — Wave 07 Update 1

Date: 2025-12-22

Purpose:
- show which new docs affect which implementation areas
- prevent drift by making dependencies explicit

---

## Wave 07 new docs → What they influence

### Capacity, sizing, SLOs
- `docs/07_Reliability_Scaling/Capacity_Plan_and_SLOs.md`
  - informs: Lambda reserved concurrency defaults, queue age alarms, rollout SLO checks

- `docs/07_Reliability_Scaling/Concurrency_and_Throughput_Model.md`
  - informs: worker concurrency tuning rules, downstream request budgets

### Queueing and scaling strategy
- `docs/07_Reliability_Scaling/SQS_FIFO_Strategy_and_Limits.md`
  - informs: MessageGroupId selection, dedup strategy, visibility timeout configuration

### Reliability mechanics
- `docs/07_Reliability_Scaling/Resilience_Patterns_and_Timeouts.md`
  - informs: hard timeouts, circuit breaker triggers, degraded mode playbooks

- `docs/07_Reliability_Scaling/Failure_Modes_and_Recovery.md`
  - informs: operational runbooks, incident triage (Wave 10 expansion)

### Load testing
- `docs/07_Reliability_Scaling/Load_Testing_and_Soak_Test_Plan.md`
  - informs: Wave 09 release gates, staging test requirements, pass/fail criteria

### Cost controls
- `docs/07_Reliability_Scaling/Cost_Guardrails_and_Budgeting.md`
  - informs: budgets/alerts, token monitoring (Wave 08 dashboards), kill switch triggers

### DR and limits
- `docs/07_Reliability_Scaling/DR_and_Business_Continuity_Posture.md`
  - informs: go-live expectations, operational fallback design, future multi-region decision

- `docs/07_Reliability_Scaling/Service_Quotas_and_Operational_Limits.md`
  - informs: quota checks and requests during build, production readiness checklist

### Closeout artifacts
- `docs/07_Reliability_Scaling/Wave07_Definition_of_Done_Checklist.md`
- `docs/07_Reliability_Scaling/Parameter_Defaults_Appendix.md`
  - informs: final Wave 07 completion gates and implementation defaults

