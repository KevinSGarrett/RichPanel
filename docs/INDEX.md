# Docs Index

Last updated: 2025-12-29  
Last verified: 2025-12-29 — schedules clarified; Foundation DoD added (Wave F09)

Use this as the master navigation for the project plan.

Quick start:
- [Progress & Wave Schedule](00_Project_Admin/Progress_Wave_Schedule.md)
- [Roadmap](ROADMAP.md)
- [CODEMAP](CODEMAP.md)
- [Docs Registry (all files)](REGISTRY.md)


## Core living docs (always kept up to date)
These are the “always-update” docs that capture the full build history and current truth.

Definition + update triggers:
- [Living documentation set](98_Agent_Ops/Living_Documentation_Set.md)
- [Foundation Definition of Done](00_Project_Admin/Definition_of_Done__Foundation.md)
- [Build Mode Activation checklist](00_Project_Admin/Build_Mode_Activation_Checklist.md)

Quick links:
- [Repository Changelog](../CHANGELOG.md)
- [Decision Log](00_Project_Admin/Decision_Log.md)
- [Change Requests](00_Project_Admin/Change_Requests/README.md)
- [Issue Log](00_Project_Admin/Issue_Log.md)
- [Progress Log](00_Project_Admin/Progress_Log.md)
- [To-Do / Checklists](00_Project_Admin/To_Do/README.md)
- [System Overview](02_System_Architecture/System_Overview.md)
- [System Matrix](02_System_Architecture/System_Matrix.md)
- [API Reference](04_API_Contracts/API_Reference.md)
- [OpenAPI](04_API_Contracts/openapi.yaml)
- [Environment & Config](09_Deployment_Operations/Environment_Config.md)
- [Env template (non-secret)](../config/.env.example)
- [Security & privacy](06_Security_Privacy_Compliance/README.md)
- [Test evidence log](08_Testing_Quality/Test_Evidence_Log.md)
- [Raw test evidence folder](../qa/test_evidence/)
- [User Manual](07_User_Documentation/User_Manual.md)
- [Operations handbook](10_Operations_Runbooks_Training/Operations_Handbook.md)

---

## 00 — Project administration
- [Rehydration](00_Project_Admin/Rehydration.md)
- [Open Questions](00_Project_Admin/Open_Questions.md)
- [Assumptions & Constraints](00_Project_Admin/Assumptions_Constraints.md)
- [Decision Log](00_Project_Admin/Decision_Log.md)
- [Change Requests](00_Project_Admin/Change_Requests/README.md)
- [Canonical vs legacy doc paths](00_Project_Admin/Canonical_vs_Legacy_Documentation_Paths.md)
- [Documentation chunking audit](00_Project_Admin/Doc_Chunking_Audit.md)
- [Risk Register](00_Project_Admin/Risk_Register.md)
- [Stakeholders & RACI](00_Project_Admin/Stakeholders_RACI.md)
- [Change Log](00_Project_Admin/Change_Log.md)
- [Roles and Tooling](00_Project_Admin/Roles_and_Tooling.md)

---

## 01 — Product scope and requirements
- [Product vision and non-goals](01_Product_Scope_Requirements/Product_Vision_and_Non_Goals.md)
- [User journeys and workflows](01_Product_Scope_Requirements/User_Journeys_and_Workflows.md)
- [Department routing spec](01_Product_Scope_Requirements/Department_Routing_Spec.md)
- [FAQ automation scope](01_Product_Scope_Requirements/FAQ_Automation_Scope.md)
- [Success metrics and SLAs](01_Product_Scope_Requirements/Success_Metrics_and_SLAs.md)

---

## 02 — System architecture
- [AWS serverless reference architecture](02_System_Architecture/AWS_Serverless_Reference_Architecture.md)
- [Data flow and storage](02_System_Architecture/Data_Flow_and_Storage.md)
- [DynamoDB idempotency + state schema](02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md)

---

## 03 — Richpanel integration
- [Webhook and event handling](03_Richpanel_Integration/Webhooks_and_Event_Handling.md)
- [API contracts and error handling](03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md)
- [Idempotency / retry / dedup](03_Richpanel_Integration/Idempotency_Retry_Dedup.md)
- [Team/tag mapping and drift](03_Richpanel_Integration/Team_Tag_Mapping_and_Drift.md)
- [Vendor doc crosswalk (Richpanel)](03_Richpanel_Integration/Vendor_Doc_Crosswalk.md)
- [Richpanel vendor reference index](../reference/richpanel/INDEX.md)

