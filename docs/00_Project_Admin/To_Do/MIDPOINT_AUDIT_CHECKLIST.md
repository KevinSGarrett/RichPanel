# Midpoint Audit Checklist (WaveAudit ??? Repo Tasks)

Last updated: 2026-01-10 ??? RUN_20260110_1445Z

This checklist converts **WaveAudit** findings into **repo-native, evidence-backed** tasks.

## Owners (A/B/C)

- **A**: Engineering / integrations / CI enforcement
- **B**: LLM behavior + routing policy + product alignment
- **C**: QA / observability / Richpanel ops configuration + enablement

## Evidence rules (per checkbox)

Each completed item must include concrete evidence (at least one, ideally more):

- **PR evidence**: commit/PR link + key diff excerpt(s)
- **Docs evidence**: updated doc link + section heading(s)
- **Ops evidence**: screenshot/export of Richpanel rule/view/tag library (stored under `qa/test_evidence/` or linked)
- **Test evidence**: executed test case IDs + logs + screenshots (see `docs/08_Testing_Quality/Test_Evidence_Log.md`)
- **Run evidence**: `REHYDRATION_PACK/RUNS/<RUN_ID>/*/RUN_REPORT.md` (commands + outputs)

---

## 0) Alignment: personalization strategy (mismatch resolution)

> WaveAudit doc `WaveAudit/04_Message_Personalization_Strategy.md` recommends template-only replies.
> Project direction is **guardrailed OpenAI rewrite** (deterministic facts ??? rewrite for tone/uniqueness ??? validate ??? fallback).

- [ ] **MP-WA-ALIGN-001 ??? Document the ???guardrailed rewrite layer??? decision**
  - **Owner**: B
  - **Evidence required**: Decision entry (or equivalent) + updated product/policy doc(s) showing ???rewrite + validation + deterministic fallback??? + rollout gating (???OFF by default???, proof windows)

- [ ] **MP-WA-ALIGN-002 ??? Define rewrite safety contract**
  - **Owner**: B
  - **Evidence required**: Written constraints covering ???no new facts/promises/PII???, length bounds, failure fallback behavior, and log redaction policy

---

## 1) Documentation updates (WaveAudit remediation)

- [ ] **PLN-WA001 ??? Add ???Customer Replies to Auto-Closed Tickets??? section**
  - **Owner**: C
  - **Evidence required**: Updated `docs/05_FAQ_Automation/Order_Status_Automation.md` section + link to routing policy + mention of ???no 2nd auto-reply on reopen???

- [ ] **PLN-WA002 ??? Add ???Personalization Strategy??? section (rewrite layer, not template-only)**
  - **Owner**: B
  - **Evidence required**: Updated `docs/05_FAQ_Automation/Order_Status_Automation.md` describing deterministic message ??? OpenAI rewrite ??? validation ??? fallback

- [ ] **PLN-WA003 ??? Add ???Pre-Launch Validation Checklist??? section**
  - **Owner**: C
  - **Evidence required**: Updated `docs/05_FAQ_Automation/Order_Status_Automation.md` validation checklist + links to test evidence locations

- [ ] **PLN-WA004 ??? Add ???Special Case: Reopened Tickets After Auto-Close??? section**
  - **Owner**: B
  - **Evidence required**: Updated `docs/01_Product_Scope_Requirements/Department_Routing_Spec.md` section with detection criteria + route-only policy

- [ ] **PLN-WA005 ??? Extend routing matrix for reopen scenarios**
  - **Owner**: B
  - **Evidence required**: Routing matrix rows for `reopened_after_auto_close` and `multiple_reopen_after_auto_close` (with tags + escalation notes)

- [ ] **PLN-WA006 ??? Create FAQ extensibility guide**
  - **Owner**: C
  - **Evidence required**: New `docs/05_FAQ_Automation/How_to_Add_New_FAQ.md` + walkthrough for adding one FAQ end-to-end

