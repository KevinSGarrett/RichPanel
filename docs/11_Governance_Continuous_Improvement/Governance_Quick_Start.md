# Governance Quick Start

Last updated: 2025-12-22

This is the **short, operational guide** to keep the Richpanel routing + FAQ automation system accurate and safe over time.

Use this when you need to:
- diagnose “why did the system do that?”
- make a change (template/prompt/taxonomy/threshold/mapping)
- roll out improvements without creating new production risks

---

## The 3 rules that prevent 90% of governance failures

1) **The system is code + artifacts.**  
   Prompts, templates, schemas, thresholds, team mappings, and automation policies are **versioned artifacts**.  
   No “silent production edits.”

2) **Smallest safe fix first.**  
   Prefer (in order):
   - disabling a template or entering safe_mode
   - tightening thresholds / gating
   - adjusting routing mappings
   - prompt changes
   - taxonomy refactors

3) **LLM output is advisory. Policy is authoritative.**  
   Policy gates must block unsafe outcomes even if the model suggests them.

---

## Where things live (the “map”)

### Routing & automation behavior
- **Intent taxonomy + labeling**: `docs/04_LLM_Design_Evaluation/Intent_Taxonomy_and_Labeling_Guide.md`
- **LLM decision schema**: `docs/04_LLM_Design_Evaluation/schemas/`
- **Confidence scoring + thresholds**: `docs/04_LLM_Design_Evaluation/Confidence_Scoring_and_Thresholds.md`
- **Primary policy gates**: `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`

### Customer-facing replies (controlled)
- **Template ID catalog** (LLM outputs IDs, not text): `docs/04_LLM_Design_Evaluation/Template_ID_Catalog.md`
- **Templates library**: `docs/05_FAQ_Automation/Templates_Library_v1.md`
- **Template source YAML**: `docs/05_FAQ_Automation/templates/templates_v1.yaml`
- **Brand constants**: `docs/05_FAQ_Automation/templates/brand_constants_v1.yaml`

### Operational knobs (safety + performance)
- **Kill switch / safe mode**: `docs/06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md`
- **Parameter defaults (v1)**: `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
- **Tuning playbook**: `docs/07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md`

### Observability & quality monitoring
- **Event taxonomy**: `docs/08_Observability_Analytics/observability_event_taxonomy_v1.yaml`
- **Dashboards/alerts/reports**: `docs/08_Observability_Analytics/Dashboards_Alerts_and_Reports.md`
- **Drift detection**: `docs/08_Observability_Analytics/Quality_Monitoring_and_Drift_Detection.md`

### Testing & release gates
- **Smoke test pack**: `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
- **Go/No-Go**: `docs/09_Deployment_Operations/Go_No_Go_Checklist.md`
- **First prod deploy runbook**: `docs/09_Deployment_Operations/First_Production_Deploy_Runbook.md`

### Ops runbooks
- **Operator quick start**: `docs/08_Observability_Analytics/Operator_Quick_Start_Runbook.md`
- **Runbooks index**: `docs/10_Operations_Runbooks_Training/Runbook_Index.md`

### Governance tracking
- **Decision Log**: `docs/00_Project_Admin/Decision_Log.md`
- **Change Log**: `docs/00_Project_Admin/Change_Log.md`
- **Progress & Wave schedule**: `docs/00_Project_Admin/Progress_Wave_Schedule.md`

---

## Standard change workflow (default)

Use this for any non-emergency change (copy edits, threshold changes, mapping tweaks, new templates, new intents).

1) **Describe the change**
   - What is the problem?
   - What is the “smallest safe fix”?
   - What artifact(s) change?

2) **Edit the artifact(s)**
   - Templates: `templates_v1.yaml` + regenerate library doc
   - Thresholds: update threshold config (Wave 04/07)
   - Mappings: routing mapping docs (Wave 01/03)
   - Prompts/schemas: Wave 04 schemas/prompts

3) **Run validations**
   - Schema validation (decision + observability)
   - Offline eval / golden set check (Wave 04 + Wave 08 EvalOps)
   - Smoke tests (Wave 09 pack)

4) **Log the change**
   - Update `Change_Log.md`
   - If the change alters policy/behavior, also add a decision entry to `Decision_Log.md`

5) **Release safely**
   - Stage first
   - Progressive enablement (routing-only → limited Tier 1 → Tier 2)
   - Monitor dashboards for regressions

6) **Close the loop**
   - Verify success metrics
   - Record learnings (postmortem if incident)

---

## Emergency workflow (safety first)

If there is a wrong reply, PII risk, runaway costs, or misrouting spike:

1) **Pull the safety lever first**
   - `automation_enabled=false` (stop auto replies)
   - `safe_mode=true` (route-only mode)
   - disable individual templates if the issue is localized

2) **Stabilize**
   - follow the relevant Wave 10 runbook
   - watch SQS age, DLQ, and vendor 429s

3) **Fix**
   - smallest safe fix first
   - test + verify with smoke tests

4) **Document**
   - Decision Log (what we did and why)
   - Change Log (what changed)
   - Postmortem if SEV-0/SEV-1

---

## Common governance actions (fast paths)

### Change template copy (or variables)
- Edit `templates_v1.yaml`
- Ensure variables are safe (no addresses/payment info v1)
- Verify template renders with missing optional fields
- Run smoke tests for that template’s playbook

### Enable/disable a template
- Prefer runtime feature flag first (fast mitigation)
- Then update template catalog (to keep drift low)

### Add a new FAQ automation
- Add/define a template (Wave 05)
- Add playbook rules (Wave 05)
- Add taxonomy intent if needed (Wave 04)
- Add test case + eval coverage (Wave 09 + Wave 04)

### Add a new intent/team/department mapping
- Follow: `docs/11_Governance_Continuous_Improvement/Procedures_Adding_Intents_Teams_Templates.md`
- Update routing spec (Wave 01)
- Add eval + smoke coverage

### Adjust routing thresholds
- Update threshold config
- Run golden set evaluation and compare with baseline
- Deploy progressively and monitor drift signals

### Update model version or prompt
- Follow `Model_Update_Policy.md`
- Use progressive rollout + rollback path
- Monitor cost + quality drift metrics

---

## Ownership
See: `docs/11_Governance_Continuous_Improvement/Artifact_Ownership_RACI.md`

If names are not yet assigned, default ownership is:
- Engineering Owner: responsible for releases, infrastructure knobs, observability
- Support Ops Owner: responsible for macros, templates review, process compliance
- Quality/Eval Owner: responsible for labeling and evaluation cadence

---

## The monthly audit
Use: `docs/11_Governance_Continuous_Improvement/Governance_Audit_Checklist.md`