---

## 04 — LLM routing design and evaluation
- [Taxonomy and labeling guide](04_LLM_Design_Evaluation/Intent_Taxonomy_and_Labeling_Guide.md)
- [Decision pipeline and gating](04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md)
- [Confidence scoring and thresholds](04_LLM_Design_Evaluation/Confidence_Scoring_and_Thresholds.md)
- [Golden set labeling SOP](04_LLM_Design_Evaluation/Golden_Set_Labeling_SOP.md)
- [Template ID catalog (LLM contract)](04_LLM_Design_Evaluation/Template_ID_Catalog.md)

---

## 05 — FAQ automation
- [Templates library (approved copy)](05_FAQ_Automation/Templates_Library_v1.md)
- [Order status automation](05_FAQ_Automation/Order_Status_Automation.md)
- [Top FAQs playbooks](05_FAQ_Automation/Top_FAQs_Playbooks.md)
- [Macro alignment + governance](05_FAQ_Automation/Macro_Alignment_and_Governance.md)
- [Pre-launch copy checklist](05_FAQ_Automation/Pre_Launch_Copy_and_Link_Checklist.md)

---

## 06 — Security, privacy, and compliance
- [Security overview](06_Security_Privacy_Compliance/Security_Privacy_Compliance_Overview.md)
- [Data classification & PII inventory](06_Security_Privacy_Compliance/Data_Classification_and_PII_Inventory.md)
- [PII handling and redaction](06_Security_Privacy_Compliance/PII_Handling_and_Redaction.md)
- [Data retention and access](06_Security_Privacy_Compliance/Data_Retention_and_Access.md)
- [Access & secrets inventory](06_Security_Secrets/Access_and_Secrets_Inventory.md)
- [Webhook auth and request validation](06_Security_Privacy_Compliance/Webhook_Auth_and_Request_Validation.md)
- [Secrets and key management](06_Security_Privacy_Compliance/Secrets_and_Key_Management.md)
- [IAM least privilege](06_Security_Privacy_Compliance/IAM_Least_Privilege.md)
- [IAM access review & break-glass](06_Security_Privacy_Compliance/IAM_Access_Review_and_Break_Glass.md)
- [Network security and egress controls](06_Security_Privacy_Compliance/Network_Security_and_Egress_Controls.md)
- [Encryption and data protection](06_Security_Privacy_Compliance/Encryption_and_Data_Protection.md)
- [Security monitoring, alarms & dashboards](06_Security_Privacy_Compliance/Security_Monitoring_Alarms_and_Dashboards.md)
- [AWS security baseline checklist](06_Security_Privacy_Compliance/AWS_Security_Baseline_Checklist.md)
- [Webhook secret rotation runbook](06_Security_Privacy_Compliance/Webhook_Secret_Rotation_Runbook.md)
- [Kill switch and safe mode](06_Security_Privacy_Compliance/Kill_Switch_and_Safe_Mode.md)
- [Incident response runbooks](06_Security_Privacy_Compliance/Incident_Response_Security_Runbooks.md)
- [Compliance readiness checklist](06_Security_Privacy_Compliance/Compliance_Readiness_Checklist.md)
- [Wave 06 definition of done](06_Security_Privacy_Compliance/Wave06_Definition_of_Done_Checklist.md)

---

## 07 — Reliability and scaling
- [Capacity plan and SLOs](07_Reliability_Scaling/Capacity_Plan_and_SLOs.md)
- [Concurrency and throughput model](07_Reliability_Scaling/Concurrency_and_Throughput_Model.md)
- [SQS FIFO strategy and limits](07_Reliability_Scaling/SQS_FIFO_Strategy_and_Limits.md)
- [Resilience patterns and timeouts](07_Reliability_Scaling/Resilience_Patterns_and_Timeouts.md)
- [Failure modes and recovery](07_Reliability_Scaling/Failure_Modes_and_Recovery.md)
- [Tuning playbook and degraded modes](07_Reliability_Scaling/Tuning_Playbook_and_Degraded_Modes.md)
- [Backlog catch-up and replay strategy](07_Reliability_Scaling/Backlog_Catchup_and_Replay_Strategy.md)
- [Rate limiting and backpressure](07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md)
- [Load testing and soak test plan](07_Reliability_Scaling/Load_Testing_and_Soak_Test_Plan.md)
- [Service quotas and operational limits](07_Reliability_Scaling/Service_Quotas_and_Operational_Limits.md)
- [DR and business continuity posture](07_Reliability_Scaling/DR_and_Business_Continuity_Posture.md)
- [Cost guardrails and budgeting](07_Reliability_Scaling/Cost_Guardrails_and_Budgeting.md)
- [Cost model](07_Reliability_Scaling/Cost_Model.md)
- [Wave 07 definition of done](07_Reliability_Scaling/Wave07_Definition_of_Done_Checklist.md)
- [Parameter defaults appendix](07_Reliability_Scaling/Parameter_Defaults_Appendix.md)
- [Parameter defaults YAML](07_Reliability_Scaling/parameter_defaults_v1.yaml)


