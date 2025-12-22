# Structure Report — Wave 04 Update 2

Generated: 2025-12-22

This report captures the current documentation folder structure after Wave 04 continuation work (prompts + schemas + gating spec).

---

## docs/ tree (current)
```text
├── 00_Project_Admin
│   ├── Assumptions_Constraints.md
│   ├── Change_Log.md
│   ├── Decision_Log.md
│   ├── Open_Questions.md
│   ├── Progress_Wave_Schedule.md
│   ├── Rehydration.md
│   ├── Risk_Register.md
│   ├── Stakeholders_RACI.md
│   ├── Structure_Report_Wave00.md
│   ├── Structure_Report_Wave01_Update3.md
│   ├── Structure_Report_Wave01_Update4.md
│   ├── Structure_Report_Wave02_Closeout_Wave03_Update1.md
│   ├── Structure_Report_Wave02_Update1.md
│   ├── Structure_Report_Wave02_Update2.md
│   ├── Structure_Report_Wave02_Update3.md
│   ├── Structure_Report_Wave02_Update4.md
│   ├── Structure_Report_Wave02_Update5.md
│   ├── Structure_Report_Wave03_Update2.md
│   ├── Structure_Report_Wave03_Update3.md
│   ├── Structure_Report_Wave03_Update4.md
│   └── Structure_Report_Wave03_Update5_Wave04_Start.md
├── 01_Product_Scope_Requirements
│   ├── Customer_Message_Dataset_Insights.md
│   ├── Department_Routing_Spec.md
│   ├── FAQ_Automation_Scope.md
│   ├── Product_Vision_and_Non_Goals.md
│   ├── Success_Metrics_and_SLAs.md
│   └── User_Journeys_and_Workflows.md
├── 02_System_Architecture
│   ├── AWS_Organizations_Setup_Plan_No_Control_Tower.md
│   ├── AWS_Region_and_Environment_Strategy.md
│   ├── AWS_Serverless_Reference_Architecture.md
│   ├── Architecture_Overview.md
│   ├── Data_Flow_and_Storage.md
│   ├── DynamoDB_State_and_Idempotency_Schema.md
│   ├── Hosting_Options_and_Recommendation.md
│   └── Sequence_Diagrams.md
├── 03_Richpanel_Integration
│   ├── Attachments_Playbook.md
│   ├── Automation_Rules_and_Config_Inventory.md
│   ├── Idempotency_Retry_Dedup.md
│   ├── Integration_Test_Plan.md
│   ├── Macros_and_Template_Alignment.md
│   ├── Queues_and_Routing_Primitives.md
│   ├── Richpanel_API_Contracts_and_Error_Handling.md
│   ├── Richpanel_Config_Changes_v1.md
│   ├── Team_Tag_Mapping_and_Drift.md
│   ├── Tenant_Capabilities_Clarifications.md
│   └── Webhooks_and_Event_Handling.md
├── 04_LLM_Design_Evaluation
│   ├── Confidence_Scoring_and_Thresholds.md
│   ├── Decision_Pipeline_and_Gating.md
│   ├── Intent_Taxonomy_and_Labeling_Guide.md
│   ├── Model_Config_and_Versioning.md
│   ├── Offline_Evaluation_Framework.md
│   ├── Prompt_Library_and_Templates.md
│   ├── Prompting_and_Output_Schemas.md
│   ├── Safety_and_Prompt_Injection_Defenses.md
│   ├── prompts
│   │   ├── classification_routing_v1.md
│   │   └── tier2_verifier_v1.md
│   └── schemas
│       ├── mw_decision_v1.schema.json
│       └── mw_tier2_verifier_v1.schema.json
├── 05_FAQ_Automation
│   ├── Human_Handoff_and_Escalation.md
│   ├── Order_Status_Automation.md
│   ├── Response_Templates_and_Tone.md
│   └── Top_FAQs_Playbooks.md
├── 06_Security_Privacy_Compliance
│   ├── Data_Retention_and_Access.md
│   ├── Logging_Metrics_Tracing.md
│   └── PII_Handling_and_Redaction.md
├── 07_Reliability_Scaling
│   ├── Capacity_Plan_and_SLOs.md
│   ├── Cost_Model.md
│   ├── Failure_Modes_and_Recovery.md
│   └── Rate_Limiting_and_Backpressure.md
├── 08_Testing_Quality
│   ├── LLM_Evals_in_CI.md
│   ├── Load_and_Soak_Testing.md
│   └── Test_Strategy_and_Matrix.md
├── 09_Deployment_Operations
│   ├── CICD_Plan.md
│   ├── Environments.md
│   ├── Release_and_Rollback.md
│   └── Runbooks.md
├── 10_Governance_Continuous_Improvement
│   ├── Change_Management.md
│   ├── Model_Update_Policy.md
│   └── Taxonomy_Drift_and_Calibration.md
├── 11_Cursor_Agent_Work_Packages
│   └── README.md
├── 90_Risks_Common_Issues
│   ├── Common_Issues_Mitigation_Matrix.md
│   ├── FMEA.md
│   └── Threat_Model.md
├── 99_Appendices
│   ├── Data_Inputs.md
│   ├── Glossary.md
│   └── References.md
├── CODEMAP.md
├── INDEX.md
├── ROADMAP.md
└── Waves
    ├── Wave_00_Phase0_Folder_Structure
    │   └── Wave_Notes.md
    ├── Wave_01_Discovery_Requirements
    │   └── Wave_Notes.md
    ├── Wave_02_Architecture_Infra
    │   └── Wave_Notes.md
    ├── Wave_03_Richpanel_Integration_Design
    │   ├── Cursor_Agent_Quick_Checklist_Plain_English.md
    │   ├── Cursor_Agent_Tasks.md
    │   └── Wave_Notes.md
    ├── Wave_04_LLM_Routing_Design
    │   ├── Cursor_Agent_Tasks.md
    │   └── Wave_Notes.md
    ├── Wave_05_FAQ_Automation_Design
    │   └── Wave_Notes.md
    ├── Wave_06_Security_Privacy_Compliance
    │   └── Wave_Notes.md
    ├── Wave_07_Reliability_Scaling_Capacity
    │   └── Wave_Notes.md
    ├── Wave_08_Observability_Analytics
    │   └── Wave_Notes.md
    ├── Wave_09_Testing_QA_Release
    │   └── Wave_Notes.md
    ├── Wave_10_Operations_Runbooks
    │   └── Wave_Notes.md
    ├── Wave_11_Governance_Continuous_Improvement
    │   └── Wave_Notes.md
    └── Wave_12_Cursor_Agent_Execution_Packs
        └── Wave_Notes.md
```

