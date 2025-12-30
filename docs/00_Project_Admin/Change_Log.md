# Change Log

> **Note:** This file originated from the planning library and may be partially legacy.
> The **canonical repository changelog** is: `CHANGELOG.md` (repo root).
> Keep `CHANGELOG.md` updated for all meaningful changes going forward.


Last updated: 2025-12-29
Last verified: 2025-12-23 — Wave 12 started (Update 1).

Track structural and major content changes wave-by-wave.

## 2025-12-21
- Created initial folder structure under `docs/`
- Added INDEX and CODEMAP
- Added initial wave schedule + rehydration
- Added skeleton documents for major plan areas
- Updated `07_Reliability_Scaling/Capacity_Plan_and_SLOs.md` with preliminary heatmap insights

## 2025-12-21 (Wave 01 progress update)
- Captured your answers to the initial gap questions (Shopify, identifier uncertainty, automation/integration strategy unknown, PII posture).
- Updated Wave 01 requirements docs with v0.1 content:
  - Product vision and non-goals
  - User journeys/workflows
  - Intent taxonomy v0.1 + intent→team mapping recommendations
  - FAQ automation scope + risk-tier policy
  - Success metrics and draft SLAs
- Updated admin trackers:
  - Progress/Wave schedule now marks Wave 01 as in progress
  - Open questions now include status markers (open/partial/closed)
  - Assumptions, decision log (proposed decisions), and risk register expanded
- Updated integration docs with v0.1 best-practice recommendations:
  - webhook/HTTP Target contract, ack-fast, idempotency basics
  - initial automation inventory notes from current setup snapshot
- Expanded Common Issues Mitigation Matrix to cover all 22 common issue files.
- Updated appendices `Data_Inputs.md` with extracted highlights from RoughDraft + heatmap.

## 2025-12-21 (Wave 01 update 2)
- Captured new input: `SC_Data_ai_ready_package.zip` (conversation/message dataset) and referenced it in plan inputs.
- Updated requirements docs with new confirmed decisions:
  - Order status auto-replies include tracking link + tracking number when deterministic match.
  - Chargebacks/disputes route to a dedicated Chargebacks/Disputes queue (no automation).
- Updated routing spec with:
  - recommended Chargebacks/Disputes queue as an explicit destination
  - recommended owner for missing items: Returns Admin (Fulfillment Exceptions).
- Updated admin trackers:
  - Open Questions, Decision Log, Risk Register, Rehydration, and Progress/Wave Schedule.
## 2025-12-21 (Wave 01 update 3)
- Answered new product policy questions and incorporated into docs:
  - Confirmed “auto-close only for whitelisted, deflection-safe templates (CR-001 adds order-status ETA exception)” policy
  - Added recommendations for chargeback queue implementation, missing-items ownership, and delivered-not-received handling
- Added new Richpanel integration doc:
  - `03_Richpanel_Integration/Queues_and_Routing_Primitives.md`
- Updated Richpanel integration docs:
  - `Webhooks_and_Event_Handling.md` (added order lookup approach)
  - `Richpanel_API_Contracts_and_Error_Handling.md` (added auth + order endpoints + validation checklist)
- Rewrote/expanded requirements docs:
  - `Department_Routing_Spec.md` (intent taxonomy v0.1 + mapping + tie-breakers)
  - `FAQ_Automation_Scope.md` (tiered policy, delivered-not-received default, auto-close confirmed)
  - `Customer_Message_Dataset_Insights.md` (added aggregate stats from SC_Data)
- Updated admin trackers:
  - `Decision_Log.md`, `Open_Questions.md`, `Assumptions_Constraints.md`, `Risk_Register.md`, `Progress_Wave_Schedule.md`, `Rehydration.md`
- Updated navigation:
  - `docs/INDEX.md` and `docs/CODEMAP.md` to include the new Queues doc
  - `docs/ROADMAP.md` marked Wave 01 as complete

## 2025-12-21 (Wave 02 update 1 — Architecture + Infra decisions)
- Selected best-suggested hosting stack:
  - AWS Serverless (API Gateway + Lambda + SQS FIFO + DynamoDB)