---


## 08 — Observability, analytics, and eval ops
- [Observability overview](08_Observability_Analytics/Observability_Analytics_Overview.md)
- [Event taxonomy and log schema](08_Observability_Analytics/Event_Taxonomy_and_Log_Schema.md)
- [Metrics catalog and SLO instrumentation](08_Observability_Analytics/Metrics_Catalog_and_SLO_Instrumentation.md)
- [Tracing and correlation](08_Observability_Analytics/Tracing_and_Correlation.md)
- [Dashboards, alerts, and reports](08_Observability_Analytics/Dashboards_Alerts_and_Reports.md)
- [Operator quick start runbook](08_Observability_Analytics/Operator_Quick_Start_Runbook.md)
- [Cross-wave alignment map](08_Observability_Analytics/Cross_Wave_Alignment_Map.md)
- [Analytics data model and exports](08_Observability_Analytics/Analytics_Data_Model_and_Exports.md)
- [Quality monitoring and drift detection](08_Observability_Analytics/Quality_Monitoring_and_Drift_Detection.md)
- [EvalOps scheduling and runbooks](08_Observability_Analytics/EvalOps_Scheduling_and_Runbooks.md)
- [Feedback signals and override macros](08_Observability_Analytics/Feedback_Signals_and_Agent_Override_Macros.md)
- [Wave 08 definition of done](08_Observability_Analytics/Wave08_Definition_of_Done_Checklist.md)



## 08.5 — Engineering and repo workflow
- [Branch protection and merge settings](08_Engineering/Branch_Protection_and_Merge_Settings.md)
- [Developer guide](08_Engineering/Developer_Guide.md)
- [Repository conventions](08_Engineering/Repository_Conventions.md)
- [GitHub workflow and repo standards](08_Engineering/GitHub_Workflow_and_Repo_Standards.md)
- [Multi-agent GitOps playbook](08_Engineering/Multi_Agent_GitOps_Playbook.md)
- [CI and GitHub Actions runbook](08_Engineering/CI_and_Actions_Runbook.md)
- [Protected paths and safe deletion rules](08_Engineering/Protected_Paths_and_Safe_Deletion_Rules.md)

---

## 08 — Testing and quality
- [Test strategy and matrix](08_Testing_Quality/Test_Strategy_and_Matrix.md)
- [Integration test plan](08_Testing_Quality/Integration_Test_Plan.md)
- [Contract tests and schema validation](08_Testing_Quality/Contract_Tests_and_Schema_Validation.md)
- [Manual QA checklists](08_Testing_Quality/Manual_QA_Checklists.md)
- [Smoke test pack](08_Testing_Quality/Smoke_Test_Pack_v1.md)
- [Load and soak testing](08_Testing_Quality/Load_and_Soak_Testing.md)
- [Test data and fixtures](08_Testing_Quality/Test_Data_and_Fixtures.md)
- [LLM evals in CI](08_Testing_Quality/LLM_Evals_in_CI.md)
- [LLM regression gates checklist](08_Testing_Quality/LLM_Regression_Gates_Checklist.md)
- [Wave 09 definition of done](08_Testing_Quality/Wave09_Definition_of_Done_Checklist.md)

---

## 09 — Deployment and operations
- [Environments](09_Deployment_Operations/Environments.md)
- [CI/CD plan](09_Deployment_Operations/CICD_Plan.md)
- [Release and rollback](09_Deployment_Operations/Release_and_Rollback.md)
- [First production deploy runbook](09_Deployment_Operations/First_Production_Deploy_Runbook.md)
- [Go/No-Go checklist](09_Deployment_Operations/Go_No_Go_Checklist.md)
- [Runbooks](09_Deployment_Operations/Runbooks.md)