- [ ] **PLN-WA007 ??? Update product vision/non-goals to match rewrite approach**
  - **Owner**: B
  - **Evidence required**: Updated `docs/01_Product_Scope_Requirements/Product_Vision_and_Non_Goals.md` (or equivalent) explicitly describing rewrite layer + guardrails + fallback

- [ ] **PLN-WA008 ??? Document Richpanel automation rule spec for reopen routing**
  - **Owner**: C
  - **Evidence required**: Updated `docs/03_Richpanel_Integration/Richpanel_Config_Changes_v1.md` describing rule trigger/order/actions and tags

- [ ] **PLN-WA009 ??? Document human handoff for reopened tickets**
  - **Owner**: C
  - **Evidence required**: Updated `docs/05_FAQ_Automation/Human_Handoff_and_Escalation.md` section describing reopen handling and escalation tags

---

## 2) Richpanel configuration (ops)

- [ ] **PLN-WA010 ??? Create automation rule: ???Middleware ??? Route Reopened Tickets???**
  - **Owner**: C
  - **Evidence required**: Screenshot/export of rule (trigger: `mw-reopened-after-auto-close`; action: assign to Email Support Team; ordering documented)

- [ ] **PLN-WA011 ??? Add tags to Richpanel tag library**
  - **Owner**: C
  - **Evidence required**: Screenshot/export showing tags exist (at minimum: `mw-reopened-after-auto-close`, `requires-human-review`, `mw-persistent-issue`)

- [ ] **PLN-WA012 ??? Create saved view: ???Reopened After Auto-Close???**
  - **Owner**: C
  - **Evidence required**: Screenshot/export of view definition + filter (has tag `mw-reopened-after-auto-close`)

- [ ] **PLN-WA013 ??? Configure rule ordering for reopened ticket routing**
  - **Owner**: C
  - **Evidence required**: Screenshot/export showing rule order + ???skip subsequent rules??? setting (documented in the config doc)

---

## 3) Testing & validation (WaveAudit requirements)

> Store evidence under `qa/test_evidence/wave_audit/` and log results in `docs/08_Testing_Quality/Test_Evidence_Log.md`.

- [ ] **PLN-WA014 ??? Validate Richpanel reopen mechanics (Resolved ??? Open on customer reply)**
  - **Owner**: C
  - **Evidence required**: Screenshot of reopen + log excerpt showing status transition + evidence log entry

- [ ] **PLN-WA015 ??? Validate reopened ticket triggers webhook to middleware**
  - **Owner**: A
  - **Evidence required**: Captured webhook payload sample + middleware logs showing receipt + classification as reopen scenario

- [ ] **PLN-WA016 ??? Validate reopen routing end-to-end (tag + Richpanel rule assignment + no 2nd auto-reply)**
  - **Owner**: C
  - **Evidence required**: Conversation screenshots + logs showing `mw-reopened-after-auto-close` + assignment confirmation

- [ ] **PLN-WA017 ??? E2E: order status with tracking (auto-reply + auto-close)**
  - **Owner**: C
  - **Evidence required**: Test case evidence (template/response content + tags + close status + idempotency confirmation)

- [ ] **PLN-WA018 ??? E2E: order status without tracking, within SLA (ETA + auto-close)**
  - **Owner**: C
  - **Evidence required**: Logs proving business-day math + message output + close status

- [ ] **PLN-WA019 ??? E2E: order without tracking, outside SLA (route-only; no auto-close)**
  - **Owner**: C
  - **Evidence required**: Conversation + assignment evidence + proof ticket remained open

- [ ] **PLN-WA020 ??? Reopen within 24h: routes to Email Support; no 2nd auto-reply**
  - **Owner**: C
  - **Evidence required**: Reopen screenshots + routing/assignment proof + ???no second auto reply??? proof

- [ ] **PLN-WA021 ??? Multiple reopens: persistent issue tagging/escalation**
  - **Owner**: C
  - **Evidence required**: Evidence of `mw-persistent-issue` tag on 3rd reopen + escalation behavior proof (if configured)

- [ ] **PLN-WA022 ??? Idempotency: duplicate webhook delivery only replies once**
  - **Owner**: A
  - **Evidence required**: Logs showing duplicate detection + idempotency record + proof only one reply/action taken

