# Data Inputs (Reference)

Last updated: 2025-12-22

This project plan references the following inputs.

---

## 1) Provided by you
- `CommonIssues.zip` — known pitfalls to design around.
- `RichPanel_Docs_Instructions_Library_001.zip` — Richpanel documentation snapshot + deep research  
  - includes current configs under `RichPanel_Docs_Phase0/04_SETUP_CONFIGURATION`
- `Policies.zip` — rules/guidelines for ChatGPT PM + Cursor agents
- `RoughDraft.zip` — deeper project details + dataset summaries (top FAQs, routing model, prompt schema ideas)
- `Agent Activity Heatmap.csv` — 7-day hourly support volume
- ✅ `SC_Data_ai_ready_package.zip` — normalized dataset of customer conversations + support responses (AI-ready format)

---

## 2) Extracted highlights (so far)

### 2.1 RoughDraft — Top FAQ distribution (sample size: 3,611 tickets)
Top driver: **Order status & tracking** (~51.84% of tickets in the sample).  
Other major intents include cancellations, troubleshooting, subscriptions, missing items, shipping delays, returns/refunds, and pre-orders.

This data is being used to prioritize:
- routing taxonomy v0.1
- automation scope v0.1

### 2.2 SC_Data_ai_ready — Dataset overview (evidence dataset)
From `profile_summary.json` in the package:
- Conversations: **3,613**
- Messages: **28,585**
- Chunks: **8,006**
- Date range (closed_at): **2025-10-14** to **2025-12-20**
- Channels present include: email, email_from_widget, TikTok, Facebook comments/messages, Instagram messages/comments

**Primary planned uses**
- Validate/refine the intent taxonomy using real language patterns.
- Build an offline evaluation set (routing accuracy, confidence calibration).
- Derive safe response templates and “ask-for-info” patterns (without copying PII).
- Identify recurring failure modes (multi-intent, low-context, attachment-heavy tickets).

**Important:** this dataset likely contains PII (emails, phone numbers, order numbers).  
We must treat it as sensitive and avoid pasting raw transcripts into documentation.

### 2.3 Agent Activity Heatmap — Volume overview
- Total inbound messages observed in the 7-day file: **35465**
- Peak hourly inbound volume: **430** messages at **Sun 02:00 PM**
- Busiest day by inbound volume: **Mon** (5658 messages)

Notes:
- We still need to confirm the timezone and whether this is “all inbound” or filtered by a subset of channels/agents.
- Capacity planning will be finalized in Wave 07.

---

## 3) How we use these inputs
- RoughDraft informs **what to automate first** and what intents exist in real data.
- SC_Data provides **real message language** to ground taxonomy, prompts, and evaluation.
- Richpanel docs snapshot informs **integration contracts, automations, and API usage**.
- CommonIssues informs **guardrails and failure-mode planning**.
- Heatmap informs **scaling, concurrency, and cost modeling**.

We do not re-embed those archives here to keep this plan lightweight.
Instead, the plan documents *how to use them* and what we must extract/confirm from them.

### 2.4 Additional extracted highlights (Wave 03)
From quick aggregate scans of SC_Data customer messages:
- First customer message contains an order-number-like pattern only ~10% of the time (rough).
- Tracking numbers are almost never present in the *first* message (<1%).
Implication: automation must rely on Richpanel-linked orders or “ask for order #” fallbacks.

From Richpanel docs snapshot:
- Order schema includes fulfillment tracking number + tracking URL fields (suggesting we can provide tracking info when order linkage exists).