---

## 10 — Operations, runbooks, training
- [Operations handbook](10_Operations_Runbooks_Training/Operations_Handbook.md)
- [Runbook index](10_Operations_Runbooks_Training/Runbook_Index.md)
- [Runbook signal map (CSV)](10_Operations_Runbooks_Training/runbook_signal_map_v1.csv)
- [On-call and escalation](10_Operations_Runbooks_Training/On_Call_and_Escalation.md)
- [Operational cadence and checklists](10_Operations_Runbooks_Training/Operational_Cadence_and_Checklists.md)
- [Training guide for support teams](10_Operations_Runbooks_Training/Training_Guide_for_Support_Teams.md)
- [Wave 10 definition of done](10_Operations_Runbooks_Training/Wave10_Definition_of_Done_Checklist.md)

---

## 11 — Governance
- [Governance program overview](11_Governance_Continuous_Improvement/Governance_Program_Overview.md)
- [Governance quick start](11_Governance_Continuous_Improvement/Governance_Quick_Start.md)
- [Governance audit checklist](11_Governance_Continuous_Improvement/Governance_Audit_Checklist.md)
- [Ownership and RACI](11_Governance_Continuous_Improvement/Artifact_Ownership_RACI.md)
- [Governance cadence and ceremonies](11_Governance_Continuous_Improvement/Governance_Cadence_and_Ceremonies.md)
- [Governance meeting templates](11_Governance_Continuous_Improvement/Governance_Meeting_Templates.md)
- [Change management](11_Governance_Continuous_Improvement/Change_Management.md)
- [Model update policy](11_Governance_Continuous_Improvement/Model_Update_Policy.md)
- [Taxonomy drift and calibration](11_Governance_Continuous_Improvement/Taxonomy_Drift_and_Calibration.md)
- [Versioning rules (prompts/templates/schemas)](11_Governance_Continuous_Improvement/Prompt_Template_Schema_Versioning.md)
- [Procedures: add intents/teams/templates](11_Governance_Continuous_Improvement/Procedures_Adding_Intents_Teams_Templates.md)
- [Continuous improvement loop](11_Governance_Continuous_Improvement/Continuous_Improvement_Loop.md)
- [Vendor change management](11_Governance_Continuous_Improvement/Vendor_Change_Management.md)
- [Wave 11 Definition of Done](11_Governance_Continuous_Improvement/Wave11_Definition_of_Done_Checklist.md)

## 12 — Execution packs
- [Execution packs README](12_Cursor_Agent_Work_Packages/README.md)
- [Execution pack overview](12_Cursor_Agent_Work_Packages/00_Overview/Execution_Pack_Overview.md)
- [Implementation sequence (sprints)](12_Cursor_Agent_Work_Packages/00_Overview/Implementation_Sequence_Sprints.md)
- [V1 cutline and post‑v1 backlog](12_Cursor_Agent_Work_Packages/00_Overview/V1_Cutline_and_Backlog.md)
- [Jira import instructions](12_Cursor_Agent_Work_Packages/00_Overview/Jira_Import_Instructions.md)
- [Work breakdown structure](12_Cursor_Agent_Work_Packages/01_Work_Breakdown/Work_Breakdown_Structure.md)
- [Dependency map](12_Cursor_Agent_Work_Packages/01_Work_Breakdown/Dependency_Map.md)
- [Tickets index](12_Cursor_Agent_Work_Packages/03_Tickets/TICKETS_INDEX.md)

---

## Risks, common issues, and waves
- [Common issues mitigation matrix](90_Risks_Common_Issues/Common_Issues_Mitigation_Matrix.md)
- [Waves folder](Waves/)
---

## 98 — Agent ops (AI workflow, policies, templates)
- [AI worker retrieval workflow](98_Agent_Ops/AI_Worker_Retrieval_Workflow.md)
- [Agent ops overview](98_Agent_Ops/README.md)
- [Chunking & indexing standard](98_Agent_Ops/Chunking_and_Indexing_Standard.md)
- [Rehydration Pack spec](98_Agent_Ops/Rehydration_Pack_Spec.md)
- [Validation and automation](98_Agent_Ops/Validation_and_Automation.md)
- [Policies](98_Agent_Ops/Policies/INDEX.md)
- [Run/report templates](98_Agent_Ops/Templates/)
