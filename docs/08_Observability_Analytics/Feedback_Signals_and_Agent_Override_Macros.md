# Feedback Signals and Agent Override Macros (Wave 08)

Last updated: 2025-12-22

This document defines how we collect **high-signal human feedback** to improve routing and automation safely.

Why this matters:
- LLM confidence scores alone do not tell us if a route was *correct*.
- The fastest way to improve is to capture **explicit corrections** from agents during normal work.

This wave defines a **minimal, low-friction** feedback design.

---

## 1) Design goals
- Minimal agent effort (1 click macro)
- No PII in feedback artifacts
- Structured enough to power:
  - drift detection
  - training set expansion
  - routing bug triage

---

## 2) Minimal feedback tags (v1 recommended)

These tags are safe to store and analyze (no PII).  
They should be added by macros (preferred) or manually.

### Core tags
- `mw_feedback_misroute`  
  Meaning: middleware routed to the wrong department/team.

- `mw_feedback_auto_reply_wrong`  
  Meaning: automation reply was incorrect or unhelpful.

- `mw_feedback_auto_reply_helpful` (optional)  
  Meaning: automation reply solved the issue (positive signal).

- `mw_feedback_new_intent_candidate`  
  Meaning: this ticket does not fit existing taxonomy well.

### Optional “correct destination” tags
To capture the corrected destination without free-text:
- `mw_feedback_correct_dept_sales`
- `mw_feedback_correct_dept_returns_admin`
- `mw_feedback_correct_dept_chargebacks_disputes`
and similar variants for other departments.

If Support Ops prefers fewer tags, we can skip these and just use `mw_feedback_misroute`.

---

## 3) Macro pack proposal (Support Ops)
Create a separate macro pack in Richpanel:

### “MW Feedback” macros
- `MW Feedback: Misrouted → Sales`
- `MW Feedback: Misrouted → Backend`
- `MW Feedback: Misrouted → Technical Support`
- `MW Feedback: Misrouted → Phone Support`
- `MW Feedback: Misrouted → TikTok Support`
- `MW Feedback: Misrouted → Returns Admin`
- `MW Feedback: Misrouted → LiveChat Support`
- `MW Feedback: Misrouted → Leadership`
- `MW Feedback: Misrouted → Social Media`
- `MW Feedback: Misrouted → Email Support`
- `MW Feedback: Misrouted → Chargebacks/Disputes`

Each macro should:
1) add `mw_feedback_misroute`
2) add the appropriate `mw_feedback_correct_dept_*` tag (optional)
3) reassign ticket to the correct team (optional but recommended)

### “Auto reply” feedback macros
- `MW Feedback: Auto reply wrong`
- `MW Feedback: Auto reply helpful`
These add the relevant tag and do **not** change routing.

---

## 4) How we use feedback (analytics + eval)

### A) Daily/weekly monitoring
- track misroute rate (tickets with `mw_feedback_misroute`)
- track auto-reply wrong rate

### B) Training set expansion
- add labeled examples to golden set:
  - message summary (redacted)
  - correct department
  - correct intent/template_id

### C) Drift detection
- sudden spike in misroute tag rate is a strong signal of:
  - prompt regression
  - product/policy changes (new intent)
  - team/tag mapping drift

---

## 5) Privacy rules for feedback
- Agents must not paste customer PII into “notes” fields used for analytics.
- Feedback tags are preferred to free text.
- If a comment is required, it must be short and **PII-free**.

---

## 6) Implementation notes (tenant-dependent)
How we ingest feedback into analytics depends on tenant capabilities:
- Option A: Richpanel webhook on tag add (if supported)
- Option B: scheduled daily export via Richpanel API
- Option C: manual export/reporting in early rollout

This wave defines the contract; implementation is scheduled in later waves.

---

## 7) Related docs
- Macro governance: `docs/05_FAQ_Automation/Macro_Alignment_and_Governance.md`
- Drift monitoring: `Quality_Monitoring_and_Drift_Detection.md`
