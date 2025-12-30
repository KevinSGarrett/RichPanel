# Vendor Doc Crosswalk — Richpanel

Last updated: 2025-12-29

Purpose: map our **canonical integration specs** to the most relevant **Richpanel vendor reference docs**.

Use this when you need to confirm platform behavior (triggers, payload, retries, limits) without browsing the entire reference dump.

Vendor reference indexes:
- `reference/richpanel/TOP_20.md`
- `reference/richpanel/INDEX.md`

---

## Crosswalk table

| Canonical spec (our plan) | What to confirm | Vendor reference docs |
|---|---|---|
| `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md` | Webhook triggers, ACK-fast behavior, safe ingestion patterns | [Comprehensive Guide — Acknowledge Quickly](../reference/richpanel/Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Receiving the Webhook in Your Middleware/Acknowledge Quickly.txt)<br>[Comprehensive Guide — Verify the Source](../reference/richpanel/Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Receiving the Webhook in Your Middleware/Verify the Source.txt)<br>[Richpanel Integration — Official entry points (Stability)](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Official_Integration_Entry_Points/Stability.txt) |
| `docs/03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md` | API authentication, error responses, request patterns | [API — Getting started](../reference/richpanel/Non_Indexed_Library/API/Getting_Started_RichPanel_API.txt)<br>[API — Authentication](../reference/richpanel/Non_Indexed_Library/API/Authentication.txt)<br>[API — Errors](../reference/richpanel/Non_Indexed_Library/API/Errors.txt) |
| `docs/03_Richpanel_Integration/Idempotency_Retry_Dedup.md` | Delivery guarantees, duplicate calls, success/timeout codes, dedup keys | [Reliability — Delivery Guarantees for HTTP Targets](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Reliability and Retries of HTTP Targets & API Calls/Delivery Guarantees for HTTP Targets.txt)<br>[Reliability — Duplicate Calls](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Reliability and Retries of HTTP Targets & API Calls/Duplicate Calls.txt)<br>[HTTP Target Payload — Including IDs and Deduplication Keys](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/HTTP Target Payload and Available Fields/Including IDs and Deduplication Keys.txt) |
| `docs/03_Richpanel_Integration/Team_Tag_Mapping_and_Drift.md` | Teams/departments concept + safest routing primitives | [Routing — Department concept](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Routing Primitives Teams (Departments) and Ticket Assignment/Department_Concept.txt)<br>[Routing — Cleanest routing approach](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Routing Primitives Teams (Departments) and Ticket Assignment/Cleanest Routing Approach.txt)<br>[Routing — Routing ticket to the right queue](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Routing Primitives Teams (Departments) and Ticket Assignment/Routing Ticket To The Right Queue.txt) |
| `docs/05_FAQ_Automation/FAQ_Automation_Dedup_Rate_Limits.md` | Rate limits, throughput constraints, scaling patterns | [Scalability — API Rate Limits](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Scalability Limits and Best Practices/API Rate Limits.txt)<br>[Scalability — Parallelism and Queueing](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Scalability Limits and Best Practices/Parallelism and Queueing.txt)<br>[API — Limitations](../reference/richpanel/Non_Indexed_Library/API/Limitations.txt) |
| `docs/03_Richpanel_Integration/Automation_Rules_and_Config_Inventory.md` | Automation interactions and loop prevention patterns | [Automation loops — processed flag](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Automation Rule Interactions & Preventing Loops/Use A Processed Flag.txt)<br>[Automation loops — trigger on customer message only](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Automation Rule Interactions & Preventing Loops/Trigger On Customer Message Only.txt)<br>[Comprehensive Guide — Don’t Re-trigger on API Actions](../reference/richpanel/Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Avoiding Automation Loops/Don’t Re-trigger on API Actions.txt) |
| `docs/06_Security_Privacy_Compliance/Security_Privacy_Compliance_Overview.md` | Webhook security, least privilege, audit logging | [Security & Long-Term Support — Secure Webhook Calls](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Security, Compliance, and Long-Term Support/Secure Webhook Calls.txt)<br>[Comprehensive Guide — Principle of Least Privilege](../reference/richpanel/Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Security and Compliance/Principle of Least Privilege.txt)<br>[Comprehensive Guide — Audit Logging](../reference/richpanel/Non_Indexed_Library/Developing Middleware for Richpanel Comprehensive Guide/Security and Compliance/Audit Logging.txt) |
| `docs/09_Deployment_Operations/Release_and_Rollback.md` | Sandbox/testing and staged rollout strategy (progressive enablement) | [Testing safely — Sandbox Environment](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Testing Safely Sandbox and Rollout Strategy/Sandbox Environment.txt)<br>[Testing safely — Rollout Plan](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Testing Safely Sandbox and Rollout Strategy/Rollout Plan – Shadow to Full.txt)<br>[Testing safely — Testing Flows Without Impacting Production](../reference/richpanel/Non_Indexed_Library/Richpanel_Integration/Testing Safely Sandbox and Rollout Strategy/Testing Flows Without Impacting Production.txt) |
| `docs/05_FAQ_Automation/Order_Status_Automation.md` | Order event structure examples for mapping | [Order event — Sample Order Event](../reference/richpanel/Non_Indexed_Library/Order_Event_Structure/Sample_Order_Event.txt)<br>[Order event — Order Properties](../reference/richpanel/Non_Indexed_Library/Order_Event_Structure/Order_Properties.txt) |

---

## Notes

- Vendor docs are raw `.txt` files; treat them as reference for platform behavior.
- If vendor docs contradict the plan, update `docs/00_Project_Admin/Decision_Log.md` and/or the relevant spec explicitly (don’t silently drift).