- Expanded system architecture documentation:
  - Updated `docs/02_System_Architecture/Architecture_Overview.md`
  - Updated `docs/02_System_Architecture/Hosting_Options_and_Recommendation.md`
  - Updated `docs/02_System_Architecture/Sequence_Diagrams.md`
  - Updated `docs/02_System_Architecture/Data_Flow_and_Storage.md`
  - Added `docs/02_System_Architecture/AWS_Serverless_Reference_Architecture.md`
- Defined baseline latency SLOs/SLAs for early rollout:
  - Updated `docs/07_Reliability_Scaling/Capacity_Plan_and_SLOs.md`
  - Updated `docs/01_Product_Scope_Requirements/Success_Metrics_and_SLAs.md`
- Expanded Richpanel config inventory using `04_SETUP_CONFIGURATION` snapshot:
  - documented existing chargeback auto-close rules and dispute macros
- Updated admin trackers:
  - Progress/Wave Schedule, Rehydration, Open Questions, Decision Log, Risk Register

## 2025-12-21 — Wave 02 Update 2
- Selected AWS region for v1 (`us-east-2`) and documented DR option (`us-west-2`).
- Selected environment strategy: separate AWS accounts for dev/staging/prod (Organizations/Control Tower recommended).
- Updated latency targets to treat LiveChat as the only real-time channel for v1.
- Added `02_System_Architecture/AWS_Region_and_Environment_Strategy.md`.
- Updated admin trackers (Decision Log, Open Questions, Assumptions, Rehydration, Progress).

## 2025-12-21 — Wave 02 Update 3
- Confirmed current state: **no AWS Organizations / Control Tower set up yet**.
- Documented a minimal “cloud foundation” plan using **AWS Organizations without Control Tower**:
  - added `02_System_Architecture/AWS_Organizations_Setup_Plan_No_Control_Tower.md`.
- Updated admin trackers and navigation to reflect the new AWS foundation plan.

- **2025-12-21** — Wave 02 Update 4: recorded AWS management account ownership (you) and confirmed Control Tower deferral; updated AWS Organizations setup plan + trackers.


## 2025-12-21 (Wave 02 Update 5)
- Added `docs/02_System_Architecture/DynamoDB_State_and_Idempotency_Schema.md` (minimal v1 state model + TTL rules)
- Expanded idempotency/retry/dedup rules and linked to DynamoDB schema
- Expanded `07_Reliability_Scaling/Rate_Limiting_and_Backpressure.md` with layered strategy (concurrency caps + token buckets + retry queues + DLQ)
- Updated `07_Reliability_Scaling/Cost_Model.md` with formula-based model + real 7-day traffic inputs from heatmap
- Added `07_Reliability_Scaling/Failure_Modes_and_Recovery.md` v1 skeleton runbook
- Updated `07_Reliability_Scaling/Capacity_Plan_and_SLOs.md` with full 7-day totals and daily ranges
- Updated AWS Serverless reference architecture and sequence diagrams to include idempotency + kill switch/shadow mode
- Updated admin trackers (progress schedule, rehydration, open questions, decisions, risks) and refreshed INDEX/CODEMAP links

## 2025-12-21 (Wave 02 closeout + Wave 03 kickoff)
- Closed Wave 02 by locking remaining infra decisions:
  - v1 audit trail = logs-only (defer optional DynamoDB audit-actions table)
  - v1 queues = single SQS FIFO queue (no separate LiveChat lane in v1)
- Started Wave 03 by adding build-ready Richpanel integration documentation:
  - Richpanel config changes v1 (Teams/Tags/Automations/HTTP Targets)
  - Webhook contract hardening (anti-spoof token + ACK-fast rules)
  - API endpoint list updates (tickets + tags + teams + order lookup)
  - Macro/template alignment doc for future FAQ automation
  - Integration test plan + draft execution tasks
- Updated INDEX navigation and added Structure Report for this update.

## 2025-12-22 (Wave 03 Update 2 — Integration hardening + legacy rule de-conflict)
- Updated Richpanel integration design to account for existing automation rules with **“skip subsequent rules”** toggles:
  - added explicit requirement that the middleware trigger rule must be **top-of-list** (or otherwise guaranteed to run first).