---

## Notable additions/changes in this update
### Added
- `docs/04_LLM_Design_Evaluation/schemas/mw_decision_v1.schema.json`
- `docs/04_LLM_Design_Evaluation/schemas/mw_tier2_verifier_v1.schema.json`
- `docs/04_LLM_Design_Evaluation/prompts/classification_routing_v1.md`
- `docs/04_LLM_Design_Evaluation/prompts/tier2_verifier_v1.md`
- `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
- `docs/00_Project_Admin/Structure_Report_Wave04_Update2.md` (this file)

### Updated
- `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`
- `docs/04_LLM_Design_Evaluation/Intent_Taxonomy_and_Labeling_Guide.md`
- `docs/04_LLM_Design_Evaluation/Offline_Evaluation_Framework.md`
- `docs/04_LLM_Design_Evaluation/Model_Config_and_Versioning.md`
- `docs/04_LLM_Design_Evaluation/Safety_and_Prompt_Injection_Defenses.md`
- `docs/04_LLM_Design_Evaluation/Prompt_Library_and_Templates.md`
- `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`
- `docs/08_Testing_Quality/LLM_Evals_in_CI.md`
- `docs/00_Project_Admin/Progress_Wave_Schedule.md`
- `docs/00_Project_Admin/Decision_Log.md`
- `docs/00_Project_Admin/Change_Log.md`

---

## Quick navigation
- Wave 04 notes: `docs/Waves/Wave_04_LLM_Routing_Design/Wave_Notes.md`
- Cursor tasks: `docs/Waves/Wave_04_LLM_Routing_Design/Cursor_Agent_Tasks.md`
- Pipeline gates: `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`
