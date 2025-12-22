# Docs Index

Last updated: 2025-12-22  
Last verified: 2025-12-22 — Wave 06 Update 3 complete (closeout)

Use this as the master navigation for the project plan.

Quick start:
- [Progress & Wave Schedule](00_Project_Admin/Progress_Wave_Schedule.md)
- [Roadmap](ROADMAP.md)
- [CODEMAP](CODEMAP.md)
- [Docs Registry (all files)](REGISTRY.md)

---

## 00 — Project administration
- [Rehydration](00_Project_Admin/Rehydration.md)
- [Open Questions](00_Project_Admin/Open_Questions.md)
- [Assumptions & Constraints](00_Project_Admin/Assumptions_Constraints.md)
- [Decision Log](00_Project_Admin/Decision_Log.md)
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
- [Rate limiting and backpressure](07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md)
- [Cost model](07_Reliability_Scaling/Cost_Model.md)

---

## 08 — Testing and quality
- [LLM evals in CI](08_Testing_Quality/LLM_Evals_in_CI.md)
- [LLM regression gates checklist](08_Testing_Quality/LLM_Regression_Gates_Checklist.md)

---

## 09 — Deployment and operations
- [Release and rollback](09_Deployment_Operations/Release_and_Rollback.md)

---

## 10 — Governance
- (see `10_Governance_Continuous_Improvement/`)

## 11 — Execution packs
- (see `11_Cursor_Agent_Work_Packages/`)

---

## Risks, common issues, and waves
- [Common issues mitigation matrix](90_Risks_Common_Issues/Common_Issues_Mitigation_Matrix.md)
- [Waves folder](Waves/)