- Added a recommended **minimal HTTP Target payload** strategy (send only `conversation_id` + basic metadata; fetch full context via Richpanel API).
- Expanded inventory of current Richpanel assignment rules (reassign-even-if-assigned ON + triggers on every new message) and documented the routing-fight risk.
- Added the recommended mitigation: gate legacy assignment rules behind a middleware flag tag (`mw-routing-applied`) and/or disable “reassign even if already assigned”.
- Updated order-status automation notes with evidence that Richpanel order objects include tracking fields (tracking number + tracking URL), while still requiring tenant confirmation.
- Added aggregate identifier-in-message statistics from SC_Data (order # / tracking / phone / email presence rates) to support deterministic-match policy.
- Updated admin trackers (Progress/Wave Schedule, Decision Log, Open Questions, Rehydration, Change Log, INDEX/CODEMAP/ROADMAP).
- Added new Structure Report: `Structure_Report_Wave03_Update2.md`.

## 2025-12-22 (Wave 03 Update 3 — Tenant-capability clarifications + API path alignment)
- Corrected Richpanel API paths across Wave 03 docs:
  - standardized on `/v1/tickets/{id}` for “Conversation” GET/PUT
  - updated tag endpoints to `/v1/tickets/{id}/add-tags` and `/v1/tickets/{id}/remove-tags`
  - documented Attach Order endpoint (`/v1/tickets/{id}/attach-order/{appClientId}/{orderId}`)
- Refined middleware trigger strategy:
  - preferred placement as a **Tagging Rule** (top-of-list) to avoid being blocked by Assignment Rules using “skip subsequent rules”
  - fallback placement as first Assignment Rule
- Added a dedicated clarification doc:
  - `03_Richpanel_Integration/Tenant_Capabilities_Clarifications.md` (plain-English explanations + defaults + fallbacks)
- Updated verification tasks for Cursor agents:
  - added JSON-escaping test for `{{ticket.lastMessage.text}}`
  - updated API verification steps to use `/v1/tickets/{id}`
- Updated order status automation notes:
  - documented that `GET /v1/order/{conversationId}` returns `{}` when no linked order
  - documented tracking/status fields expected in order payloads
- Updated admin trackers:
  - Progress/Wave Schedule, Decision Log, Wave 03 notes

## 2025-12-22 (Wave 03 Update 4 — Plain-language Cursor verification tasks)
- Clarified that Richpanel “tenant capability” questions are **not** meant to be answered from memory by the project owner.
- Rewrote Wave 03 Cursor tasks in plain English with clear ✅/❌ deliverables:
  - `docs/Waves/Wave_03_Richpanel_Integration_Design/Cursor_Agent_Tasks.md`
- Added a 1-page summary checklist for agents:
  - `docs/Waves/Wave_03_Richpanel_Integration_Design/Cursor_Agent_Quick_Checklist_Plain_English.md`
- Updated `Tenant_Capabilities_Clarifications.md` to explicitly describe who performs checks and how fallbacks work.
- Updated admin trackers (`Progress_Wave_Schedule.md`, `Rehydration.md`, `Open_Questions.md`) to mark these items as “verify in tenant via Cursor” with non-blocking fallbacks.

## 2025-12-22 (Wave 03 Update 5 + Wave 04 start — Deferred tenant verification; LLM docs expanded)
- Marked Wave 03 tenant/UI verification as **deferred** per owner instruction (not blocking planning).
  - Updated: `docs/00_Project_Admin/Progress_Wave_Schedule.md`, `docs/00_Project_Admin/Open_Questions.md`
  - Updated: `docs/Waves/Wave_03_Richpanel_Integration_Design/Cursor_Agent_Tasks.md` (status set to deferred)
- Closed Wave 03 as “complete with deferred backlog” and started Wave 04.
- Expanded Wave 04 documentation:
  - Added intent taxonomy + labeling guide: `docs/04_LLM_Design_Evaluation/Intent_Taxonomy_and_Labeling_Guide.md`
  - Expanded prompting + JSON schema strategy: `docs/04_LLM_Design_Evaluation/Prompting_and_Output_Schemas.md`
  - Expanded confidence scoring + thresholds: `docs/04_LLM_Design_Evaluation/Confidence_Scoring_and_Thresholds.md`
  - Expanded safety and prompt injection defenses: `docs/04_LLM_Design_Evaluation/Safety_and_Prompt_Injection_Defenses.md`
  - Added model config and prompt versioning plan: `docs/04_LLM_Design_Evaluation/Model_Config_and_Versioning.md`
  - Added prompt library organization guide: `docs/04_LLM_Design_Evaluation/Prompt_Library_and_Templates.md`
  - Added Cursor tasks for Wave 04: `docs/Waves/Wave_04_LLM_Routing_Design/Cursor_Agent_Tasks.md`
- Added structure report: `docs/00_Project_Admin/Structure_Report_Wave03_Update5_Wave04_Start.md`



## 2025-12-22 (Wave 04 continuation — prompts/schemas + pipeline gating)
- Expanded v1 intent taxonomy to include missing Top FAQ intents (cancel/edit/subscription/billing/influencer).
- Created structured output schemas:
  - `schemas/mw_decision_v1.schema.json`
  - `schemas/mw_tier2_verifier_v1.schema.json`
- Created prompt artifacts:
  - `prompts/classification_routing_v1.md`
  - `prompts/tier2_verifier_v1.md`
- Added detailed pipeline spec:
  - `Decision_Pipeline_and_Gating.md`
- Updated LLM design docs to align with new artifacts:
  - Prompting/output schemas, prompt library, offline evaluation, safety, model config.
- Updated `Department_Routing_Spec.md` to align with v1 taxonomy.
- Expanded `LLM_Evals_in_CI.md` to define CI gate strategy.
- Updated Progress/Wave Schedule Wave 04 section with completed items + remaining exit criteria.


## 2025-12-22 (Wave 04 continued — thresholds, acceptance criteria, prototype notes)
- Added `00_Project_Admin/Roles_and_Tooling.md` to clarify planning vs implementation roles (ChatGPT vs Cursor).
- Added Wave 04 docs:
  - `04_LLM_Design_Evaluation/Acceptance_Criteria_and_Rollout_Stages.md`
  - `04_LLM_Design_Evaluation/Adversarial_and_Edge_Case_Test_Suite.md`
  - `04_LLM_Design_Evaluation/Prototype_Validation_Notes.md`
  - `04_LLM_Design_Evaluation/Prototype_Wave04_LLMEval_Report.md`
- Expanded and rewrote:
  - `04_LLM_Design_Evaluation/Confidence_Scoring_and_Thresholds.md` (v1 threshold defaults + calibration plan; data-informed)
  - `04_LLM_Design_Evaluation/Offline_Evaluation_Framework.md` (dataset profile + acceptance bands + prototype reference)
  - `04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md` (clarified “LLM is advisory; policy engine is authoritative”)
- Added optional reference artifacts:
  - `reference_artifacts/cursor_wave04_offline_eval_scaffold/` (non-production; docs remain source of truth)
- Updated navigation and trackers:
  - `INDEX.md`, `CODEMAP.md`, `Progress_Wave_Schedule.md`, `Rehydration.md`, `Decision_Log.md`
- Added structure report: `00_Project_Admin/Structure_Report_Wave04_Update3.md`

## 2025-12-22 (Wave 04 closeout)
- Added Golden Set labeling SOP + label schema:
  - `04_LLM_Design_Evaluation/Golden_Set_Labeling_SOP.md`
  - `04_LLM_Design_Evaluation/schemas/golden_example_v1.schema.json`
- Added deterministic multi-intent precedence rules:
  - `04_LLM_Design_Evaluation/Multi_Intent_Priority_Matrix.md`
- Added Template ID interface catalog (IDs only; copy deferred to Wave 05):
  - `04_LLM_Design_Evaluation/Template_ID_Catalog.md`
- Defined CI regression gates and updated CI eval documentation:
  - `08_Testing_Quality/LLM_Regression_Gates_Checklist.md`
  - Updated `08_Testing_Quality/LLM_Evals_in_CI.md`
- Updated Wave 04 notes + admin trackers to mark Wave 04 complete and set Wave 05 as next.

## 2025-12-22 (Wave 05 start — Update 1)
- Started Wave 05 (FAQ automation design) and added/updated:
  - `05_FAQ_Automation/00_Overview.md`
  - `05_FAQ_Automation/Templates_Library_v1.md`
  - `05_FAQ_Automation/templates/templates_v1.yaml`
  - `05_FAQ_Automation/Order_Status_Automation.md`
  - `05_FAQ_Automation/Top_FAQs_Playbooks.md`
  - `05_FAQ_Automation/Response_Templates_and_Tone.md`
  - `05_FAQ_Automation/Template_Rendering_and_Variables.md`
  - `05_FAQ_Automation/Macro_Alignment_and_Governance.md`
  - `05_FAQ_Automation/FAQ_Automation_Dedup_Rate_Limits.md`
  - `05_FAQ_Automation/Customer_Experience_Metrics.md`
- Rewrote admin schedule tracker to mark Wave 05 in progress:
  - `00_Project_Admin/Progress_Wave_Schedule.md`
- Updated interface/catalog + routing:
  - `04_LLM_Design_Evaluation/Template_ID_Catalog.md`
  - `01_Product_Scope_Requirements/Department_Routing_Spec.md`
- Updated navigation docs:
  - `INDEX.md`
  - `CODEMAP.md`


## 2025-12-22 (Wave 05 Update 2)
- Added brand constants file + policy link guidance:
  - `05_FAQ_Automation/templates/brand_constants_v1.yaml`
  - `05_FAQ_Automation/Brand_Constants_and_Policy_Links.md`
- Added stakeholder review pack:
  - `05_FAQ_Automation/Stakeholder_Review_and_Approval.md`
  - `05_FAQ_Automation/review/Template_Review_Checklist.csv`
- Added Richpanel AUTO macro execution artifacts:
  - `05_FAQ_Automation/Richpanel_AUTO_Macro_Setup_Checklist.md`
  - `05_FAQ_Automation/Richpanel_AUTO_Macro_Pack_v1.md`
  - `05_FAQ_Automation/templates/richpanel_auto_macro_mapping_v1.csv`
- Added sender identity + channel scope recommendations:
  - `05_FAQ_Automation/Automation_Sender_Identity_and_Channel_Scope.md`
- Added QA test cases for FAQ automation:
  - `05_FAQ_Automation/FAQ_Playbook_Test_Cases.md`
- Standardized placeholder format across docs and YAML to Mustache.
- Regenerated `Templates_Library_v1.md` from YAML to keep copy consistent.
- Updated navigation: `INDEX.md`, `CODEMAP.md`


## 2025-12-22 (Wave 05 closeout — Update 3)
- Closed Wave 05 with implementation-ready FAQ automation artifacts:
  - Added LiveChat variants for all enabled templates in `templates_v1.yaml`
  - Regenerated `Templates_Library_v1.md` from YAML
  - Finalized sender identity + channel scope decisions (LiveChat + Email; others route-only)
  - Finalized brand constants posture (safe defaults; links disabled by default)
  - Added `Pre_Launch_Copy_and_Link_Checklist.md` (prevents shipping placeholders)
  - Updated template review CSV to “baseline drafted” status
- Updated admin trackers: Progress schedule, Rehydration, Decision Log, ROADMAP, INDEX
- Added structure report: `Structure_Report_Wave05_Update3_Closeout.md`


## 2025-12-22 (Wave 06 start — Update 1)
- Renamed/relocated privacy folder:
  - `06_Data_Privacy_Observability/` → `06_Security_Privacy_Compliance/` (stubs left behind for backwards reference)
- Added Wave 06 security/privacy/compliance docs:
  - Security overview, data classification/PII inventory
  - Webhook auth + request validation
  - Secrets/key management
  - IAM least privilege + network security + encryption
  - Retention/access controls (expanded from stub)
  - STRIDE threat model + security controls matrix
  - Incident response runbooks
  - Vendor data handling checklist (OpenAI/Richpanel/Shopify)
- Updated Wave 06 notes + admin trackers (Progress, Rehydration, Open Questions, Decisions)


## 2025-12-22 (Wave 06 Update 2)
- Added AWS security baseline checklist (MD + CSV)
- Added kill switch / safe mode spec (runtime feature flags to disable automation quickly)
- Rewrote webhook auth + request validation doc (removed placeholders; clarified tiered options)
- Rewrote network/egress controls doc (WAF/throttling/SSRF defenses)
- Rewrote incident response runbooks (explicit kill switch steps)
- Rebuilt navigation artifacts:
  - `docs/INDEX.md` (curated links)
  - `docs/REGISTRY.md` (complete doc list; prevents orphan files)
  - `docs/ROADMAP.md` (fixed truncation)
  - `docs/CODEMAP.md` (registry + invariants)
- Updated admin trackers:
  - Progress/Wave schedule, risk register, decision log, rehydration

## 2025-12-22
- **Wave 06 Update 3** — Added security monitoring baseline (alarms + dashboards), webhook secret rotation runbook, IAM access review cadence + break-glass procedure, and Wave 06 definition-of-done checklist.
- Updated Wave 06 references in existing security docs (Secrets/IAM/Logging/Incident response) to link to the new runbooks.
- Updated trackers/navigation (INDEX, REGISTRY, ROADMAP, Progress schedule) and marked Wave 06 as complete.

## 2025-12-22 (Wave 07 start — Update 1)
- Started Wave 07 (Reliability / scaling / capacity & cost).
- Expanded reliability documentation set under `docs/07_Reliability_Scaling/`:
  - Updated `Capacity_Plan_and_SLOs.md` with percentiles, daily totals table, anomaly notes, and sizing formulas.
  - Added throughput and concurrency sizing: `Concurrency_and_Throughput_Model.md`
  - Added FIFO strategy guidance: `SQS_FIFO_Strategy_and_Limits.md`
  - Added resilience patterns + timeout defaults: `Resilience_Patterns_and_Timeouts.md`
  - Added load + soak + failure-injection test plan: `Load_Testing_and_Soak_Test_Plan.md`
  - Added service quotas checklist: `Service_Quotas_and_Operational_Limits.md`
  - Added DR posture (single-region multi-AZ): `DR_and_Business_Continuity_Posture.md`
  - Added cost guardrails: `Cost_Guardrails_and_Budgeting.md`
  - Added Wave 07 closeout artifacts: `Wave07_Definition_of_Done_Checklist.md`, `Parameter_Defaults_Appendix.md`
- Updated Wave 07 notes: `docs/Waves/Wave_07_Reliability_Scaling_Capacity/Wave_Notes.md`
- Updated admin trackers and navigation:
  - `Progress_Wave_Schedule.md` (Wave 07 in progress)
  - `Rehydration.md` (Wave 06 closed; Wave 07 started)
  - `Decision_Log.md` (reliability decisions recorded)
  - `Risk_Register.md` (added backlog catch-up cost risk)


## 2025-12-22 (Wave 07 Update 2 / Closeout)
- Finalized v1 runtime parameter defaults:
  - Added canonical YAML: `docs/07_Reliability_Scaling/parameter_defaults_v1.yaml`
  - Updated summary: `docs/07_Reliability_Scaling/Parameter_Defaults_Appendix.md`
- Added operations-focused reliability runbooks:
  - `Tuning_Playbook_and_Degraded_Modes.md`
  - `Backlog_Catchup_and_Replay_Strategy.md`
- Marked Wave 07 Definition of Done as complete.
- Updated Wave 07 notes and marked Wave 07 as complete in `Progress_Wave_Schedule.md`.
- Added admin reports: `Structure_Report_Wave07_Update2.md`, `Docs_Impact_Map_Wave07_Update2.md`.


## 2025-12-22 (Wave 08 start — Update 1)
- Started Wave 08 (Observability / analytics / EvalOps).
- Added new observability documentation set under `docs/08_Observability_Analytics/`:
  - `Observability_Analytics_Overview.md`
  - `Event_Taxonomy_and_Log_Schema.md`
  - `observability_event_taxonomy_v1.yaml`
  - `schemas/mw_observability_event_v1.schema.json`
  - `Metrics_Catalog_and_SLO_Instrumentation.md`
  - `Tracing_and_Correlation.md`
  - `Dashboards_Alerts_and_Reports.md` (+ `dashboards/cloudwatch_dashboard_stub_v1.json`)
  - `Analytics_Data_Model_and_Exports.md`
  - `Quality_Monitoring_and_Drift_Detection.md`
  - `EvalOps_Scheduling_and_Runbooks.md`
  - `Feedback_Signals_and_Agent_Override_Macros.md`
  - `Wave08_Definition_of_Done_Checklist.md`
- Updated Wave 08 notes: `docs/Waves/Wave_08_Observability_Analytics/Wave_Notes.md`
- Updated admin trackers and navigation:
  - `Progress_Wave_Schedule.md` (Wave 08 in progress)
  - `Rehydration.md` (Wave 07 closed; Wave 08 started)
  - `Decision_Log.md`, `Risk_Register.md`
  - `INDEX.md`, `CODEMAP.md`, `REGISTRY.md`, `ROADMAP.md`


## 2025-12-22 (Wave 08 Update 2 / Closeout)
- Added Wave 08 closeout operator and alignment artifacts:
  - `docs/08_Observability_Analytics/Operator_Quick_Start_Runbook.md`
  - `docs/08_Observability_Analytics/Cross_Wave_Alignment_Map.md`
- Performed cross-wave consistency alignment (Waves 06–08):
  - dashboards/alerts reference Wave 06 security and Wave 07 tuning as authoritative
  - metric catalog references the alignment map for field/metric consistency
- Updated EvalOps artifact storage guidance to support CloudWatch-only rollout (S3 export optional).
- Updated Wave 05 macro governance with Wave 08 feedback macro addendum.
- Closed open question: analytics export posture decided (CloudWatch-first required; S3 export optional).
- Marked Wave 08 Definition of Done cross-wave checks as complete.
- Updated trackers/navigation and marked Wave 08 as complete:
  - `Progress_Wave_Schedule.md`, `Rehydration.md`, `ROADMAP.md`, `Wave_Notes.md`
  - regenerated `REGISTRY.md` after adding new files.


## 2025-12-22 (Wave 09 Update 1 — started testing/QA/release readiness)
- Expanded testing docs under `docs/08_Testing_Quality/`:
  - Test strategy + matrix (full)
  - Load/soak testing plan
  - Integration test plan
  - Contract tests + schema validation plan
  - Manual QA checklists
  - Test data/fixtures guidance
- Expanded deployment/release docs under `docs/09_Deployment_Operations/`:
  - CI/CD plan (gates + artifact promotion)
  - Environments plan (dev/staging/prod + safe defaults)
  - Release/rollback plan (progressive enablement)
  - Added Go/No-Go checklist
- Updated admin trackers:
  - Progress/Wave schedule now marks Wave 09 in progress (Update 1)
  - Decision log updated with Wave 09 decisions
  - Risk register expanded with staging realism risk
- Regenerated `docs/REGISTRY.md` and updated `docs/INDEX.md` navigation links

## 2025-12-22 (Wave 09 Update 2 — closeout)
- Added a v1 smoke test pack:
  - `docs/08_Testing_Quality/Smoke_Test_Pack_v1.md`
  - `docs/08_Testing_Quality/smoke_tests/smoke_test_cases_v1.csv`
- Added a step-by-step first production deploy runbook:
  - `docs/09_Deployment_Operations/First_Production_Deploy_Runbook.md`
- Tightened Go/No-Go checklist to require smoke pack evidence and runbook adherence.
- Updated LLM regression gates checklist to reference release-level smoke execution.
- Updated Wave 09 DoD checklist and Wave 09 notes to mark the wave **complete**.
- Updated trackers/navigation and regenerated `docs/REGISTRY.md`.

## 2025-12-22 — Wave 10 Update 1 (Operations / Runbooks / Training)

- Added Wave 10 operations documentation:
  - `docs/10_Operations_Runbooks_Training/Operations_Handbook.md`
  - `docs/10_Operations_Runbooks_Training/Runbook_Index.md`
  - `docs/10_Operations_Runbooks_Training/On_Call_and_Escalation.md`
  - `docs/10_Operations_Runbooks_Training/Operational_Cadence_and_Checklists.md`
  - `docs/10_Operations_Runbooks_Training/Training_Guide_for_Support_Teams.md`
  - `docs/10_Operations_Runbooks_Training/training/Richpanel_Agent_Override_and_Feedback.md`
  - Incident templates:
    - `docs/10_Operations_Runbooks_Training/templates/Incident_Comms_Templates.md`
    - `docs/10_Operations_Runbooks_Training/templates/Postmortem_Template.md`
  - Runbooks (initial set):
    - `docs/10_Operations_Runbooks_Training/runbooks/R001_Webhook_Failures_and_Duplicate_Storms.md`
    - `docs/10_Operations_Runbooks_Training/runbooks/R002_Misrouting_Spike.md`
    - `docs/10_Operations_Runbooks_Training/runbooks/R003_Automation_Wrong_Reply_or_PII_Risk.md`
    - `docs/10_Operations_Runbooks_Training/runbooks/R004_Vendor_Rate_Limit_Storm.md`
    - `docs/10_Operations_Runbooks_Training/runbooks/R005_Backlog_Catchup_and_DLQ.md`
    - `docs/10_Operations_Runbooks_Training/runbooks/R006_Cost_Spike_Token_Runaway.md`
    - `docs/10_Operations_Runbooks_Training/runbooks/R007_Order_Status_Automation_Failure.md`
    - `docs/10_Operations_Runbooks_Training/runbooks/R008_Chargebacks_Disputes_Process.md`
    - `docs/10_Operations_Runbooks_Training/runbooks/R009_Shipping_Exceptions_Returns_Workflow.md`
    - `docs/10_Operations_Runbooks_Training/runbooks/R010_Prompt_or_Template_Change_Release.md`
- Added Wave 10 DoD checklist:
  - `docs/10_Operations_Runbooks_Training/Wave10_Definition_of_Done_Checklist.md`
- Aligned folder numbering with wave schedule:
  - Governance moved: `docs/10_Governance_Continuous_Improvement/` → `docs/11_Governance_Continuous_Improvement/`
  - Cursor packs moved: `docs/11_Cursor_Agent_Work_Packages/` → `docs/12_Cursor_Agent_Work_Packages/`
  - Stub `MOVED.md` files added at old paths.
- Updated navigation and tracking:
  - `docs/INDEX.md`, `docs/CODEMAP.md`, `docs/ROADMAP.md`, `docs/REGISTRY.md`
  - `docs/00_Project_Admin/Progress_Wave_Schedule.md`, `docs/00_Project_Admin/Rehydration.md`, `docs/00_Project_Admin/Decision_Log.md`



## 2025-12-22 — Wave 10 Update 2
- Added standardized per-runbook sections: dashboards/metrics/log queries, operator levers, smoke-test verification.
- Added Runbook Index quick mapping table and machine-readable mapping CSV.
- Added “After mitigation: verify and restore” section to Operations Handbook.
- Marked Wave 10 Definition of Done checklist complete.

## 2025-12-22 — Wave 11 Update 1
- Started Wave 11 governance documentation.
- Expanded change management, model update policy, and taxonomy drift calibration docs.
- Added governance overview, RACI, cadence, meeting templates, versioning rules, and extension procedures.
- Updated trackers and navigation (INDEX/ROADMAP/REGISTRY) to reflect Wave 11 started.



## 2025-12-22 — Wave 11 Update 2
- Added Governance Quick Start and Governance Audit Checklist.
- Rewrote Wave 11 Definition of Done checklist and marked all items complete.
- Updated Wave 11 notes, Progress tracker, and Roadmap to mark Wave 11 complete.
- Updated INDEX and regenerated REGISTRY to include the new governance docs.

## 2025-12-23
- Started Wave 12 (Execution packs).
- Added `docs/12_Cursor_Agent_Work_Packages/` execution pack contents: overview, WBS, dependency map, epics, 49 build tickets, Cursor run prompts, CSV assets.
- Updated INDEX, ROADMAP, Progress schedule, Rehydration, CODEMAP, Decision Log.

## 2025-12-23 — Wave 12 Update 2 (Execution packs closeout)

- Added sprint-by-sprint implementation sequence (`Implementation_Sequence_Sprints.md`) and machine-readable sprint plan CSV.
- Added v1 cutline vs post-v1 backlog (`V1_Cutline_and_Backlog.md`) with priority classification (P0/P1/P2).
- Updated ticket asset CSV to include points/priority/sprint metadata; added epic points summary CSV.
- Added Jira import CSVs + instructions (two-pass epic → tasks import workflow).
- Updated Wave 12 notes and project trackers to mark **Wave 12 complete** (documentation ready for implementation).