- [ ] **PLN-WA023 ??? Rate limiting: repeated customer messages don???t spam replies**
  - **Owner**: A
  - **Evidence required**: Logs showing cooldown enforcement + tagging + proof replies suppressed within window

---

## 4) Implementation (middleware + behavior)

- [ ] **PLN-WA024 ??? Implement reopened-after-auto-close detection**
  - **Owner**: A
  - **Evidence required**: Code + unit tests covering detection criteria (mw-auto-replied + reopen signal + <7d rule) + logs proving deterministic behavior

- [ ] **PLN-WA025 ??? Ensure reopened tickets are route-only (no auto-reply)**
  - **Owner**: A
  - **Evidence required**: Code + tests proving no second outbound message is sent; tags applied for routing

- [ ] **MP-WA-IMPL-026 ??? Implement guardrailed rewrite layer (deterministic ??? rewrite ??? validate ??? fallback)**
  - **Owner**: A
  - **Evidence required**: Feature flag default-off + tests for ???rewrite success??? and ???rewrite rejected ??? fallback??? + proof no raw inbound ticket body is stored

- [ ] **MP-WA-IMPL-027 ??? Add rewrite validation rules + failure telemetry**
  - **Owner**: A
  - **Evidence required**: Validation policy documented + metrics/log events showing accept/reject/fallback counts

---

## 5) Observability / monitoring / alerting

- [ ] **PLN-WA026 ??? Add metric: reopened_tickets_count (+ dimensions)**
  - **Owner**: A
  - **Evidence required**: Metric emission code + example CloudWatch query/screenshot + run report proof (logs/metric data)

- [ ] **PLN-WA027 ??? Add structured logging for reopened scenarios**
  - **Owner**: A
  - **Evidence required**: Log event schema documented + example log lines captured in run report

- [ ] **PLN-WA030 ??? P1 alert: template (or rewrite category) reopen rate >20%**
  - **Owner**: C
  - **Evidence required**: Alarm definition + documented action plan (???pause automation???) + link to dashboard/query used

- [ ] **PLN-WA031 ??? P2 alert: global reopen rate >15%**
  - **Owner**: C
  - **Evidence required**: Alarm definition + escalation path + runbook entry

- [ ] **PLN-WA032 ??? P3 alert: persistent reopens spike**
  - **Owner**: C
  - **Evidence required**: Alarm definition + alert routing target

- [ ] **PLN-WA033 ??? Dashboard: reopened tickets + reopen rate by template/category**
  - **Owner**: C
  - **Evidence required**: Dashboard screenshot/link + documented widget list

---

## 6) Training, comms, and log hygiene

- [ ] **PLN-WA034 ??? Train Email Support Team on reopened ticket handling**
  - **Owner**: C
  - **Evidence required**: Training doc/slide link + attendance/ack record (or equivalent)

- [ ] **PLN-WA035 ??? Update operations handbook with reopen procedures**
  - **Owner**: C
  - **Evidence required**: Updated `docs/10_Operations_Runbooks_Training/Operations_Handbook.md` (or equivalent) section

- [ ] **PLN-WA036 ??? Share personalization decision (rewrite layer) with stakeholders**
  - **Owner**: B
  - **Evidence required**: Stakeholder summary artifact (doc/email) + link stored in repo (or referenced in logs)

- [ ] **PLN-WA037 ??? Update `CHANGELOG.md` with WaveAudit remediation**
  - **Owner**: B
  - **Evidence required**: Changelog entry referencing completed items and links to evidence

- [ ] **PLN-WA038 ??? Update `docs/00_Project_Admin/Progress_Log.md` when WaveAudit items land**
  - **Owner**: B
  - **Evidence required**: Progress log entry linking run folder + summarizing what shipped

- [ ] **PLN-WA039 ??? Update `REHYDRATION_PACK/02_CURRENT_STATE.md` to reflect reopen handling + FAQ extensibility status**
  - **Owner**: B
  - **Evidence required**: Current state update with links to shipped code/docs + evidence pointers
