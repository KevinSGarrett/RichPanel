# Runbook index

Last updated: 2025-12-22

This index lists the **primary operational runbooks**. Each runbook contains:
- symptoms / alerts
- immediate actions (including safe-mode guidance)
- diagnosis steps
- mitigation and verification
- post-incident follow-ups

If you are in a SEV-0/SEV-1 situation, start here:
- [R003 — Automation wrong reply or PII risk](runbooks/R003_Automation_Wrong_Reply_or_PII_Risk.md)
- [R001 — Webhook failures and duplicate storms](runbooks/R001_Webhook_Failures_and_Duplicate_Storms.md)
- [R004 — Vendor rate limit storm](runbooks/R004_Vendor_Rate_Limit_Storm.md)

---


## Quick mapping (dashboards → levers → smoke tests)

Machine-readable mapping:
- `docs/10_Operations_Runbooks_Training/runbook_signal_map_v1.csv`


Use this table to jump from a symptom to:
1) the right dashboards,
2) the first safe lever to pull,
3) the minimum smoke tests to run before re-enabling automation.

| Runbook | Primary dashboards | First lever | Smoke tests |
|---|---|---|---|
| [R001 — Webhook failures and duplicate storms](runbooks/R001_Webhook_Failures_and_Duplicate_Storms.md) | Dashboard A — System Health, Security monitoring dashboards | Set `safe_mode=true` if automation/routing loops are suspected. | ST-060 (idempotency_duplicate_webhook), ST-070 (kill_switch_automation_disabled) |
| [R002 — Misrouting spike](runbooks/R002_Misrouting_Spike.md) | Dashboard C — Quality & Safety, Dashboard A — System Health | Enter `safe_mode=true` (route-only) if customers are being harmed. | ST-001..ST-005 (route-only baseline set), ST-050..ST-052 (multi_intent priority enforcement) |
| [R003 — Automation wrong reply or PII risk](runbooks/R003_Automation_Wrong_Reply_or_PII_Risk.md) | Dashboard C — Quality & Safety, Security monitoring dashboards, Dashboard B — Vendor Health | Immediate: `automation_enabled=false` (stop replies). | ST-040 (tier2_verified_no_match), ST-041 (tier2_verified_match); plus relevant PII/redaction tests in Smoke_Test_Pack_v1.md |
| [R004 — Vendor rate limit storm (Richpanel / OpenAI / Shopify)](runbooks/R004_Vendor_Rate_Limit_Storm.md) | Dashboard B — Vendor Health, Dashboard A — System Health | Reduce worker reserved concurrency (Wave 07 tuning) to lower QPS. | ST-070 (automation disabled) + confirm routing still works, ST-071 (safe_mode route-only) |
| [R005 — Backlog catch-up and DLQ handling](runbooks/R005_Backlog_Catchup_and_DLQ.md) | Dashboard A — System Health | Increase worker reserved concurrency gradually (Wave 07 playbook). | ST-060 (duplicate webhook/idempotency), ST-070 (automation disabled during recovery) |
| [R006 — Cost spike / token runaway](runbooks/R006_Cost_Spike_Token_Runaway.md) | Dashboard C — Quality & Safety, Dashboard B — Vendor Health | Immediate: `automation_enabled=false` to reduce LLM calls from reply flows. | ST-070 (automation disabled) still routes correctly |
| [R007 — Order status automation failure](runbooks/R007_Order_Status_Automation_Failure.md) | Dashboard A — System Health, Dashboard B — Vendor Health | Disable only order-status template(s): `template_enabled.t_order_status_tracking_verified=false`. | ST-002 (route-only order status), ST-040 (tier2 no match falls back to Tier 1); plus order-status tests in Smoke_Test_Pack_v1.md |
| [R008 — Chargebacks / disputes process (human-only)](runbooks/R008_Chargebacks_Disputes_Process.md) | Dashboard C — Quality & Safety | Keep automation off for Tier 0; ensure policy engine blocks replies. | ST-010 (tier0 chargeback_dispute), ST-052 (multi-intent tier0 override) |
| [R009 — Shipping exceptions / returns workflow (Tier 1 intake)](runbooks/R009_Shipping_Exceptions_Returns_Workflow.md) | Dashboard A — System Health, Dashboard C — Quality & Safety | If intake replies are wrong/too frequent: disable specific intake template(s). | ST-022 (DNR Tier 1 intake), ST-023 (missing items intake); plus shipping/returns intake tests in Smoke_Test_Pack_v1.md |
| [R010 — Prompt or template change release](runbooks/R010_Prompt_or_Template_Change_Release.md) | Dashboard A — System Health, Dashboard C — Quality & Safety, Go/No-Go checklist | Deploy with automation disabled first; then progressive enablement (Wave 09 runbook). | Minimum subset: ST-001..ST-005, ST-010, ST-040..ST-041, ST-060, ST-070..ST-071, Recommended: run full Smoke_Test_Pack_v1.md |


---

## Core reliability runbooks

- [R001 — Webhook failures and duplicate storms](runbooks/R001_Webhook_Failures_and_Duplicate_Storms.md)
- [R004 — Vendor rate limit storm (Richpanel / OpenAI / Shopify)](runbooks/R004_Vendor_Rate_Limit_Storm.md)
- [R005 — Backlog catch-up and DLQ handling](runbooks/R005_Backlog_Catchup_and_DLQ.md)
- [R006 — Cost spike / token runaway](runbooks/R006_Cost_Spike_Token_Runaway.md)

## Quality and routing runbooks

- [R002 — Misrouting spike](runbooks/R002_Misrouting_Spike.md)
- [R003 — Automation wrong reply or PII risk](runbooks/R003_Automation_Wrong_Reply_or_PII_Risk.md)
- [R007 — Order status automation failure](runbooks/R007_Order_Status_Automation_Failure.md)

## Business workflow runbooks

- [R008 — Chargebacks / disputes process](runbooks/R008_Chargebacks_Disputes_Process.md)
- [R009 — Shipping exceptions / returns workflow](runbooks/R009_Shipping_Exceptions_Returns_Workflow.md)

## Change and release runbooks

- [R010 — Prompt or template change release](runbooks/R010_Prompt_or_Template_Change_Release.md)

---

## Related operational references

- [Kill switch and safe mode](../06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md)
- [Tuning playbook and degraded modes](../07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md)
- [Backlog catch-up strategy](../07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md)
- [Operator quick start](../08_Observability_Analytics/Operator_Quick_Start_Runbook.md)
- [First production deploy runbook](../09_Deployment_Operations/First_Production_Deploy_Runbook.md)
