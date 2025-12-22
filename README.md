# Richpanel Middleware Project Plan (Documentation)

Last updated: 2025-12-22

This folder contains the end-to-end, production-grade **project plan** for building a middleware that:

1) Routes inbound Richpanel customer messages to the correct department/team using an LLM + confidence scoring  
2) Safely automates top FAQs (starting with order status & tracking)  
3) Falls back to humans when confidence is low, content is ambiguous, or required data is missing  
4) Applies defense-in-depth: idempotency, rate limits, PII handling, prompt-injection controls, and kill switches

---

## How we work (waves)
We build and refine the plan in **waves** (see `docs/00_Project_Admin/Progress_Wave_Schedule.md`).

After each update:
- this documentation folder is updated
- you re-upload the updated zip (so the plan persists)
- we proceed to the next wave

---

## Roles (so there’s no confusion)
- **ChatGPT (project plan manager):** produces and maintains the documentation plan (this repository).  
  This includes architecture, routing logic, templates/copy, policy gating, evaluation plans, and operational runbooks.

- **Cursor agents (builders):** implement the plan when you start building.  
  Cursor usage during planning is optional and only used if it reduces ambiguity or validates feasibility.

> In other words: we can complete the planning work without Cursor. Cursor becomes the worker agent once you begin implementation.

---

## Where to start reading
If you only read 6 files:

1) `docs/00_Project_Admin/Progress_Wave_Schedule.md`  
2) `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md`  
3) `docs/04_LLM_Design_Evaluation/Decision_Pipeline_and_Gating.md`  
4) `docs/04_LLM_Design_Evaluation/Template_ID_Catalog.md`  
5) `docs/05_FAQ_Automation/Templates_Library_v1.md`  
6) `docs/05_FAQ_Automation/Order_Status_Automation.md`

