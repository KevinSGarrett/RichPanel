# Structure Report — Wave 03 Update 2

Date: 2025-12-22  
Scope: Wave 03 (Richpanel integration design hardening)

---

## 1) What was scanned
- Scanned the entire `docs/` tree for this documentation repo.
- Total files under `docs/`: **90**

---

## 2) Key outcomes (what changed conceptually)
1) **Automation ordering constraint captured**
   - Middleware trigger must run before rules that use “Skip all subsequent rules”.
2) **Webhook payload simplified**
   - Plan default: minimal payload (conversation_id only) + fetch context via API.
3) **Legacy routing fight risk documented + mitigations proposed**
   - Guard legacy rules behind `mw-routing-applied` and/or disable “reassign even if already assigned”.
4) **Order tracking field evidence added**
   - Richpanel order schema includes tracking number + tracking URL fields (tenant confirmation still required).
5) **Data-driven identifier scarcity documented**
   - Regex-based stats show order/tracking rarely appear in first message text; supports deterministic-match + ask-for-order-number fallback.
6) **Assumptions + risks updated**
   - Captured automation ordering assumption and updated automation conflict risk mitigations.

---

## 3) Files updated (and why)
- `README.md`
- `docs/ROADMAP.md`
- `docs/CODEMAP.md`
- `docs/INDEX.md`
- `docs/00_Project_Admin/Change_Log.md`
- `docs/00_Project_Admin/Progress_Wave_Schedule.md`
- `docs/00_Project_Admin/Decision_Log.md`
- `docs/00_Project_Admin/Open_Questions.md`
- `docs/00_Project_Admin/Rehydration.md`
- `docs/01_Product_Scope_Requirements/Customer_Message_Dataset_Insights.md`
- `docs/03_Richpanel_Integration/Webhooks_and_Event_Handling.md`
- `docs/03_Richpanel_Integration/Automation_Rules_and_Config_Inventory.md`
- `docs/03_Richpanel_Integration/Richpanel_Config_Changes_v1.md`
- `docs/03_Richpanel_Integration/Richpanel_API_Contracts_and_Error_Handling.md`
- `docs/05_FAQ_Automation/Order_Status_Automation.md`
- `docs/99_Appendices/Data_Inputs.md`
- `docs/Waves/Wave_03_Richpanel_Integration_Design/Wave_Notes.md`
- `docs/Waves/Wave_03_Richpanel_Integration_Design/Cursor_Agent_Tasks.md`
- `docs/00_Project_Admin/Assumptions_Constraints.md`
- `docs/00_Project_Admin/Risk_Register.md`

---

## 4) New files created
- `docs/00_Project_Admin/Structure_Report_Wave03_Update2.md` (this file)

---

## 5) Files reviewed but unchanged
- All other docs were scanned; no content changes were required in this update.

---

## 6) Follow-ups / next actions (to complete Wave 03)
- Confirm Richpanel tenant UI capabilities:
  - rule ordering (drag/drop)
  - “Tags does not contain …” condition support
  - HTTP Target payload templating variables
  - whether a message_id is available in inbound triggers
- Capture real API payload samples (staging) for:
  - conversation retrieval (where message text lives, attachment representation)
  - order linkage and tracking field population
- Lock final v1 webhook contract and Richpanel config checklist for implementation.
